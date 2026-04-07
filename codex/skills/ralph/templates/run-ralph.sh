#!/bin/bash
# Ralph Loop - {{TASK_NAME}}
#
# Usage: ./run-ralph.sh <engine> [max_iterations]
#
#   engine:         codex | claude
#   max_iterations: optional, default {{MAX_ITERATIONS_DEFAULT}}
#
# Examples:
#   ./run-ralph.sh codex           # Run with Codex (default {{MAX_ITERATIONS_DEFAULT}} iterations)
#   ./run-ralph.sh claude          # Run with Claude Code (default {{MAX_ITERATIONS_DEFAULT}} iterations)
#   ./run-ralph.sh codex 30        # Run with Codex, 30 iterations
#   ./run-ralph.sh claude 15       # Run with Claude Code, 15 iterations

set -e

WORKDIR="{{WORKDIR}}"
MAX_ITERATIONS_DEFAULT={{MAX_ITERATIONS_DEFAULT}}
COMPLETION_PROMISE="{{COMPLETION_PROMISE}}"
LOG_FILE="{{LOG_FILE}}"
TEMP_OUTPUT="/tmp/ralph-iteration-$$.txt"

# --- Engine selection (mandatory first argument) ---
ENGINE="${1:-}"
MAX_ITERATIONS="${2:-$MAX_ITERATIONS_DEFAULT}"

if [ -z "$ENGINE" ]; then
    echo ""
    echo "ERROR: Engine argument is required."
    echo ""
    echo "Usage: ./run-ralph.sh <engine> [max_iterations]"
    echo ""
    echo "  engine:         codex | claude"
    echo "  max_iterations: optional, default $MAX_ITERATIONS_DEFAULT"
    echo ""
    echo "Run one of these:"
    echo ""
    echo "  ./run-ralph.sh codex          # Codex CLI"
    echo "  ./run-ralph.sh claude         # Claude Code CLI"
    echo "  ./run-ralph.sh codex 30       # Codex, 30 iterations"
    echo "  ./run-ralph.sh claude 15      # Claude Code, 15 iterations"
    echo ""
    exit 1
fi

case "$ENGINE" in
    codex)
        RUN_CMD="codex --dangerously-bypass-approvals-and-sandbox exec"
        # Codex may echo the prompt in output, so discount promise matches that
        # already appear in PROMPT.md and only look for assistant-side matches.
        PROMISE_THRESHOLD=1
        ;;
    claude)
        RUN_CMD="claude --dangerously-skip-permissions -p"
        PROMISE_THRESHOLD=1
        ;;
    *)
        echo ""
        echo "ERROR: Unknown engine '$ENGINE'"
        echo ""
        echo "Supported engines:"
        echo "  codex   - OpenAI Codex CLI"
        echo "  claude  - Claude Code CLI"
        echo ""
        echo "Run one of these:"
        echo ""
        echo "  ./run-ralph.sh codex"
        echo "  ./run-ralph.sh claude"
        echo ""
        exit 1
        ;;
esac

cd "$WORKDIR"

echo "=== Ralph Loop: {{TASK_NAME}} ===" | tee "$LOG_FILE"
echo "Engine: $ENGINE ($RUN_CMD)" | tee -a "$LOG_FILE"
echo "Working dir: $WORKDIR" | tee -a "$LOG_FILE"
echo "Max iterations: $MAX_ITERATIONS" | tee -a "$LOG_FILE"
echo "Completion promise: $COMPLETION_PROMISE" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "===========================================" | tee -a "$LOG_FILE"

cleanup() {
    rm -f "$TEMP_OUTPUT"
}
trap cleanup EXIT

for i in $(seq 1 $MAX_ITERATIONS); do
    echo "" | tee -a "$LOG_FILE"
    echo ">>> Iteration $i / $MAX_ITERATIONS - $(date)" | tee -a "$LOG_FILE"
    echo "---" | tee -a "$LOG_FILE"

    # Clear temp file for this iteration
    > "$TEMP_OUTPUT"

    # Stream output in real-time to console, log file, AND temp file for promise detection
    cat PROMPT.md | $RUN_CMD 2>&1 | tee -a "$LOG_FILE" "$TEMP_OUTPUT" || true

    # Discount promise-string matches already present in PROMPT.md so prompt-echo
    # output does not produce a false completion signal.
    PROMPT_PROMISE_COUNT=$(grep -cF "$COMPLETION_PROMISE" PROMPT.md 2>/dev/null || echo "0")
    TOTAL_PROMISE_COUNT=$(grep -cF "$COMPLETION_PROMISE" "$TEMP_OUTPUT" 2>/dev/null || echo "0")
    ASSISTANT_PROMISE_COUNT=$((TOTAL_PROMISE_COUNT - PROMPT_PROMISE_COUNT))
    if [ "$ASSISTANT_PROMISE_COUNT" -lt 0 ]; then
        ASSISTANT_PROMISE_COUNT=0
    fi

    if [ "$ASSISTANT_PROMISE_COUNT" -ge "$PROMISE_THRESHOLD" ]; then
        echo "" | tee -a "$LOG_FILE"
        echo "=== COMPLETED ===" | tee -a "$LOG_FILE"
        echo "Assistant promise detected $ASSISTANT_PROMISE_COUNT times (threshold=$PROMISE_THRESHOLD for $ENGINE; total matches=$TOTAL_PROMISE_COUNT, prompt matches=$PROMPT_PROMISE_COUNT)" | tee -a "$LOG_FILE"
        echo "Finished at iteration $i" | tee -a "$LOG_FILE"
        echo "Ended: $(date)" | tee -a "$LOG_FILE"
        exit 0
    fi

    # Brief pause between iterations
    sleep 3
done

echo "" | tee -a "$LOG_FILE"
echo "=== MAX ITERATIONS REACHED ===" | tee -a "$LOG_FILE"
echo "Ended: $(date)" | tee -a "$LOG_FILE"
exit 1
