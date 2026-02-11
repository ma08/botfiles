# LiteLLM Web Search Proxy

Enables web search in Claude Code when using AWS Bedrock.

## Quick Start

### 1. One-time setup
```bash
# Install litellm proxy
uv tool install 'litellm[proxy]'

# Copy your Exa API key
cp .env.example .env
# Edit .env with your EXA_API_KEY
```

### 2. Start the proxy
```bash
# Option A: Foreground (see logs)
./start-proxy.sh

# Option B: Background
./start-proxy.sh --bg
```

### 3. Use Claude Code with web search
```bash
# In a new terminal
ccws   # alias that points Claude to the proxy
```

### 4. Stop the proxy (if running in background)
```bash
./start-proxy.sh --stop
```

## How It Works

1. LiteLLM proxy runs on localhost:4000
2. Claude Code connects to the proxy instead of directly to Bedrock
3. Proxy intercepts `web_search` tool calls
4. Searches execute via Exa AI and results return to Claude

## Troubleshooting

**Proxy won't start:**
- Check if port 4000 is in use: `lsof -i :4000`
- Verify AWS credentials: `aws sts get-caller-identity`

**Web search not working:**
- Verify proxy is running: `curl http://localhost:4000/health`
- Check proxy logs: `tail -f proxy.log`

**"Auth conflict" warning:**
This appears when you're logged into claude.ai AND using the proxy. It's expected:
- Select "Yes" when asked about the custom API key
- The warning can be ignored - Claude will use the proxy correctly
- To avoid the warning, run `claude /logout` first (but then you can't use regular `cc` without logging back in)

## Aliases

Added to `.botrc`:
- `ccws` - Claude Code with web search (uses proxy)
- `ccwsc` - Continue last session with web search
- `ccws-start` - Start the proxy
- `ccws-stop` - Stop the proxy

## Technical Notes

The `ccws` command uses `--api-key` and `--base-url` flags instead of environment variables to avoid auth conflicts with your claude.ai login.
