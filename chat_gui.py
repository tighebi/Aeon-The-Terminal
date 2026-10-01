#!/usr/bin/env python3

import argparse
import http.client
import json
import os
import queue
import threading
import tkinter as tk
import urllib.error
import urllib.request
from pathlib import Path
from tkinter import ttk


SYSTEM_PROMPT = """You are named Aeon. Reply with plain text only.
You cannot run commands, inspect arbitrary files, modify files, or control the computer.
Do not claim to have performed actions you cannot perform.
Be concise unless asked for more detail.
Be direct and aloof. Do not be overly complimentary, flattering, sentimental, or validating.
Give honest feedback, including criticism or disagreement.
Be clear when you do not understand something. Do not invent information or guess when clarification is necessary.
Keep responses relevant to the user's request and avoid follow-up questions."""
MAX_HISTORY_CHARS = 8000


def parse_args():
    parser = argparse.ArgumentParser(
        prog="chat",
        description="Open Aeon in a desktop chat window.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("LLMCHAT_MODEL", "llama3.1:8b"),
        help="Ollama model to use",
    )
    parser.add_argument(
        "--memory-file",
        default=os.environ.get(
            "CHAT_MEMORY_FILE",
            os.environ.get("LLMCHAT_MEMORY_FILE", str(Path.home() / ".config/chat/memory.md")),
        ),
        help="Optional persistent context file",
    )
    parser.add_argument("--no-history", action="store_true", help="Disable chat history")
    parser.add_argument("--no-memory", action="store_true", help="Disable persistent context")
    return parser.parse_args()


def build_messages(model, history, user_text, memory_context, use_history):
    system_content = SYSTEM_PROMPT
    if memory_context:
        system_content += "\n\nPersistent context:\n" + memory_context

    messages = [{"role": "system", "content": system_content}]
    if use_history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_text})
    return {
        "model": model,
        "messages": messages,
        "stream": True,
        "keep_alive": "30m",
    }


def stream_chat(host, payload):
    request = urllib.request.Request(
        f"{host.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    response_text = []
    with urllib.request.urlopen(request, timeout=600) as response:
        for raw_line in response:
            if not raw_line.strip():
                continue
            data = json.loads(raw_line)
            if data.get("error"):
                raise RuntimeError(data["error"])
            token = data.get("message", {}).get("content", "")
            if token:
                response_text.append(token)
                yield token

    if not "".join(response_text).strip():
        raise RuntimeError("Ollama returned an empty response.")


class AeonWindow:
    def __init__(self, args):
        self.args = args
        self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.history = []
        self.events = queue.Queue()
        self.busy = False
        self.warmed_models = set()
        self.warming_model = None
        self.memory_context = ""
        self.startup_warning = ""

        if not args.no_memory:
            try:
                self.memory_context = Path(args.memory_file).read_text(encoding="utf-8")
            except FileNotFoundError:
                pass
            except (OSError, UnicodeError) as error:
                self.startup_warning = f"Could not read memory file: {error}"

        self.root = tk.Tk()
        self.root.title("Aeon")
        self.root.geometry("760x620")
        self.root.minsize(480, 360)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        self._build_ui(args.model)
        self.root.after(60, self._poll_events)
        if self.startup_warning:
            self._append(f"Warning: {self.startup_warning}\n", "error")
        threading.Thread(target=self._load_models, daemon=True).start()
        self._ensure_model_warm(args.model)

    def _build_ui(self, model):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(outer)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(toolbar, text="Model").pack(side=tk.LEFT, padx=(0, 8))
        self.model_box = ttk.Combobox(toolbar, values=(model,), width=30)
        self.model_box.set(model)
        self.model_box.pack(side=tk.LEFT)
        self.model_box.bind("<<ComboboxSelected>>", self._model_selected)
        ttk.Button(toolbar, text="New chat", command=self.clear_chat).pack(side=tk.RIGHT)

        transcript_frame = ttk.Frame(outer)
        transcript_frame.pack(fill=tk.BOTH, expand=True)
        self.transcript = tk.Text(
            transcript_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=12,
            pady=12,
            font=("TkFixedFont", 10),
            background="#17191f",
            foreground="#e7e9ee",
            insertbackground="#e7e9ee",
            relief=tk.FLAT,
        )
        scrollbar = ttk.Scrollbar(transcript_frame, command=self.transcript.yview)
        self.transcript.configure(yscrollcommand=scrollbar.set)
        self.transcript.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.transcript.tag_configure("user", foreground="#8cc8ff", spacing1=12)
        self.transcript.tag_configure("aeon", foreground="#a8e6b0", spacing1=12)
        self.transcript.tag_configure("error", foreground="#ff9b9b", spacing1=8)

        self.status = ttk.Label(outer, text="", anchor=tk.W)
        self.status.pack(fill=tk.X, pady=(8, 6))

        input_frame = ttk.Frame(outer)
        input_frame.pack(fill=tk.X)
        self.input = ttk.Entry(input_frame)
        self.input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input.bind("<Return>", self._send_on_return)
        self.send_button = ttk.Button(input_frame, text="Send", command=self.send)
        self.send_button.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0))
        self.input.focus_set()

    def _append(self, text, tag=None):
        self.transcript.configure(state=tk.NORMAL)
        self.transcript.insert(tk.END, text, tag)
        self.transcript.configure(state=tk.DISABLED)
        self.transcript.see(tk.END)

    def _set_status(self, text, error=False):
        self.status.configure(text=text, foreground="#b00020" if error else "")

    def _model_selected(self, _event=None):
        model = self.model_box.get().strip()
        if model:
            self.args.model = model
            self._ensure_model_warm(model)

    def _ensure_model_warm(self, model):
        if not model:
            self.send_button.configure(state=tk.NORMAL)
            self._set_status("Enter a model name.", error=True)
            return
        if model in self.warmed_models:
            if not self.busy:
                self.send_button.configure(state=tk.NORMAL)
                self._set_status("Ready")
            return
        if self.warming_model is not None:
            self.send_button.configure(state=tk.DISABLED)
            return

        self.warming_model = model
        self.send_button.configure(state=tk.DISABLED)
        self._set_status(f"Loading {model}...")
        threading.Thread(target=self._warm_model, args=(model,), daemon=True).start()

    def _warm_model(self, model):
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": ""}],
            "stream": False,
            "keep_alive": "30m",
        }
        request = urllib.request.Request(
            f"{self.host.rstrip('/')}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                data = json.load(response)
            if data.get("error"):
                raise RuntimeError(data["error"])
            self.events.put(("warmup_done", model, None))
        except (
            urllib.error.URLError,
            http.client.HTTPException,
            OSError,
            ValueError,
            json.JSONDecodeError,
            RuntimeError,
        ) as error:
            self.events.put(("warmup_done", model, str(error)))

    def _load_models(self):
        request = urllib.request.Request(f"{self.host.rstrip('/')}/api/tags")
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.load(response)
            names = [item["name"] for item in data.get("models", []) if item.get("name")]
            self.events.put(("models", names, None))
        except (
            urllib.error.URLError,
            http.client.HTTPException,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            self.events.put(("models", [], str(error)))

    def _poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "models":
                    _, models, error = event
                    if models:
                        self.model_box.configure(values=models)
                        if (
                            self.args.model not in models
                            and self.args.model not in self.warmed_models
                            and self.warming_model is None
                        ):
                            self._set_status(
                                f"Model {self.args.model!r} is not installed. Run: ollama pull {self.args.model}",
                                error=True,
                            )
                    elif error and self.warming_model is None:
                        self._set_status(f"Cannot reach Ollama at {self.host}: {error}", error=True)
                    elif not error and self.warming_model is None:
                        self._set_status("No models installed. Pull a model with ollama pull.", error=True)
                elif event[0] == "warmup_done":
                    _, model, error = event
                    self.warming_model = None
                    if not error:
                        self.warmed_models.add(model)
                    selected_model = self.model_box.get().strip()
                    if selected_model and selected_model != model:
                        self._ensure_model_warm(selected_model)
                    elif error:
                        if not self.busy:
                            self.send_button.configure(state=tk.NORMAL)
                        self._set_status(f"Could not load {model}: {error}", error=True)
                    else:
                        if not self.busy:
                            self.send_button.configure(state=tk.NORMAL)
                            self._set_status("Ready")
                elif event[0] == "token":
                    self._append(event[1], "aeon")
                elif event[0] == "done":
                    user_text, response_text = event[1], event[2]
                    if not self.args.no_history:
                        self.history.extend(
                            [
                                {"role": "user", "content": user_text},
                                {"role": "assistant", "content": response_text},
                            ]
                        )
                        self._trim_history()
                    self.busy = False
                    self.send_button.configure(
                        state=tk.DISABLED if self.warming_model else tk.NORMAL
                    )
                    self._append("\n\n")
                    self._set_status(
                        f"Loading {self.warming_model}..." if self.warming_model else "Ready"
                    )
                    self.input.focus_set()
                elif event[0] == "error":
                    self._append(f"\n\nError: {event[1]}\n", "error")
                    self.busy = False
                    self.send_button.configure(
                        state=tk.DISABLED if self.warming_model else tk.NORMAL
                    )
                    if self.warming_model:
                        self._set_status(f"Loading {self.warming_model}...")
                    else:
                        self._set_status("Request failed", error=True)
                    self.input.focus_set()
        except queue.Empty:
            pass
        self.root.after(60, self._poll_events)

    def _trim_history(self):
        while len(self.history) > 2 and sum(
            len(item["content"]) for item in self.history
        ) > MAX_HISTORY_CHARS:
            del self.history[:2]

    def _send_on_return(self, _event):
        self.send()
        return "break"

    def send(self):
        if self.busy:
            return
        user_text = self.input.get().strip()
        if not user_text:
            return
        model = self.model_box.get().strip()
        if not model:
            self._set_status("Enter a model name.", error=True)
            return
        if model not in self.warmed_models:
            self._ensure_model_warm(model)
            return

        self.args.model = model
        self.input.delete(0, tk.END)
        self._append(f"You>\n{user_text}\n\n", "user")
        self._append("Aeon>\n", "aeon")
        self.busy = True
        self.send_button.configure(state=tk.DISABLED)
        self._set_status(f"Waiting for {model}...")

        payload = build_messages(
            model,
            self.history,
            user_text,
            self.memory_context,
            not self.args.no_history,
        )
        threading.Thread(
            target=self._request_response,
            args=(payload, user_text),
            daemon=True,
        ).start()

    def _request_response(self, payload, user_text):
        response_parts = []
        try:
            for token in stream_chat(self.host, payload):
                response_parts.append(token)
                self.events.put(("token", token))
            self.events.put(("done", user_text, "".join(response_parts)))
        except (
            urllib.error.URLError,
            http.client.HTTPException,
            OSError,
            ValueError,
            json.JSONDecodeError,
            UnicodeDecodeError,
            RuntimeError,
        ) as error:
            self.events.put(("error", str(error)))

    def clear_chat(self):
        if self.busy:
            return
        self.history.clear()
        self.transcript.configure(state=tk.NORMAL)
        self.transcript.delete("1.0", tk.END)
        self.transcript.configure(state=tk.DISABLED)
        self._set_status("History cleared")

    def run(self):
        self.root.mainloop()


def main():
    AeonWindow(parse_args()).run()


if __name__ == "__main__":
    main()
