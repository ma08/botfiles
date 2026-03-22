# Shared SSH + mosh + zellij workflows for resilient reconnects.
#
# Configurable host aliases (override before sourcing .botrc if needed):
#   BOT_ML_HOST_PRIMARY   (default: ladduu-dev-ml-vm-ts)
#   BOT_ML_HOST_FALLBACK  (default: ladduu-dev-ml-vm)
#   BOT_ARYA_HOST         (default: ladduu-dev-aryabhatta)
#   BOT_AGENT_HOST        (default: ladduu-agent-prod)
#   BOT_CURSOR_ML_HOST_PRIMARY  (default: BOT_ML_HOST_PRIMARY)
#   BOT_CURSOR_ML_HOST_FALLBACK (default: BOT_ML_HOST_FALLBACK)
#   BOT_CURSOR_ML_PATH          (default: /home/azureuser)

: "${BOT_ML_HOST_PRIMARY:=ladduu-dev-ml-vm-ts}"
: "${BOT_ML_HOST_FALLBACK:=ladduu-dev-ml-vm}"
: "${BOT_ARYA_HOST:=ladduu-dev-aryabhatta}"
: "${BOT_AGENT_HOST:=ladduu-agent-prod}"
: "${BOT_CURSOR_ML_HOST_PRIMARY:=$BOT_ML_HOST_PRIMARY}"
: "${BOT_CURSOR_ML_HOST_FALLBACK:=$BOT_ML_HOST_FALLBACK}"
: "${BOT_CURSOR_ML_PATH:=/home/azureuser}"
# Keep mosh usable in Ghostty by default.
# --no-init avoids sending smcup/rmcup (alternate-screen init), which can make
# touchpad scroll behave like Up/Down keys in some Ghostty + mosh sessions.
# References:
# - https://github.com/ghostty-org/ghostty/discussions/4617
# - https://www.manpagez.com/man/1/mosh/ (see --no-init)
: "${BOT_MOSH_NO_INIT:=1}"

_bot_mosh_connect() {
  local host="$1"
  shift

  if [ "${BOT_MOSH_NO_INIT}" = "1" ]; then
    mosh --no-init "$host" "$@"
  else
    mosh "$host" "$@"
  fi
}

_bot_ssh_validate_session_name() {
  case "${1:-}" in
    "")
      return 1
      ;;
    *[!A-Za-z0-9._:-]*)
      return 1
      ;;
    *)
      return 0
      ;;
  esac
}

_bot_ssh_pick_reachable_host() {
  local host
  for host in "$@"; do
    [ -n "$host" ] || continue
    if ssh -o BatchMode=yes -o ConnectTimeout=5 "$host" "exit" >/dev/null 2>&1; then
      printf "%s\n" "$host"
      return 0
    fi
  done
  return 1
}

_bot_zellij_workflow_script() {
  printf "%s\n" "${BOTFILES_ROOT:-$HOME/pro/botfiles}/shell/work-zellij"
}

_bot_run_zellij_workflow() {
  local workflow_script
  workflow_script="$(_bot_zellij_workflow_script)"

  if [ ! -x "$workflow_script" ]; then
    echo "work-zellij helper not found or not executable: $workflow_script"
    return 1
  fi

  "$workflow_script" "$@"
}

_bot_ssh_workflow_connect() {
  local transport="$1"
  local explicit_session="$2"
  shift 2
  local host

  host="$(_bot_ssh_pick_reachable_host "$@")" || {
    echo "No reachable host found in candidates: $*"
    return 1
  }

  # The helper owns all TTY interaction so prompts are not swallowed by
  # command substitution when fzf or confirmation steps are active.
  if [ -n "$explicit_session" ]; then
    _bot_run_zellij_workflow connect --mode remote --transport "$transport" --host "$host" --session "$explicit_session"
    return $?
  fi

  _bot_run_zellij_workflow connect --mode remote --transport "$transport" --host "$host"
}

work-ml() {
  _bot_ssh_workflow_connect "mosh" "${1:-}" "$BOT_ML_HOST_PRIMARY" "$BOT_ML_HOST_FALLBACK"
}

work-ml-ssh() {
  _bot_ssh_workflow_connect "ssh" "${1:-}" "$BOT_ML_HOST_PRIMARY" "$BOT_ML_HOST_FALLBACK"
}

work-arya() {
  _bot_ssh_workflow_connect "ssh" "${1:-}" "$BOT_ARYA_HOST"
}

work-arya-mosh() {
  _bot_ssh_workflow_connect "mosh" "${1:-}" "$BOT_ARYA_HOST"
}

work-arya-ssh() {
  _bot_ssh_workflow_connect "ssh" "${1:-}" "$BOT_ARYA_HOST"
}

work-agent() {
  _bot_ssh_workflow_connect "ssh" "${1:-}" "$BOT_AGENT_HOST"
}

work-agent-mosh() {
  _bot_ssh_workflow_connect "mosh" "${1:-}" "$BOT_AGENT_HOST"
}

work-agent-ssh() {
  _bot_ssh_workflow_connect "ssh" "${1:-}" "$BOT_AGENT_HOST"
}

work-here() {
  if [ -n "${1:-}" ]; then
    _bot_run_zellij_workflow connect --mode local --transport local --session "$1"
    return $?
  fi

  _bot_run_zellij_workflow connect --mode local --transport local
}

# Raw shell shortcuts (no zellij attach), useful for quick ad-hoc sessions.
mml() {
  local host
  host="$(_bot_ssh_pick_reachable_host "$BOT_ML_HOST_PRIMARY" "$BOT_ML_HOST_FALLBACK")" || {
    echo "No reachable host found in candidates: $BOT_ML_HOST_PRIMARY $BOT_ML_HOST_FALLBACK"
    return 1
  }

  if command -v mosh >/dev/null 2>&1; then
    if _bot_mosh_connect "$host"; then
      return 0
    fi
    echo "mosh failed for ${host}; falling back to ssh."
  else
    echo "mosh is not installed; falling back to ssh."
  fi

  ssh "$host"
}

marya() {
  local host="$BOT_ARYA_HOST"

  if command -v mosh >/dev/null 2>&1; then
    if _bot_mosh_connect "$host"; then
      return 0
    fi
    echo "mosh failed for ${host}; falling back to ssh."
  else
    echo "mosh is not installed; falling back to ssh."
  fi

  ssh "$host"
}

magent() {
  local host="$BOT_AGENT_HOST"

  if command -v mosh >/dev/null 2>&1; then
    if _bot_mosh_connect "$host"; then
      return 0
    fi
    echo "mosh failed for ${host}; falling back to ssh."
  else
    echo "mosh is not installed; falling back to ssh."
  fi

  ssh "$host"
}

# Cursor Remote-SSH shortcut for the ML VM (SSH transport, not mosh transport).
cursor-ml() {
  local host
  local remote_path
  local remote_uri

  if ! command -v cursor >/dev/null 2>&1; then
    echo "cursor CLI is not installed or not in PATH."
    return 1
  fi

  host="$(_bot_ssh_pick_reachable_host "$BOT_CURSOR_ML_HOST_PRIMARY" "$BOT_CURSOR_ML_HOST_FALLBACK")" || {
    echo "No reachable host found in candidates: $BOT_CURSOR_ML_HOST_PRIMARY $BOT_CURSOR_ML_HOST_FALLBACK"
    return 1
  }

  remote_path="${1:-$BOT_CURSOR_ML_PATH}"
  remote_uri="vscode-remote://ssh-remote+${host}${remote_path}"
  cursor --reuse-window --folder-uri "$remote_uri"
}
