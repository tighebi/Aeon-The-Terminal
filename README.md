# AeonProject

AeonProject is a local-only terminal LLM chat tool for `zsh`, powered by [Ollama](https://ollama.com).

It provides a simple command called:

```zsh
chat
```

The goal is to have a terminal-based language model assistant that can respond like an LLM, while avoiding shell-agent behavior. The model output is printed as text only. It is not executed.

---

## Features

- Local LLM chat through Ollama
- Interactive terminal chat mode
- One-shot prompt mode
- Optional session history
- Optional persistent memory/context file
- Multiline prompts
- Model selection through command-line flags
- No command execution from model output

---

## Requirements

You need:

- `zsh`
- `ollama`
- a local Ollama model

Install Ollama from:

```text
https://ollama.com
```

Then pull a model:

```zsh
ollama pull llama3.1:8b
```

For a faster, smaller model:

```zsh
ollama pull llama3.2:3b
```

---

## Installation

Clone or place this repository somewhere on your system.

Example location:

```zsh
/home/tighe/Documents/Junior/AeonProject
```

Run the installer:

```zsh
cd /home/tighe/Documents/Junior/AeonProject
./install.zsh
```

This creates a symlink:

```text
~/bin/chat -> /home/tighe/Documents/Junior/AeonProject/chat
```

Make sure `~/bin` is in your PATH.

If needed, add this to `~/.zshrc`:

```zsh
export PATH="$$HOME/bin:$$PATH"
```

Then reload your shell:

```zsh
source ~/.zshrc
```

Test:

```zsh
chat --help
```

---

## Usage

Start interactive chat:

```zsh
chat
```

Ask a one-shot question:

```zsh
chat "What is 5 + 5?"
```

Use a specific model:

```zsh
chat --model llama3.2:3b
```

Disable temporary session history:

```zsh
chat --no-history
```

Disable persistent memory/context:

```zsh
chat --no-memory
```

Use a custom memory file:

```zsh
chat --memory-file ~/my-memory.md
```

---

## Interactive commands

Inside `chat`, you can use:

```text
/help
```

Show help.

```text
/exit
```

Exit the chat.

```text
/quit
```

Exit the chat.

```text
/clear
```

Clear temporary session history.

```text
/model
```

Show the current Ollama model.

```text
/history
```

Show session history status.

```text
/memory
```

Show persistent memory/context status.

```text
/multiline
```

Enter a multiline prompt. Finish with a single line containing only:

```text
.
```

---

## Persistent memory/context

The script can include a local persistent context file in every prompt.

Default location:

```zsh
~/.config/chat/memory.md
```

This is useful for storing preferences like:

```md
- The user uses zsh.
- The user prefers step-by-step explanations.
- The assistant should not claim it can run commands.
```

This is not true model training. It is prompt context that gets included with each request.

Do not put passwords, API keys, private keys, or sensitive information in the memory file.

A safe example file is included as:

```text
memory.example.md
```

Your real `memory.md` should not be committed to Git.

---

## Safety model

This script is intended to be text-only.

It does not intentionally:

- execute model output
- run commands suggested by the model
- inspect your files
- modify your files
- install packages automatically
- act as a shell agent

The only required external command is `ollama`, which is used to generate local model responses.

The model may suggest commands in its text responses, but the script does not run them.

---

## Recommended models

Balanced:

```zsh
ollama pull llama3.1:8b
```

Faster:

```zsh
ollama pull llama3.2:3b
```

Very small and fast:

```zsh
ollama pull llama3.2:1b
```

Then run with:

```zsh
chat --model llama3.2:3b
```

---

## Project structure

```text
AeonProject/
├── chat
├── install.zsh
├── README.md
├── .gitignore
└── memory.example.md
```

---

## Notes

If `chat` does not run, check where your shell finds it:

```zsh
which chat
```

Check the symlink:

```zsh
ls -l ~/bin/chat
```

It should point to the `chat` script inside this repository.