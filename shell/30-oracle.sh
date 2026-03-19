# Oracle CLI wrappers.
# Keep upstream skill instructions pristine; local runtime quirks live here.

_botfiles_oracle_exec_node22() {
  local nvm_dir="${NVM_DIR:-$HOME/.nvm}"
  local nvm_sh="$nvm_dir/nvm.sh"

  if [ -s "$nvm_sh" ]; then
    # shellcheck disable=SC1090
    . "$nvm_sh"
    if nvm which 22 >/dev/null 2>&1; then
      (
        nvm use 22 >/dev/null
        "$@"
      )
      return
    fi
    echo "oracle wrapper: Node 22 is required. Install with: . \"$nvm_sh\" && nvm install 22" >&2
    return 1
  fi

  if command -v node >/dev/null 2>&1; then
    local node_major
    node_major="$(node -p 'Number(process.versions.node.split(".")[0])' 2>/dev/null || echo 0)"
    if [ "${node_major:-0}" -ge 22 ]; then
      "$@"
      return
    fi
  fi

  echo "oracle wrapper: Node 22+ is required. Install Node 22 or configure nvm under \$HOME/.nvm." >&2
  return 1
}

_botfiles_oracle_browser_requested() {
  local expect_engine_value=0
  local arg
  for arg in "$@"; do
    if [ "$expect_engine_value" -eq 1 ]; then
      [ "$arg" = "browser" ] && return 0
      expect_engine_value=0
      continue
    fi
    case "$arg" in
      --engine)
        expect_engine_value=1
        ;;
      --engine=browser|--browser|--remote-chrome|--remote-host)
        return 0
        ;;
      -e)
        expect_engine_value=1
        ;;
      -ebrowser)
        return 0
        ;;
    esac
  done
  return 1
}

_botfiles_oracle_engine_specified() {
  local expect_engine_value=0
  local arg
  for arg in "$@"; do
    if [ "$expect_engine_value" -eq 1 ]; then
      return 0
    fi
    case "$arg" in
      --engine| -e)
        expect_engine_value=1
        ;;
      --engine=*|--browser|--remote-chrome|--remote-host|-e*)
        return 0
        ;;
    esac
  done
  return 1
}

_botfiles_oracle_model_specified() {
  local expect_model_value=0
  local arg
  for arg in "$@"; do
    if [ "$expect_model_value" -eq 1 ]; then
      return 0
    fi
    case "$arg" in
      --model|--models|-m)
        expect_model_value=1
        ;;
      --model=*|--models=*|-m*)
        return 0
        ;;
    esac
  done
  return 1
}

_botfiles_oracle_is_subcommand_invocation() {
  local expect_value=0
  local arg
  for arg in "$@"; do
    if [ "$expect_value" -eq 1 ]; then
      expect_value=0
      continue
    fi

    case "$arg" in
      --prompt|--followup|--followup-model|--file|--slug|--model|--models|--engine|--timeout|--http-timeout|--zombie-timeout|--write-output|--base-url|--azure-endpoint|--azure-deployment|--azure-api-version|--browser-cookie-path|--chatgpt-url|--browser-port|--browser-model-strategy|--browser-attachments|--remote-chrome|--remote-host|--remote-token|--youtube|--generate-image|--edit-image|--output|--aspect|--retain-hours|--heartbeat)
        expect_value=1
        continue
        ;;
      --*=*|-*|--help|--version)
        continue
        ;;
      serve|bridge|tui|session|status|restart)
        return 0
        ;;
      *)
        return 1
        ;;
    esac
  done
  return 1
}

oracle() {
  local args=("$@")
  local defaults=()

  if ! _botfiles_oracle_is_subcommand_invocation "${args[@]}"; then
    if ! _botfiles_oracle_engine_specified "${args[@]}" && ! _botfiles_oracle_browser_requested "${args[@]}"; then
      defaults+=(--engine api)
    fi
    if ! _botfiles_oracle_model_specified "${args[@]}"; then
      defaults+=(--model gpt-5.4-pro)
    fi
  fi

  if [ -z "${DISPLAY:-}" ] && _botfiles_oracle_browser_requested "${args[@]}" && command -v xvfb-run >/dev/null 2>&1; then
    _botfiles_oracle_exec_node22 xvfb-run -a npx -y @steipete/oracle "${defaults[@]}" "${args[@]}"
    return
  fi
  _botfiles_oracle_exec_node22 npx -y @steipete/oracle "${defaults[@]}" "${args[@]}"
}

oracle-mcp() {
  _botfiles_oracle_exec_node22 npx -y @steipete/oracle oracle-mcp "$@"
}
