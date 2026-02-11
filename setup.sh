#!/bin/bash
#
# Botfiles Setup Script
# Sets up Claude Code configuration symlinks and dependencies
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
CODEX_DIR="$HOME/.codex"

echo "=== Botfiles Setup ==="
echo "Script directory: $SCRIPT_DIR"
echo "Claude directory: $CLAUDE_DIR"
echo "Codex directory: $CODEX_DIR"
echo ""

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."

    if ! command -v uv &> /dev/null; then
        echo "ERROR: uv is not installed"
        echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    echo "  - uv: OK"

    if ! command -v terminal-notifier &> /dev/null; then
        echo "WARNING: terminal-notifier not installed (needed for local notifications)"
        echo "Install with: brew install terminal-notifier"
    else
        echo "  - terminal-notifier: OK"
    fi

    echo ""
}

# Backup existing files (if not already symlinks)
backup_existing() {
    echo "Checking for existing files to backup..."

    if [ -f "$CLAUDE_DIR/settings.json" ] && [ ! -L "$CLAUDE_DIR/settings.json" ]; then
        echo "  Backing up settings.json"
        mv "$CLAUDE_DIR/settings.json" "$CLAUDE_DIR/settings.json.bak.$(date +%Y%m%d%H%M%S)"
    fi

    if [ -f "$CLAUDE_DIR/statusline-simple.sh" ] && [ ! -L "$CLAUDE_DIR/statusline-simple.sh" ]; then
        echo "  Backing up statusline-simple.sh"
        mv "$CLAUDE_DIR/statusline-simple.sh" "$CLAUDE_DIR/statusline-simple.sh.bak.$(date +%Y%m%d%H%M%S)"
    fi

    if [ -d "$CLAUDE_DIR/hooks" ] && [ ! -L "$CLAUDE_DIR/hooks" ]; then
        echo "  Backing up hooks directory"
        mv "$CLAUDE_DIR/hooks" "$CLAUDE_DIR/hooks.bak.$(date +%Y%m%d%H%M%S)"
    fi

    if [ -d "$CLAUDE_DIR/skills" ] && [ ! -L "$CLAUDE_DIR/skills" ]; then
        echo "  Backing up skills directory"
        mv "$CLAUDE_DIR/skills" "$CLAUDE_DIR/skills.bak.$(date +%Y%m%d%H%M%S)"
    fi

    if [ -f "$CODEX_DIR/config.toml" ] && [ ! -L "$CODEX_DIR/config.toml" ]; then
        echo "  Backing up codex config.toml"
        mv "$CODEX_DIR/config.toml" "$CODEX_DIR/config.toml.bak.$(date +%Y%m%d%H%M%S)"
    fi

    echo ""
}

# Create symlinks
create_symlinks() {
    echo "Creating symlinks..."

    # Ensure .claude directory exists
    mkdir -p "$CLAUDE_DIR"
    mkdir -p "$CODEX_DIR"

    # Remove existing symlinks if they exist
    [ -L "$CLAUDE_DIR/settings.json" ] && rm "$CLAUDE_DIR/settings.json"
    [ -L "$CLAUDE_DIR/statusline-simple.sh" ] && rm "$CLAUDE_DIR/statusline-simple.sh"
    [ -L "$CLAUDE_DIR/hooks" ] && rm "$CLAUDE_DIR/hooks"
    [ -L "$CLAUDE_DIR/skills" ] && rm "$CLAUDE_DIR/skills"
    [ -L "$CODEX_DIR/config.toml" ] && rm "$CODEX_DIR/config.toml"

    # Create new symlinks
    ln -sf "$SCRIPT_DIR/claude/settings.json" "$CLAUDE_DIR/settings.json"
    echo "  settings.json -> $SCRIPT_DIR/claude/settings.json"

    ln -sf "$SCRIPT_DIR/claude/statusline-simple.sh" "$CLAUDE_DIR/statusline-simple.sh"
    echo "  statusline-simple.sh -> $SCRIPT_DIR/claude/statusline-simple.sh"

    ln -sf "$SCRIPT_DIR/claude/hooks" "$CLAUDE_DIR/hooks"
    echo "  hooks/ -> $SCRIPT_DIR/claude/hooks"

    ln -sf "$SCRIPT_DIR/claude/skills" "$CLAUDE_DIR/skills"
    echo "  skills/ -> $SCRIPT_DIR/claude/skills"

    ln -sf "$SCRIPT_DIR/codex/config.toml" "$CODEX_DIR/config.toml"
    echo "  codex config.toml -> $SCRIPT_DIR/codex/config.toml"

    echo ""
}

# Install Python dependencies
install_deps() {
    echo "Installing Python dependencies..."
    cd "$SCRIPT_DIR/claude/hooks"
    uv sync

    # Install LiteLLM proxy (optional, for web search with Bedrock)
    if ! command -v litellm &> /dev/null; then
        echo "Installing LiteLLM proxy (for Bedrock web search)..."
        uv tool install 'litellm[proxy]'
    else
        echo "  - litellm: OK"
    fi
    echo ""
}

# Check for secret/config files
check_secrets() {
    echo "Checking configuration files..."
    echo ""

    # Claude Code Hooks (.env for WhatsApp)
    echo "=== Claude Code Hooks ==="
    if [ -f "$SCRIPT_DIR/claude/hooks/.env" ]; then
        echo "  [OK] claude/hooks/.env"
    else
        echo "  [MISSING] claude/hooks/.env (WhatsApp notifications)"
        echo "    cp $SCRIPT_DIR/claude/hooks/.env.example $SCRIPT_DIR/claude/hooks/.env"
    fi

    # Claude Code provider configs (Bedrock/Vertex)
    echo ""
    echo "=== Claude Code Providers (optional) ==="
    if [ -f "$SCRIPT_DIR/claude/.bedrock_claude_config_rc" ]; then
        echo "  [OK] claude/.bedrock_claude_config_rc (AWS Bedrock)"
    else
        echo "  [MISSING] claude/.bedrock_claude_config_rc (AWS Bedrock)"
        echo "    cp $SCRIPT_DIR/claude/.bedrock_claude_config_rc.example $SCRIPT_DIR/claude/.bedrock_claude_config_rc"
    fi

    if [ -f "$SCRIPT_DIR/claude/.vertex_claude_config_rc" ]; then
        echo "  [OK] claude/.vertex_claude_config_rc (GCP Vertex)"
    else
        echo "  [MISSING] claude/.vertex_claude_config_rc (GCP Vertex)"
        echo "    cp $SCRIPT_DIR/claude/.vertex_claude_config_rc.example $SCRIPT_DIR/claude/.vertex_claude_config_rc"
    fi

    # Codex Azure config
    echo ""
    echo "=== Codex CLI ==="
    if [ -f "$SCRIPT_DIR/codex/.azure_codex_config_rc" ]; then
        echo "  [OK] codex/.azure_codex_config_rc"
    else
        echo "  [MISSING] codex/.azure_codex_config_rc (Azure OpenAI API key)"
        echo "    cp $SCRIPT_DIR/codex/.azure_codex_config_rc.example $SCRIPT_DIR/codex/.azure_codex_config_rc"
    fi

    if [ -f "$SCRIPT_DIR/codex/.openai_codex_config_rc" ]; then
        echo "  [OK] codex/.openai_codex_config_rc"
    else
        echo "  [MISSING] codex/.openai_codex_config_rc (OpenAI API key)"
        echo "    cp $SCRIPT_DIR/codex/.openai_codex_config_rc.example $SCRIPT_DIR/codex/.openai_codex_config_rc"
    fi

    # OpenCode Azure config
    echo ""
    echo "=== OpenCode (optional) ==="
    if [ -f "$SCRIPT_DIR/opencode/.azure_codex_config_rc" ]; then
        echo "  [OK] opencode/.azure_codex_config_rc"
    else
        echo "  [MISSING] opencode/.azure_codex_config_rc (Azure OpenAI)"
        echo "    cp $SCRIPT_DIR/opencode/.azure_codex_config_rc.example $SCRIPT_DIR/opencode/.azure_codex_config_rc"
    fi

    # LiteLLM Web Search (for Bedrock)
    echo ""
    echo "=== LiteLLM Web Search (optional) ==="
    if [ -f "$SCRIPT_DIR/litellm/.env" ]; then
        echo "  [OK] litellm/.env (Exa AI API key)"
    else
        echo "  [MISSING] litellm/.env (Exa AI for web search)"
        echo "    cp $SCRIPT_DIR/litellm/.env.example $SCRIPT_DIR/litellm/.env"
    fi

    echo ""
}

# Setup shell rc file to source .botrc
setup_shell_rc() {
    echo "Checking shell configuration..."

    # Determine rc file based on current shell
    case "$SHELL" in
        */zsh)  RC_FILE="$HOME/.zshrc" ;;
        */bash) RC_FILE="$HOME/.bashrc" ;;
        *)      RC_FILE="" ;;
    esac

    if [ -z "$RC_FILE" ]; then
        echo "  Unknown shell: $SHELL"
        echo "  Please manually add to your shell rc file:"
        echo "    source $SCRIPT_DIR/.botrc"
        echo ""
        return
    fi

    BOTRC_LINE="source $SCRIPT_DIR/.botrc"

    # Check if already present
    if [ -f "$RC_FILE" ] && grep -qF ".botrc" "$RC_FILE"; then
        echo "  [OK] .botrc already sourced in $RC_FILE"
        echo ""
        return
    fi

    # Ask user for confirmation
    echo ""
    echo "  .botrc is not sourced in $RC_FILE"
    echo "  This loads environment variables for Claude Code and Codex."
    echo ""
    read -p "  Add 'source $SCRIPT_DIR/.botrc' to $RC_FILE? [Y/n] " response

    case "$response" in
        [nN]*)
            echo "  Skipped. To add manually:"
            echo "    echo 'source $SCRIPT_DIR/.botrc' >> $RC_FILE"
            ;;
        *)
            echo "" >> "$RC_FILE"
            echo "# Config files and env vars for Claude/Codex from botfiles" >> "$RC_FILE"
            echo "$BOTRC_LINE" >> "$RC_FILE"
            echo "  [ADDED] source line added to $RC_FILE"
            echo "  Run 'source $RC_FILE' or restart your terminal to apply."
            ;;
    esac
    echo ""
}

# Main
main() {
    check_prerequisites
    backup_existing
    create_symlinks
    install_deps
    check_secrets
    setup_shell_rc

    echo "=== Setup Complete ==="
    echo ""
    echo "Claude Code configuration is now symlinked to botfiles."
    echo "Restart Claude Code for changes to take effect."
}

main "$@"
