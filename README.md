# Botfiles

Configuration files for Claude Code CLI, designed to be synced across multiple machines.

## What's Included

- **settings.json** - Claude Code settings (hooks, plugins, model preferences)
- **statusline-simple.sh** - Custom statusline script
- **hooks/** - Notification hooks for local and WhatsApp alerts
  - Sends notifications when Claude finishes responding
  - Sends notifications when Claude needs permission
  - Sends notifications when Claude asks a question

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

4. **Restart Claude Code**

## Manual Setup

If you prefer manual setup:

```bash
# Create symlinks
ln -sf ~/pro/botfiles/claude/settings.json ~/.claude/settings.json
ln -sf ~/pro/botfiles/claude/statusline-simple.sh ~/.claude/statusline-simple.sh
ln -sf ~/pro/botfiles/claude/hooks ~/.claude/hooks

# Install Python dependencies
cd ~/pro/botfiles/claude/hooks
uv sync
```

## Configuration

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

## Directory Structure

```
botfiles/
├── README.md
├── .gitignore
├── setup.sh
└── claude/
    ├── settings.json
    ├── statusline-simple.sh
    └── hooks/
        ├── .env.example
        ├── .gitignore
        ├── pyproject.toml
        ├── notification.py
        ├── stop.py
        ├── pretooluse_notification.py
        ├── utils.py
        └── whatsapp.py
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
