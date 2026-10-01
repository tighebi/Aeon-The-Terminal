#!/usr/bin/env zsh

###############################################################################
# install.zsh
#
# Installs the local `chat` command by creating a symlink:
#
#   ~/bin/chat -> this_repo/chat
#
# This does not install Ollama or models.
###############################################################################

emulate -R zsh
set -e

REPO_DIR="${0:A:h}"
SOURCE="$REPO_DIR/chat"
GUI_SOURCE="$REPO_DIR/chat_gui.py"
TARGET_DIR="$HOME/bin"
TARGET="$TARGET_DIR/chat"
GUI_TARGET="$TARGET_DIR/chat-gui"

if [[ ! -f "$SOURCE" || ! -f "$GUI_SOURCE" ]]; then
  echo "Error: could not find chat script at:"
  echo "  $SOURCE"
  echo "  $GUI_SOURCE"
  exit 1
fi

mkdir -p "$TARGET_DIR"

chmod +x "$SOURCE" "$GUI_SOURCE"

if [[ -e "$TARGET" || -L "$TARGET" ]]; then
  echo "Removing existing $TARGET"
  rm "$TARGET"
fi

ln -s "$SOURCE" "$TARGET"

if [[ -L "$GUI_TARGET" && "${GUI_TARGET:A}" == */chat_gui.py ]]; then
  echo "Removing obsolete $GUI_TARGET"
  rm "$GUI_TARGET"
fi

echo "Installed chat successfully."
echo
echo "Symlink created:"
echo "  $TARGET -> $SOURCE"
echo
echo "Make sure ~/bin is in your PATH."
echo
echo "You can check with:"
echo "  echo \$PATH"
echo
echo "If needed, add this to ~/.zshrc:"
echo '  export PATH="$HOME/bin:$PATH"'
echo
echo "Then reload zsh:"
echo "  source ~/.zshrc"
echo
echo "Test with:"
echo "  chat --help"