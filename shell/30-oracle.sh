# Oracle CLI wrappers.
# Keep upstream skill instructions pristine; local runtime quirks live here.

_botfiles_oracle_exec_node24() {
  local nvm_dir="${NVM_DIR:-$HOME/.nvm}"
  local nvm_sh="$nvm_dir/nvm.sh"

  if [ -s "$nvm_sh" ]; then
    # shellcheck disable=SC1090
    . "$nvm_sh"
    local nvm_candidate=""
    if nvm which 24 >/dev/null 2>&1; then
      nvm_candidate="24"
    elif nvm which node >/dev/null 2>&1; then
      nvm_candidate="node"
    fi
    if [ -n "$nvm_candidate" ]; then
      (
        nvm use "$nvm_candidate" >/dev/null
        local node_major
        node_major="$(node -p 'Number(process.versions.node.split(".")[0])' 2>/dev/null || echo 0)"
        if [ "${node_major:-0}" -lt 24 ]; then
          echo "oracle wrapper: Node 24+ is required. Install with: . \"$nvm_sh\" && nvm install 24" >&2
          return 1
        fi
        "$@"
      )
      return
    fi
    echo "oracle wrapper: Node 24+ is required. Install with: . \"$nvm_sh\" && nvm install 24" >&2
    return 1
  fi

  if command -v node >/dev/null 2>&1; then
    local node_major
    node_major="$(node -p 'Number(process.versions.node.split(".")[0])' 2>/dev/null || echo 0)"
    if [ "${node_major:-0}" -ge 24 ]; then
      "$@"
      return
    fi
  fi

  echo "oracle wrapper: Node 24+ is required. Install Node 24 or configure nvm under \$HOME/.nvm." >&2
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

_botfiles_oracle_model_is_gpt55() {
  local expect_model_value=0
  local arg
  for arg in "$@"; do
    if [ "$expect_model_value" -eq 1 ]; then
      case "$arg" in
        *5.5*|*gpt-5.5*|*GPT-5.5*)
          return 0
          ;;
      esac
      expect_model_value=0
      continue
    fi
    case "$arg" in
      --model|--models|-m)
        expect_model_value=1
        ;;
      --model=*5.5*|--models=*5.5*|-m*5.5*|--model=*gpt-5.5*|--models=*gpt-5.5*)
        return 0
        ;;
    esac
  done
  return 1
}

_botfiles_oracle_option_specified() {
  local option="$1"
  shift
  local arg
  for arg in "$@"; do
    case "$arg" in
      "$option"|"$option"=*)
        return 0
        ;;
    esac
  done
  return 1
}

_botfiles_oracle_route_specified() {
  local expect_route_value=0
  local arg
  for arg in "$@"; do
    if [ "$expect_route_value" -eq 1 ]; then
      return 0
    fi
    case "$arg" in
      --base-url|--azure-endpoint|--azure-deployment|--azure-api-version)
        expect_route_value=1
        ;;
      --base-url=*|--azure-endpoint=*|--azure-deployment=*|--azure-api-version=*)
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

  if [ -n "${ORACLE_AZURE_OPENAI_API_KEY:-}" ] && [ -z "${AZURE_OPENAI_API_KEY:-}" ]; then
    export AZURE_OPENAI_API_KEY="$ORACLE_AZURE_OPENAI_API_KEY"
  fi

  if ! _botfiles_oracle_is_subcommand_invocation "$@"; then
    local default_gpt55_browser=0
    if ! _botfiles_oracle_engine_specified "$@" && ! _botfiles_oracle_model_specified "$@" && ! _botfiles_oracle_browser_requested "$@"; then
      default_gpt55_browser=1
    elif _botfiles_oracle_browser_requested "$@" && ! _botfiles_oracle_model_specified "$@"; then
      default_gpt55_browser=1
    elif _botfiles_oracle_model_is_gpt55 "$@" && ! _botfiles_oracle_engine_specified "$@"; then
      default_gpt55_browser=1
    fi

    if [ "$default_gpt55_browser" -eq 1 ]; then
      if ! _botfiles_oracle_engine_specified "$@" && ! _botfiles_oracle_browser_requested "$@"; then
        defaults+=(--engine browser)
      fi
      if ! _botfiles_oracle_option_specified --browser-manual-login "$@"; then
        defaults+=(--browser-manual-login)
      fi
      local chrome_path="${ORACLE_CHROME_PATH:-$HOME/pro/botfiles/bin/oracle-chrome-linux}"
      if [ -x "$chrome_path" ] && ! _botfiles_oracle_option_specified --browser-chrome-path "$@"; then
        defaults+=(--browser-chrome-path "$chrome_path")
      fi
      if ! _botfiles_oracle_model_specified "$@"; then
        defaults+=(--model "5.5 Pro")
      fi
      if ! _botfiles_oracle_option_specified --browser-model-strategy "$@"; then
        defaults+=(--browser-model-strategy select)
      fi
    elif ! _botfiles_oracle_engine_specified "$@" && ! _botfiles_oracle_browser_requested "$@"; then
      defaults+=(--engine api)
      if ! _botfiles_oracle_model_specified "$@"; then
        defaults+=(--model gpt-5.4-pro)
      fi
      if ! _botfiles_oracle_route_specified "$@"; then
        if [ -n "${ORACLE_AZURE_OPENAI_ENDPOINT:-}" ] && [ -n "${ORACLE_AZURE_OPENAI_DEPLOYMENT:-}" ]; then
          defaults+=(--azure-endpoint "$ORACLE_AZURE_OPENAI_ENDPOINT" --azure-deployment "$ORACLE_AZURE_OPENAI_DEPLOYMENT")
          if [ -n "${ORACLE_AZURE_OPENAI_API_VERSION:-}" ]; then
            defaults+=(--azure-api-version "$ORACLE_AZURE_OPENAI_API_VERSION")
          fi
        fi
      fi
    else
      if ! _botfiles_oracle_model_specified "$@"; then
        defaults+=(--model gpt-5.4-pro)
      fi
      if ! _botfiles_oracle_browser_requested "$@" && ! _botfiles_oracle_route_specified "$@"; then
        if [ -n "${ORACLE_AZURE_OPENAI_ENDPOINT:-}" ] && [ -n "${ORACLE_AZURE_OPENAI_DEPLOYMENT:-}" ]; then
          defaults+=(--azure-endpoint "$ORACLE_AZURE_OPENAI_ENDPOINT" --azure-deployment "$ORACLE_AZURE_OPENAI_DEPLOYMENT")
          if [ -n "${ORACLE_AZURE_OPENAI_API_VERSION:-}" ]; then
            defaults+=(--azure-api-version "$ORACLE_AZURE_OPENAI_API_VERSION")
          fi
        fi
      fi
    fi
  fi

  local oracle_cmd=(npx -y @steipete/oracle@latest)
  if [ "${#defaults[@]}" -gt 0 ]; then
    oracle_cmd+=("${defaults[@]}")
  fi
  if [ "${#args[@]}" -gt 0 ]; then
    oracle_cmd+=("${args[@]}")
  fi

  local effective_args=()
  if [ "${#defaults[@]}" -gt 0 ]; then
    effective_args+=("${defaults[@]}")
  fi
  if [ "${#args[@]}" -gt 0 ]; then
    effective_args+=("${args[@]}")
  fi
  if [ "${#effective_args[@]}" -gt 0 ] && [ -z "${DISPLAY:-}" ] && _botfiles_oracle_browser_requested "${effective_args[@]}" && command -v xvfb-run >/dev/null 2>&1; then
    local xvfb_cmd=(xvfb-run -a)
    xvfb_cmd+=("${oracle_cmd[@]}")
    _botfiles_oracle_exec_node24 "${xvfb_cmd[@]}"
    return
  fi
  _botfiles_oracle_exec_node24 "${oracle_cmd[@]}"
}

oracle-mcp() {
  _botfiles_oracle_exec_node24 npx -y @steipete/oracle@latest oracle-mcp "$@"
}
