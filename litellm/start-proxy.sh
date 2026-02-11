#!/bin/bash
# LiteLLM Web Search Proxy for Claude Code + Bedrock
#
# USAGE:
#   ./start-proxy.sh           # Start proxy (foreground)
#   ./start-proxy.sh --bg      # Start proxy (background)
#   ./start-proxy.sh --stop    # Stop background proxy
#
# After starting, run Claude Code in a new terminal with:
#   ccws   (alias for claude with web search)

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$SCRIPT_DIR/.proxy.pid"

# Load environment
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Debug logging (uncomment to troubleshoot)
# export LITELLM_LOG=DEBUG

case "${1:-}" in
    --stop)
        # Kill all litellm processes (not just PID file) to avoid zombies
        pkill -f "litellm.*config.yaml" 2>/dev/null || true
        rm -f "$PIDFILE"
        echo "Proxy stopped"
        ;;
    --bg)
        echo "Starting LiteLLM proxy in background..."
        nohup litellm --config "$SCRIPT_DIR/config.yaml" --port 4000 > "$SCRIPT_DIR/proxy.log" 2>&1 &
        echo $! > "$PIDFILE"
        echo "Proxy started (PID: $(cat $PIDFILE))"
        echo "Logs: $SCRIPT_DIR/proxy.log"
        echo ""
        echo "Now run Claude Code with: ccws"
        ;;
    *)
        echo "Starting LiteLLM proxy..."
        echo "Press Ctrl+C to stop"
        echo ""
        litellm --config "$SCRIPT_DIR/config.yaml" --port 4000
        ;;
esac
