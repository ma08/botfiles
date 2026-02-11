#!/bin/bash
# Claude Code with Web Search (via LiteLLM proxy)
#
# This script:
# 1. Checks if proxy is running
# 2. Sets the right environment variables
# 3. Warns about auth if needed

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if proxy is running
if ! curl -s http://localhost:4000/health -H "Authorization: Bearer sk-litellm-local" > /dev/null 2>&1; then
    echo "Error: LiteLLM proxy is not running."
    echo "Start it with: ccws-start"
    exit 1
fi

# Check if user is logged into claude.ai (has a session token)
if [ -f "$HOME/.claude/.credentials" ] || [ -f "$HOME/.claude/credentials.json" ]; then
    echo "Note: You may see an 'Auth conflict' warning - this is expected."
    echo "Select 'Yes' when asked about the custom API key."
    echo ""
fi

# Run claude with proxy settings
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=sk-litellm-local
export CLAUDE_CODE_USE_BEDROCK=0  # Use Anthropic API format (proxy handles Bedrock)

exec claude "$@"
