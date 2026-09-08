#!/bin/zsh
set -e
cd "$(dirname "$0")"
if command -v uv >/dev/null 2>&1; then
  uv_bin="$(command -v uv)"
elif [[ -x "$HOME/.local/bin/uv" ]]; then
  uv_bin="$HOME/.local/bin/uv"
elif [[ -x /opt/homebrew/bin/uv ]]; then
  uv_bin=/opt/homebrew/bin/uv
else
  print "Install uv first using the instructions in README.md, then open this launcher again."
  read "reply?Press Return to close. "
  exit 1
fi
exec "$uv_bin" run --locked --no-editable angle app --open
