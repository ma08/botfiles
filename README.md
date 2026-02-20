# Botfiles

Configuration files for Claude Code CLI, designed to be synced across multiple machines.

## What's Included

- **settings.json** - Claude Code settings (hooks, plugins, model preferences)
- **statusline-simple.sh** - Custom statusline script
- **hooks/** - Notification hooks for local and WhatsApp alerts
  - Sends notifications when Claude finishes responding
  - Sends notifications when Claude needs permission
  - Sends notifications when Claude asks a question
- **skills/** - Claude Code skills for extended capabilities
  - **notion/** - Notion workspace integration
- **codex/** - Codex CLI config, provider env templates, synced skills, and global AGENTS instructions
- **.botrc** - Shell loader that sources Claude/Codex env configs and modular shell scripts
- **shell/** - Reusable shell modules loaded by `.botrc` (for example SSH workflow helpers)

## Prerequisites

- [Claude Code CLI](https://claude.ai/claude-code) installed
- [uv](https://github.com/astral-sh/uv) - Python package manager
- [terminal-notifier](https://github.com/julienXX/terminal-notifier) - macOS notifications (optional)
- [fzf](https://github.com/junegunn/fzf) - interactive session picker for `work-*` SSH workflows (optional but recommended)
- [mosh](https://mosh.org/) - mobile shell transport for mosh-first workflows (optional; SSH fallback remains available)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install terminal-notifier (macOS)
brew install terminal-notifier

# Install optional SSH workflow tools (macOS)
brew install fzf mosh
```

## Quick Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url> ~/pro/botfiles
   cd ~/pro/botfiles
   ```

2. **Run the setup script**
   ```bash
   ./setup.sh
   ```
   The script now also performs warn-only checks for SSH workflow dependencies (`ssh`, `fzf`, `mosh`) and `~/.ssh/config`.

3. **Configure WhatsApp notifications (optional)**
   ```bash
   cp claude/hooks/.env.example claude/hooks/.env
   # Edit .env with your WhatsApp credentials
   ```

4. **Configure Codex Azure credentials**
   ```bash
   cp codex/.azure_codex_config_rc.example codex/.azure_codex_config_rc
   # Edit .azure_codex_config_rc with your API key
   ```

5. **Load shared env config**
   ```bash
   echo 'source ~/pro/botfiles/.botrc' >> ~/.zshrc
   source ~/.zshrc
   ```

6. **Restart Claude Code**

## Manual Setup

If you prefer manual setup:

```bash
# Create symlinks
ln -sf ~/pro/botfiles/claude/settings.json ~/.claude/settings.json
ln -sf ~/pro/botfiles/claude/statusline-simple.sh ~/.claude/statusline-simple.sh
ln -sf ~/pro/botfiles/claude/hooks ~/.claude/hooks
ln -sf ~/pro/botfiles/claude/skills ~/.claude/skills
ln -sf ~/pro/botfiles/codex/config.toml ~/.codex/config.toml
ln -sf ~/pro/botfiles/codex/skills ~/.codex/skills
ln -sf ~/pro/botfiles/codex/AGENTS.md ~/.codex/AGENTS.md

# Install Python dependencies
cd ~/pro/botfiles/claude/hooks
uv sync
```

## Configuration

### Shell Environment (.botrc)

`.botrc` sources provider config files and then loads modular scripts from `shell/*.sh` in lexical order.
`setup.sh` also symlinks `~/.codex/AGENTS.md` to `codex/AGENTS.md`.
Add it to your shell startup file:

```bash
source ~/pro/botfiles/.botrc
```

Codex notify flow:
- `codex/config.toml` only calls `codex/hooks/run-codex-notify.sh`.
- `shell/10-uv-bin.sh` resolves `UV_BIN` once for Linux/macOS portability.

### SSH Workflow Commands

The `shell/20-ssh-workflows.sh` module provides reconnect-friendly helpers for zellij workflows:

```bash
work-ml            # mosh-first connect to ML VM, pick/create zellij session
work-ml-ssh        # SSH-only fallback path for ML VM
work-arya          # SSH-first connect to Aryabhatta, pick/create zellij session
work-arya-mosh     # mosh-first path for Aryabhatta (use when UDP is available)
work-arya-ssh      # explicit SSH path for Aryabhatta
mml                # raw shell shortcut (mosh-first, no zellij attach)
marya              # raw shell shortcut (mosh-first, no zellij attach)
cursor-ml          # open/reuse Cursor window at ML VM home over Remote-SSH
```

Dependency behavior:
- `fzf` is required for interactive picker mode.
- If `fzf` is missing, pass a session name explicitly (example: `work-ml my-session`).
- `mosh` is only required for mosh-first commands (`work-ml`, `work-arya-mosh`).
- If `mosh` is missing or transport fails, workflows fall back to SSH.
- Cursor Remote-SSH uses SSH transport and cannot run directly over mosh transport.
- Use `cursor-ml` for editor workflow and `mml` for resilient terminal-only workflow.

Optional environment variables (set before sourcing `.botrc`) let you override host aliases:

```bash
export BOT_ML_HOST_PRIMARY=ladduu-dev-ml-vm-ts
export BOT_ML_HOST_FALLBACK=ladduu-dev-ml-vm
export BOT_ARYA_HOST=ladduu-dev-aryabhatta
export BOT_CURSOR_ML_HOST_PRIMARY=ladduu-dev-ml-vm-ts
export BOT_CURSOR_ML_HOST_FALLBACK=ladduu-dev-ml-vm
export BOT_CURSOR_ML_PATH=/home/azureuser
```

### WhatsApp Notifications

To enable WhatsApp notifications, create `claude/hooks/.env` with:

```env
WHATSAPP_ENABLED=true
WHATSAPP_TOKEN=your_whatsapp_cloud_api_token
PHONE_NUMBER_ID=your_phone_number_id
NOTIFY_PHONE_NUMBER=+1234567890
SYSTEM_NAME=MyMachineName
```

You'll need a [Meta WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/cloud-api) account.

### System Name

The `SYSTEM_NAME` is included in WhatsApp notifications to identify which machine sent the alert. If not set, it defaults to the hostname.

### Codex Provider Credentials

Create `codex/.azure_codex_config_rc` from the template:

```bash
cp codex/.azure_codex_config_rc.example codex/.azure_codex_config_rc
```

This file is ignored by git and sourced via `.botrc`.

## Skills

Skills extend Claude Code and Codex with specialized capabilities.
After running `setup.sh`:

- Claude skills are available at `~/.claude/skills/` (backed by `claude/skills/`)
- Codex skills are available at `~/.codex/skills/` (backed by `codex/skills/`)
- Codex **system** skills under `~/.codex/skills/.system/` are machine-managed and intentionally git-ignored in this repo (to allow version/platform differences across machines)

### Notion Skill

Integrates with Notion workspaces for reading/writing pages, searching, and managing databases.
I created this myself to have a skill-only Notion-Claude Code integration that avoids MCPs which were causing [context bloating](https://x.com/curious_queue/status/2008612572992315850?s=20).

**Setup:**

1. Install the Notion SDK:
   ```bash
   npm install -g @notionhq/client
   ```

2. Create a [Notion Integration](https://www.notion.so/my-integrations):
   - Go to https://www.notion.so/my-integrations
   - Create a new integration
   - Copy the "Internal Integration Token" (starts with `ntn_`)

3. Set environment variables (either in ~/.zshrc or ~/.bashrc or have a start session hook load them up):
   ```bash
   export NOTION_API_KEY="ntn_your_token_here" #Make sure that API key has read/write permissions to the pages/databases you want to access
   export NOTION_UPDATES_DB_ID="your_database_id"  # Optional
   ```

4. Share pages/databases with your integration in Notion

**Test the connection:**
```bash
node ~/.claude/skills/notion/examples/test-connection.js
```

See `claude/skills/notion/README.md` for detailed usage.

## Web Search (via LiteLLM Proxy)

When using Claude Code with AWS Bedrock, web search is not natively supported.
The LiteLLM proxy enables web search by intercepting search requests and routing them to Exa AI.

**Quick usage:**
```bash
ccws-start    # Start the proxy (background)
ccws          # Run Claude Code with web search
ccws-stop     # Stop the proxy when done
```

**First-time setup:**
1. Install litellm: `uv tool install 'litellm[proxy]'`
2. Copy API key: `cp litellm/.env.example litellm/.env`
3. Edit `litellm/.env` with your Exa AI API key

See `litellm/README.md` for detailed setup and troubleshooting.

## Directory Structure

```
botfiles/
├── .botrc
├── README.md
├── .gitignore
├── setup.sh
├── shell/
│   └── 20-ssh-workflows.sh
├── codex/
│   ├── AGENTS.md
│   ├── config.toml
│   ├── .azure_codex_config_rc.example
│   └── skills/
│       └── README.md
├── litellm/
│   ├── config.yaml
│   ├── .env.example
│   ├── start-proxy.sh
│   └── README.md
└── claude/
    ├── settings.json
    ├── statusline-simple.sh
    ├── hooks/
    │   ├── .env.example
    │   ├── .gitignore
    │   ├── pyproject.toml
    │   ├── notification.py
    │   ├── stop.py
    │   ├── pretooluse_notification.py
    │   ├── utils.py
    │   └── whatsapp.py
    └── skills/
        └── notion/
            ├── README.md
            ├── SKILL.md
            └── examples/
```

## Updating

To pull updates on any machine:

```bash
cd ~/pro/botfiles
git pull
cd claude/hooks && uv sync  # If dependencies changed
```

Restart Claude Code after pulling updates.

## Adding New Machines

1. Clone this repo to `~/pro/botfiles`
2. Run `./setup.sh`
3. Create `.env` with your WhatsApp credentials
4. Restart Claude Code

## License

Private configuration files.
