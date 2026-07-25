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

_botfiles_oracle_source_main_commit() {
  # PR #320 canary: accept GPT-5.6 Sol with a separately rendered Pro effort pill.
  # This is preferred for no-model defaults; it does not add a CLI selector for Pro effort.
  printf '%s\n' "${ORACLE_SOURCE_MAIN_COMMIT:-ea8b1b57f140f2c641a2a8a9cc1dd10bd03bdb18}"
}

_botfiles_oracle_source_main_root() {
  printf '%s\n' "${ORACLE_SOURCE_MAIN_ROOT:-$HOME/pro/lab/tools/oracle-main}"
}

_botfiles_oracle_source_main_enabled() {
  case "${ORACLE_SOURCE_MAIN:-0}" in
    1|true|True|TRUE|yes|Yes|YES|on|On|ON|source|main|canary|require|required|must)
      return 0
      ;;
  esac
  return 1
}

_botfiles_oracle_source_main_required() {
  case "${ORACLE_SOURCE_MAIN:-1}" in
    require|required|must)
      return 0
      ;;
  esac
  return 1
}

_botfiles_oracle_source_main_error() {
  if _botfiles_oracle_source_main_required; then
    echo "oracle wrapper: pinned source build unavailable: $*" >&2
    return 1
  fi
  if [ -n "${ORACLE_SOURCE_MAIN_VERBOSE:-}" ]; then
    echo "oracle wrapper: using npm latest fallback because pinned source build is unavailable: $*" >&2
  fi
  return 0
}

_botfiles_oracle_resolve_command() {
  local binary="$1"
  local dist_binary

  BOTFILES_ORACLE_RESOLVED_CMD=()

  case "$binary" in
    oracle)
      dist_binary="oracle-cli.js"
      ;;
    oracle-mcp)
      dist_binary="oracle-mcp.js"
      ;;
    *)
      echo "oracle wrapper: unknown binary '$binary'" >&2
      return 1
      ;;
  esac

  if _botfiles_oracle_source_main_enabled; then
    local source_root source_commit source_head source_bin
    source_root="$(_botfiles_oracle_source_main_root)"
    source_commit="$(_botfiles_oracle_source_main_commit)"
    source_bin="$source_root/dist/bin/$dist_binary"

    if [ ! -r "$source_bin" ]; then
      _botfiles_oracle_source_main_error "missing $source_bin" || return 1
    elif [ ! -d "$source_root/.git" ]; then
      _botfiles_oracle_source_main_error "missing $source_root/.git" || return 1
    elif ! command -v git >/dev/null 2>&1; then
      _botfiles_oracle_source_main_error "git is not available to verify $source_root" || return 1
    else
      source_head="$(git -C "$source_root" rev-parse HEAD 2>/dev/null || true)"
      if [ "$source_head" = "$source_commit" ]; then
        if [ -n "${ORACLE_SOURCE_MAIN_VERBOSE:-}" ]; then
          echo "oracle wrapper: using pinned source build $source_commit at $source_root" >&2
        fi
        BOTFILES_ORACLE_RESOLVED_CMD=(node "$source_bin")
        return 0
      fi
      _botfiles_oracle_source_main_error "$source_root is at ${source_head:-unknown}, expected $source_commit" || return 1
    fi
  fi

  if [ "$binary" = "oracle-mcp" ]; then
    BOTFILES_ORACLE_RESOLVED_CMD=(npx -y @steipete/oracle@latest oracle-mcp)
  else
    BOTFILES_ORACLE_RESOLVED_CMD=(npx -y @steipete/oracle@latest)
  fi
  return 0
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

_botfiles_oracle_model_is_gpt56() {
  local expect_model_value=0
  local arg
  for arg in "$@"; do
    if [ "$expect_model_value" -eq 1 ]; then
      case "$arg" in
        *5.6*|*gpt-5.6*|*GPT-5.6*)
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
      --model=*5.6*|--models=*5.6*|-m*5.6*|--model=*gpt-5.6*|--models=*gpt-5.6*)
        return 0
        ;;
    esac
  done
  return 1
}

_botfiles_oracle_local_remote_chrome_ready() {
  command -v curl >/dev/null 2>&1 &&
    curl --fail --silent --max-time 1 http://127.0.0.1:9223/json/version >/dev/null 2>&1
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
  local oracle_source_main_explicit=0
  if [ "${ORACLE_SOURCE_MAIN+x}" = "x" ]; then
    oracle_source_main_explicit=1
  fi
  local ORACLE_SOURCE_MAIN="${ORACLE_SOURCE_MAIN-}"

  if [ -n "${ORACLE_AZURE_OPENAI_API_KEY:-}" ] && [ -z "${AZURE_OPENAI_API_KEY:-}" ]; then
    export AZURE_OPENAI_API_KEY="$ORACLE_AZURE_OPENAI_API_KEY"
  fi

  if ! _botfiles_oracle_is_subcommand_invocation "$@"; then
    local default_gpt56_model=0
    local default_chatgpt_browser=0
    if ! _botfiles_oracle_engine_specified "$@" && ! _botfiles_oracle_model_specified "$@" && ! _botfiles_oracle_browser_requested "$@"; then
      default_gpt56_model=1
      default_chatgpt_browser=1
    elif _botfiles_oracle_browser_requested "$@" && ! _botfiles_oracle_model_specified "$@"; then
      default_gpt56_model=1
      default_chatgpt_browser=1
    elif { _botfiles_oracle_model_is_gpt55 "$@" || _botfiles_oracle_model_is_gpt56 "$@"; } &&
      ! _botfiles_oracle_engine_specified "$@"; then
      default_chatgpt_browser=1
    fi

    if [ "$default_gpt56_model" -eq 1 ] && [ "$default_chatgpt_browser" -eq 1 ] &&
      [ "$oracle_source_main_explicit" -eq 0 ]; then
      ORACLE_SOURCE_MAIN=1
    fi

    if [ "$default_chatgpt_browser" -eq 1 ]; then
      if ! _botfiles_oracle_engine_specified "$@" && ! _botfiles_oracle_browser_requested "$@"; then
        defaults+=(--engine browser)
      fi
      if ! _botfiles_oracle_option_specified --browser-manual-login "$@" &&
        ! _botfiles_oracle_option_specified --browser-chrome-path "$@" &&
        ! _botfiles_oracle_option_specified --remote-chrome "$@"; then
        if _botfiles_oracle_local_remote_chrome_ready; then
          defaults+=(--remote-chrome 127.0.0.1:9223)
        else
          defaults+=(--browser-manual-login)
          local chrome_path="${ORACLE_CHROME_PATH:-$HOME/pro/botfiles/bin/oracle-chrome-linux}"
          if [ -x "$chrome_path" ]; then
            defaults+=(--browser-chrome-path "$chrome_path")
          fi
        fi
      fi
      if ! _botfiles_oracle_model_specified "$@"; then
        defaults+=(--model gpt-5.6-sol)
      fi
      if ! _botfiles_oracle_option_specified --browser-model-strategy "$@"; then
        if [ "$default_gpt56_model" -eq 1 ] || _botfiles_oracle_model_is_gpt56 "$@"; then
          defaults+=(--browser-model-strategy select)
        else
          defaults+=(--browser-model-strategy current)
        fi
      fi
    elif ! _botfiles_oracle_engine_specified "$@" && ! _botfiles_oracle_browser_requested "$@"; then
      defaults+=(--engine api)
      if ! _botfiles_oracle_model_specified "$@"; then
        defaults+=(--model gpt-5.6-sol)
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
        defaults+=(--model gpt-5.6-sol)
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

  _botfiles_oracle_resolve_command oracle || return 1
  local oracle_cmd=("${BOTFILES_ORACLE_RESOLVED_CMD[@]}")
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
  _botfiles_oracle_resolve_command oracle-mcp || return 1
  local oracle_cmd=("${BOTFILES_ORACLE_RESOLVED_CMD[@]}")
  if [ "$#" -gt 0 ]; then
    oracle_cmd+=("$@")
  fi
  _botfiles_oracle_exec_node24 "${oracle_cmd[@]}"
}
