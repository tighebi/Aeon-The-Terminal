# AeonProject

AeonProject is a local-by-default terminal LLM chat tool for `zsh`, powered by [Ollama](https://ollama.com).

It provides a command called:

```zsh
chat
```

The assistant is named **Aeon**.

Aeon is designed to behave like a plain terminal-based language model: text goes in, text comes out. It is not a shell agent and does not execute model output.

---

## Features

- Local-by-default LLM chat through Ollama
- Uses Ollama's HTTP API instead of `ollama run`
- Streaming responses
- Interactive chat mode
- One-shot prompt mode
- Structured conversation history
- Optional persistent memory/context file
- Multiline prompts
- Model selection through command-line flags
- Keeps the model alive for faster follow-up responses
- Does not execute shell commands from model output

---

## Requirements

Aeon requires:

- `zsh`
- `curl`
- `jq`
- `ollama`
- a local Ollama model

Install Ollama from:

```text
https://ollama.com
```

Install `jq` if needed:

```zsh
sudo apt install jq
```

On macOS with Homebrew:

```zsh
brew install jq
```

Pull the default model:

```zsh
ollama pull llama3.1:8b
```

For a faster smaller model:

```zsh
ollama pull llama3.2:3b
```

---

## Installation

This project is intended to live in:

```zsh
/home/tighe/Documents/Junior/AeonProject
```

Run the installer:

```zsh
cd /home/tighe/Documents/Junior/AeonProject
./install.zsh
```

The installer creates a symlink:

```text
~/bin/chat -> /home/tighe/Documents/Junior/AeonProject/chat
```

Make sure `~/bin` is in your `PATH`.

If needed, add this to `~/.zshrc`:

```zsh
export PATH="$$HOME/bin:$$PATH"
```

Then reload your shell:

```zsh
source ~/.zshrc
```

Test the command:

```zsh
chat --help
```

---

## Starting Ollama

Aeon talks to Ollama through the local HTTP API.

By default, it expects Ollama at:

```text
http://localhost:11434
```

On Linux, start Ollama with:

```zsh
ollama serve
```

On macOS, open the Ollama app.

You can check that Ollama is reachable with:

```zsh
curl http://localhost:11434/
```

---

## Basic usage

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

Disable conversation history:

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

Explicit one-shot mode:

```zsh
chat --one-shot "Explain recursion simply."
```

or:

```zsh
chat -1 "Explain recursion simply."
```

---

## Command-line options

```text
-m, --model MODEL      Model to use
--no-history           Disable conversation history for this session
--memory-file FILE     Use a custom persistent context file
--no-memory            Disable persistent context
-1, --one-shot         Send one prompt and exit
-h, --help             Show help
```

Default model:

```text
llama3.1:8b
```

Default memory file:

```text
~/.config/chat/memory.md
```

Default Ollama host:

```text
http://localhost:11434
```

---

## Interactive commands

Inside interactive mode, these commands are available:

```text
/help
```

Show help.

```text
/exit
```

Exit Aeon.

```text
/quit
```

Exit Aeon.

```text
/clear
```

Clear the current session history.

```text
/model
```

Show the current Ollama model.

```text
/history
```

Show whether history is enabled and how much history is stored.

```text
/memory
```

Show persistent memory/context file status.

```text
/multiline
```

Enter multiline input mode.

Finish a multiline prompt with a single line containing only:

```text
.
```

Example:

```text
You> /multiline
Multiline input — finish with '.' on its own line.
... Explain this code:
... 
... print("hello")
... .
```

---

## Persistent memory/context

Aeon can load a persistent context file and include it in every prompt.

Default location:

```zsh
~/.config/chat/memory.md
```

Example:

```md
# Persistent context for Aeon

- The user uses zsh.
- The user prefers practical, terminal-focused answers.
- The assistant should be concise unless asked for detail.
- The assistant should not claim to run commands or inspect files.
```

Create the memory file with:

```zsh
mkdir -p ~/.config/chat
nano ~/.config/chat/memory.md
```

This memory is not model training. It is prompt context that gets sent with each request.

Do not store passwords, API keys, private keys, tokens, or sensitive personal information in the memory file.

A safe example file can be kept in the repository as:

```text
memory.example.md
```

Your real memory file should not be committed to Git.

---

## Session history

Aeon keeps temporary conversation history during an interactive session.

The history is stored only while the script is running.

By default, history is trimmed around:

```text
8000 characters
```

You can clear history inside the chat with:

```text
/clear
```

You can disable history when launching Aeon:

```zsh
chat --no-history
```

---

## Environment variables

Aeon supports these environment variables:

```zsh
LLMCHAT_MODEL
```

Sets the default Ollama model.

Example:

```zsh
export LLMCHAT_MODEL="llama3.2:3b"
```

```zsh
CHAT_MEMORY_FILE
```

Sets the default memory/context file.

Example:

```zsh
export CHAT_MEMORY_FILE="$HOME/.config/chat/memory.md"
```

```zsh
OLLAMA_HOST
```

Sets the Ollama API base URL.

Default:

```zsh
http://localhost:11434
```

Example:

```zsh
export OLLAMA_HOST="http://localhost:11434"
```

Note: Aeon is local by default, but this is not strictly enforced. If you set `OLLAMA_HOST` to a remote server, prompts will be sent there.

---

## Safety model

Aeon is designed as a text-only assistant.

It does not intentionally:

- execute model output
- run shell commands suggested by the model
- inspect arbitrary files
- modify files
- install packages automatically
- control the computer
- act as a shell agent

The script does read the optional memory file if enabled.

The script also calls the local Ollama API to generate model responses.

The model may suggest commands in its text responses, but Aeon does not run them.

---

## Local-by-default behavior

By default, Aeon sends requests to:

```text
http://localhost:11434
```

That is the normal local Ollama API endpoint.

However, because `OLLAMA_HOST` can be changed, Aeon is best described as:

```text
local by default, not remote-proof
```

If you point `OLLAMA_HOST` somewhere else, the script will use that endpoint.

---

## Performance notes

Aeon streams responses as they are generated.

It also sends:

```json
"keep_alive": "30m"
```

to Ollama, which asks Ollama to keep the model loaded for 30 minutes. This can make follow-up responses faster.

For better speed:

Use a smaller model:

```zsh
ollama pull llama3.2:3b
chat --model llama3.2:3b
```

Disable history for one-off prompts:

```zsh
chat --no-history "Summarize what a shell pipe is."
```

Keep the memory file short.

Long memory files and long chat histories increase prompt size, which can slow down responses.

---

## Recommended models

Balanced default:

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

Run with a specific model:

```zsh
chat --model llama3.2:3b
```

---

## Project structure

Recommended structure:

```text
AeonProject/
├── chat
├── install.zsh
├── README.md
├── .gitignore
└── memory.example.md
```

The actual executable is:

```text
chat
```

The installer is:

```text
install.zsh
```

The personal memory file should live outside the repository by default:

```text
~/.config/chat/memory.md
```

---

## Troubleshooting

Check where `chat` points:

```zsh
which chat
```

Check the symlink:

```zsh
ls -l ~/bin/chat
```

It should point to:

```text
/home/tighe/Documents/Junior/AeonProject/chat
```

If Ollama is not running, start it:

```zsh
ollama serve
```

If the model is missing, pull it:

```zsh
ollama pull llama3.1:8b
```

If `jq` is missing:

```zsh
sudo apt install jq
```

If `chat` is not found, make sure `~/bin` is in your `PATH`:

```zsh
echo $PATH
```

Add this to `~/.zshrc` if needed:

```zsh
export PATH="$$HOME/bin:$$PATH"
```

Then reload:

```zsh
source ~/.zshrc
```

---

## License

No license specified yet.