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
- **codex/** - Codex CLI config and provider environment templates
- **.botrc** - Shell loader that sources Claude/Codex env configs

## Prerequisites

- [Claude Code CLI](https://claude.ai/claude-code) installed
- [uv](https://github.com/astral-sh/uv) - Python package manager
- [terminal-notifier](https://github.com/julienXX/terminal-notifier) - macOS notifications (optional)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install terminal-notifier (macOS)
brew install terminal-notifier
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
ln -sf ~/pro/botfiles/codex/config.toml ~/.codex/config.toml

# Install Python dependencies
cd ~/pro/botfiles/claude/hooks
uv sync
```

## Configuration

### Shell Environment (.botrc)

`.botrc` sources `claude/.vertex_claude_config_rc` and `codex/.azure_codex_config_rc` if present.
Add it to your shell startup file:

```bash
source ~/pro/botfiles/.botrc
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

Skills extend Claude Code with specialized capabilities. After running `setup.sh`, skills are available at `~/.claude/skills/`.

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
├── codex/
│   ├── config.toml
│   └── .azure_codex_config_rc.example
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
