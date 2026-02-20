# Resolve UV_BIN once in shared shell config for cross-machine portability.
#
# Why this exists:
# - Codex notify hooks run via non-interactive shells where PATH may differ.
# - We want a single botfiles config that works on both Linux VMs and macOS.
# - Centralizing uv lookup here keeps codex/config.toml simple.
#
# Resolution order:
# 1) Respect pre-set UV_BIN (manual override before sourcing .botrc)
# 2) Prefer ~/.local/bin/uv (common on Linux)
# 3) Fallback to uv on PATH (e.g., /opt/homebrew/bin/uv on macOS)
if [ -z "${UV_BIN:-}" ]; then
  if [ -x "$HOME/.local/bin/uv" ]; then
    export UV_BIN="$HOME/.local/bin/uv"
  else
    _botrc_uv_bin="$(command -v uv 2>/dev/null || true)"
    if [ -n "$_botrc_uv_bin" ]; then
      export UV_BIN="$_botrc_uv_bin"
    fi
    unset _botrc_uv_bin
  fi
fi
