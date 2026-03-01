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

# Check SSH workflow tool availability (warn-only).
check_ssh_workflow_tools() {
    echo "Checking SSH workflow tools..."
    echo ""
    echo "=== SSH Workflow Tools (optional but recommended) ==="

    if command -v ssh &> /dev/null; then
        echo "  [OK] ssh"
    else
        echo "  [MISSING] ssh (required for work-* commands)"
        echo "    Install OpenSSH client using your OS package manager."
    fi

    if command -v fzf &> /dev/null; then
        echo "  [OK] fzf (interactive session picker)"
    else
        echo "  [MISSING] fzf (interactive session picker)"
        echo "    Install with: brew install fzf"
        echo "    or: sudo apt-get install -y fzf"
        echo "    You can still run with explicit session names, e.g. work-ml my-session"
    fi

    if command -v mosh &> /dev/null; then
        echo "  [OK] mosh (used by mosh-first workflows)"
    else
        echo "  [MISSING] mosh (optional; ssh fallback still works)"
        echo "    Install with: brew install mosh"
        echo "    or: sudo apt-get install -y mosh"
    fi

    if [ -f "$HOME/.ssh/config" ]; then
        echo "  [OK] ~/.ssh/config detected"
    else
        echo "  [MISSING] ~/.ssh/config"
        echo "    Add host aliases used by work-* commands (for example ladduu-dev-ml-vm-ts)."
    fi

    echo "  [INFO] Remote hosts need zellij installed for work-* attach/create commands."
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

    if [ -f "$CLAUDE_DIR/CLAUDE.md" ] && [ ! -L "$CLAUDE_DIR/CLAUDE.md" ]; then
        echo "  Backing up CLAUDE.md"
        mv "$CLAUDE_DIR/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md.bak.$(date +%Y%m%d%H%M%S)"
    fi

    if [ -f "$CODEX_DIR/config.toml" ] && [ ! -L "$CODEX_DIR/config.toml" ]; then
        echo "  Backing up codex config.toml"
        mv "$CODEX_DIR/config.toml" "$CODEX_DIR/config.toml.bak.$(date +%Y%m%d%H%M%S)"
    fi

    if [ -e "$CODEX_DIR/skills" ] && [ ! -L "$CODEX_DIR/skills" ]; then
        echo "  Backing up codex skills"
        mv "$CODEX_DIR/skills" "$CODEX_DIR/skills.bak.$(date +%Y%m%d%H%M%S)"
    fi

    if [ -f "$CODEX_DIR/AGENTS.md" ] && [ ! -L "$CODEX_DIR/AGENTS.md" ]; then
        echo "  Backing up codex AGENTS.md"
        mv "$CODEX_DIR/AGENTS.md" "$CODEX_DIR/AGENTS.md.bak.$(date +%Y%m%d%H%M%S)"
    fi

    if [ -f "$HOME/.config/zellij/config.kdl" ] && [ ! -L "$HOME/.config/zellij/config.kdl" ]; then
        echo "  Backing up zellij config.kdl"
        mv "$HOME/.config/zellij/config.kdl" "$HOME/.config/zellij/config.kdl.bak.$(date +%Y%m%d%H%M%S)"
    fi

    echo ""
}

# Create symlinks
create_symlinks() {
    echo "Creating symlinks..."

    # Ensure .claude directory exists
    mkdir -p "$CLAUDE_DIR"
    mkdir -p "$CODEX_DIR"
    mkdir -p "$SCRIPT_DIR/codex/skills"
    mkdir -p "$SCRIPT_DIR/secrets/local"
    mkdir -p "$HOME/.config/zellij"

    # Remove existing symlinks if they exist
    [ -L "$CLAUDE_DIR/settings.json" ] && rm "$CLAUDE_DIR/settings.json"
    [ -L "$CLAUDE_DIR/statusline-simple.sh" ] && rm "$CLAUDE_DIR/statusline-simple.sh"
    [ -L "$CLAUDE_DIR/hooks" ] && rm "$CLAUDE_DIR/hooks"
    [ -L "$CLAUDE_DIR/skills" ] && rm "$CLAUDE_DIR/skills"
    [ -L "$CODEX_DIR/config.toml" ] && rm "$CODEX_DIR/config.toml"
    [ -L "$CODEX_DIR/skills" ] && rm "$CODEX_DIR/skills"
    [ -L "$CODEX_DIR/AGENTS.md" ] && rm "$CODEX_DIR/AGENTS.md"
    [ -L "$HOME/.config/zellij/config.kdl" ] && rm "$HOME/.config/zellij/config.kdl"

    # Create new symlinks
    ln -sf "$SCRIPT_DIR/claude/settings.json" "$CLAUDE_DIR/settings.json"
    echo "  settings.json -> $SCRIPT_DIR/claude/settings.json"

    ln -sf "$SCRIPT_DIR/claude/statusline-simple.sh" "$CLAUDE_DIR/statusline-simple.sh"
    echo "  statusline-simple.sh -> $SCRIPT_DIR/claude/statusline-simple.sh"

    ln -sf "$SCRIPT_DIR/claude/hooks" "$CLAUDE_DIR/hooks"
    echo "  hooks/ -> $SCRIPT_DIR/claude/hooks"

    ln -sf "$SCRIPT_DIR/claude/skills" "$CLAUDE_DIR/skills"
    echo "  skills/ -> $SCRIPT_DIR/claude/skills"

    [ -L "$CLAUDE_DIR/CLAUDE.md" ] && rm "$CLAUDE_DIR/CLAUDE.md"

    ln -sf "$SCRIPT_DIR/claude/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"
    echo "  CLAUDE.md -> $SCRIPT_DIR/claude/CLAUDE.md"

    ln -sf "$SCRIPT_DIR/codex/config.toml" "$CODEX_DIR/config.toml"
    echo "  codex config.toml -> $SCRIPT_DIR/codex/config.toml"

    ln -sf "$SCRIPT_DIR/codex/skills" "$CODEX_DIR/skills"
    echo "  codex skills/ -> $SCRIPT_DIR/codex/skills"

    ln -sf "$SCRIPT_DIR/codex/AGENTS.md" "$CODEX_DIR/AGENTS.md"
    echo "  codex AGENTS.md -> $SCRIPT_DIR/codex/AGENTS.md"

    ln -sf "$SCRIPT_DIR/zellij/config.kdl" "$HOME/.config/zellij/config.kdl"
    echo "  zellij config.kdl -> $SCRIPT_DIR/zellij/config.kdl"

    echo ""
}

# Install Python dependencies
install_deps() {
    echo "Installing Python dependencies..."
    cd "$SCRIPT_DIR/claude/hooks"
    uv sync
    echo ""
}

# Check for secret/config files
check_secrets() {
    echo "Checking configuration files..."
    echo ""
    mkdir -p "$SCRIPT_DIR/secrets/local"

    check_secret_file() {
        local label="$1"
        local runtime_path="$2"
        local template_path="$3"
        local display_path="${runtime_path#$SCRIPT_DIR/}"

        if [ -f "$runtime_path" ]; then
            echo "  [OK] $display_path ($label)"
        else
            echo "  [MISSING] $display_path ($label)"
            echo "    cp $template_path $runtime_path"
        fi
    }

    echo "=== Centralized Secrets (strict cutover) ==="
    check_secret_file \
        "AWS Bedrock for Claude Code" \
        "$SCRIPT_DIR/secrets/local/claude-bedrock.rc" \
        "$SCRIPT_DIR/secrets/templates/claude-bedrock.rc.example"
    check_secret_file \
        "GCP Vertex for Claude Code" \
        "$SCRIPT_DIR/secrets/local/claude-vertex.rc" \
        "$SCRIPT_DIR/secrets/templates/claude-vertex.rc.example"
    check_secret_file \
        "Azure OpenAI for Codex" \
        "$SCRIPT_DIR/secrets/local/codex-azure.rc" \
        "$SCRIPT_DIR/secrets/templates/codex-azure.rc.example"
    check_secret_file \
        "OpenAI API for Codex" \
        "$SCRIPT_DIR/secrets/local/codex-openai.rc" \
        "$SCRIPT_DIR/secrets/templates/codex-openai.rc.example"
    check_secret_file \
        "Azure resource for OpenCode" \
        "$SCRIPT_DIR/secrets/local/opencode-azure.rc" \
        "$SCRIPT_DIR/secrets/templates/opencode-azure.rc.example"
    check_secret_file \
        "Claude/Codex hook notifications" \
        "$SCRIPT_DIR/secrets/local/claude-hooks.rc" \
        "$SCRIPT_DIR/secrets/templates/claude-hooks.rc.example"

    unset -f check_secret_file

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

# Setup git identity (interactive, no hardcoded values)
setup_git_identity() {
    echo "Checking git identity..."

    local current_name current_email
    current_name="$(git config --global user.name 2>/dev/null || true)"
    current_email="$(git config --global user.email 2>/dev/null || true)"

    # Check if values look like placeholders or are unset
    local needs_setup=false
    if [ -z "$current_name" ] || [ "$current_name" = "Your Name" ]; then
        needs_setup=true
    fi
    if [ -z "$current_email" ] || [ "$current_email" = "your.email@example.com" ]; then
        needs_setup=true
    fi

    if [ "$needs_setup" = true ]; then
        echo ""
        echo "  WARNING: Git identity is not configured (or uses placeholder values)."
        echo "  Without a proper identity, your commits will show as 'Your Name'."
        echo "  This affects commit attribution on GitHub and other platforms."
        echo ""
        echo "  Current: name='${current_name:-<unset>}' email='${current_email:-<unset>}'"
        echo ""

        local git_name git_email
        read -p "  Git user.name: " git_name
        read -p "  Git user.email: " git_email

        if [ -n "$git_name" ] && [ -n "$git_email" ]; then
            git config --global user.name "$git_name"
            git config --global user.email "$git_email"
            echo "  [SET] user.name = $git_name"
            echo "  [SET] user.email = $git_email"
        else
            echo "  Skipped (empty input). Set manually with:"
            echo "    git config --global user.name 'Your Name'"
            echo "    git config --global user.email 'you@example.com'"
        fi
    else
        echo "  [OK] Git identity already configured: $current_name <$current_email>"
    fi
    echo ""
}

# Main
main() {
    check_prerequisites
    setup_git_identity
    check_ssh_workflow_tools
    backup_existing
    create_symlinks
    install_deps
    check_secrets
    setup_shell_rc

    echo "=== Setup Complete ==="
    echo ""
    echo "Claude Code configuration is now symlinked to botfiles."
    echo "Codex CLI configuration, skills, and AGENTS.md are now symlinked to botfiles."
    echo "Zellij config is now symlinked to botfiles."
    echo "Restart Claude Code for changes to take effect."
}

main "$@"
