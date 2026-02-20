# Shared SSH + mosh + zellij workflows for resilient reconnects.
#
# Configurable host aliases (override before sourcing .botrc if needed):
#   BOT_ML_HOST_PRIMARY   (default: ladduu-dev-ml-vm-ts)
#   BOT_ML_HOST_FALLBACK  (default: ladduu-dev-ml-vm)
#   BOT_ARYA_HOST         (default: ladduu-dev-aryabhatta)
#   BOT_CURSOR_ML_HOST_PRIMARY  (default: BOT_ML_HOST_PRIMARY)
#   BOT_CURSOR_ML_HOST_FALLBACK (default: BOT_ML_HOST_FALLBACK)
#   BOT_CURSOR_ML_PATH          (default: /home/azureuser)

: "${BOT_ML_HOST_PRIMARY:=ladduu-dev-ml-vm-ts}"
: "${BOT_ML_HOST_FALLBACK:=ladduu-dev-ml-vm}"
: "${BOT_ARYA_HOST:=ladduu-dev-aryabhatta}"
: "${BOT_CURSOR_ML_HOST_PRIMARY:=$BOT_ML_HOST_PRIMARY}"
: "${BOT_CURSOR_ML_HOST_FALLBACK:=$BOT_ML_HOST_FALLBACK}"
: "${BOT_CURSOR_ML_PATH:=/home/azureuser}"

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

_bot_ssh_fetch_remote_zellij_sessions() {
  local host="$1"
  ssh -o BatchMode=yes -o ConnectTimeout=8 "$host" \
    "command -v zellij >/dev/null 2>&1 || exit 127; zellij list-sessions --short --no-formatting 2>/dev/null | sed '/^No active zellij sessions found\\.?$/d' || true" \
    2>/dev/null
}

_bot_ssh_prompt_new_session_name() {
  local host="$1"
  local session_name

  while true; do
    printf "New zellij session name for %s: " "$host"
    IFS= read -r session_name || return 1
    session_name="$(printf "%s" "$session_name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

    if [ -z "$session_name" ]; then
      echo "Session name cannot be empty."
      continue
    fi

    if _bot_ssh_validate_session_name "$session_name"; then
      printf "%s\n" "$session_name"
      return 0
    fi

    echo "Invalid name. Use only letters, numbers, dot, underscore, colon, or hyphen."
  done
}

_bot_ssh_choose_zellij_session() {
  local host="$1"
  local explicit_session="$2"
  local existing_sessions
  local selected

  if [ -n "$explicit_session" ]; then
    if _bot_ssh_validate_session_name "$explicit_session"; then
      printf "%s\n" "$explicit_session"
      return 0
    fi
    echo "Invalid session name: ${explicit_session}"
    return 1
  fi

  if ! command -v fzf >/dev/null 2>&1; then
    echo "fzf is required for interactive session picking."
    echo "Install fzf or pass a session name explicitly (example: work-ml my-session)."
    return 1
  fi

  existing_sessions="$(_bot_ssh_fetch_remote_zellij_sessions "$host")"
  selected="$(
    {
      printf "%s\n" "[new session]"
      printf "%s\n" "$existing_sessions" | awk 'NF && !seen[$0]++'
    } | fzf \
      --height=40% \
      --layout=reverse \
      --border \
      --no-multi \
      --prompt="zellij@${host}> " \
      --header="Select existing session or create a new one"
  )" || return 1

  if [ "$selected" = "[new session]" ]; then
    _bot_ssh_prompt_new_session_name "$host"
    return $?
  fi

  if _bot_ssh_validate_session_name "$selected"; then
    printf "%s\n" "$selected"
    return 0
  fi

  echo "Invalid session returned from picker: ${selected}"
  return 1
}

_bot_ssh_connect_zellij() {
  local transport="$1"
  local host="$2"
  local session_name="$3"

  if [ "$transport" = "mosh" ]; then
    if command -v mosh >/dev/null 2>&1; then
      if mosh "$host" -- zellij attach --create "$session_name"; then
        return 0
      fi
      echo "mosh failed for ${host}; falling back to ssh."
    else
      echo "mosh is not installed; falling back to ssh."
    fi
  fi

  ssh -t "$host" "zellij attach --create $session_name"
}

_bot_ssh_workflow_connect() {
  local transport="$1"
  local explicit_session="$2"
  shift 2
  local host
  local session_name

  host="$(_bot_ssh_pick_reachable_host "$@")" || {
    echo "No reachable host found in candidates: $*"
    return 1
  }

  session_name="$(_bot_ssh_choose_zellij_session "$host" "$explicit_session")" || return 1
  _bot_ssh_connect_zellij "$transport" "$host" "$session_name"
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

# Raw shell shortcuts (no zellij attach), useful for quick ad-hoc sessions.
mml() {
  local host
  host="$(_bot_ssh_pick_reachable_host "$BOT_ML_HOST_PRIMARY" "$BOT_ML_HOST_FALLBACK")" || {
    echo "No reachable host found in candidates: $BOT_ML_HOST_PRIMARY $BOT_ML_HOST_FALLBACK"
    return 1
  }

  if command -v mosh >/dev/null 2>&1; then
    if mosh "$host"; then
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
    if mosh "$host"; then
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
