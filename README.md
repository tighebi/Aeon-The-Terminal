# Aeon

Aeon is a desktop chat application for local Ollama models. Run `chat` to open its window. The app has no terminal chat mode or separate GUI launcher.

## Features

- Streams responses from Ollama
- Preloads the selected model when the window opens
- Keeps conversation history for the current session
- Optionally loads a persistent context file

## Requirements

- `zsh`
- Python 3 with Tkinter
- Ollama and at least one installed model

Install Ollama from [ollama.com](https://ollama.com). 
On Debian or Ubuntu, install the other system packages with:

```zsh
sudo apt install zsh python3 python3-tk
```

## Install

Run the installer from the project directory:

```zsh
./install.zsh
```

It installs the `chat` command in `~/bin`. Make sure that directory is in your `PATH`. For zsh, add this to `~/.zshrc` if needed:

```zsh
export PATH="$HOME/bin:$PATH"
```

Reload the shell and launch Aeon:

```zsh
source ~/.zshrc
chat
```

The installer removes an obsolete `~/bin/chat-gui` symlink if it points to a `chat_gui.py` file.

## Use

Run:

```zsh
chat
```

The window preloads the selected model on startup and whenever you switch models. Type a message and press Enter to send it. Use **New chat** to clear the current conversation.

Other options:

```text
-m, --model MODEL      Select the Ollama model
--no-history           Disable conversation history for this session
--memory-file FILE     Use a custom persistent context file
--no-memory            Disable persistent context
-h, --help             Show help
```

The default model is `llama3.1:8b`. The default Ollama server is `http://localhost:11434`.


## Persistent context

By default, Aeon loads optional context from:

```text
~/.config/chat/memory.md
```

## Project files

```text
chat
chat_gui.py
install.zsh
README.md
memory.example.md
```
