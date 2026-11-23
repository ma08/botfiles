---
trigger: model_decision
description: "Cross-session orchestration, companion sessions, Zellij message delivery, PR autoreview loops, and Ralph loop orchestrator boundaries. Load whenever coordinating across sessions, Zellij panes, PR review loops, or Ralph loops."
---

# Cross-Session Orchestration and Loops

## Multi-Session Coordination

- For regular non-Symphony multi-session work, use the shared skills `cross-session-context`, `cross-session-message`, and `pr-autoreview-loop`.
- For a persistent companion ticket/session in another agent harness, use `create-companion-session` from the source task or orchestrator. If a matching companion already exists, ask interactively with reuse recommended unless the user already chose reuse or fresh.
- Target other sessions by tracker ref or task slug first. Use `--task-dir`, `--status-file`, or `--zellij-session` only for lower-level or debug workflows.
- Treat task/status metadata as the primary source of truth, transcript tail as a targeted fallback, and live zellij inspection as diagnostic context.
- Never simulate user input into another harness by editing its SQLite databases, JSONL transcripts, or internal notification/app state. Only message another harness through an explicit supported bridge or tool; fail closed if the required transport is unavailable.

## Safe Zellij Messaging (`send-zellij-message`)

- Keep cross-session sends preview-first: run `send-zellij-message` in dry-run mode until the resolved session/tab target is verified, then pass `--execute` and `--submit enter` explicitly.
- Require the helper's composer preflight to be safe before execution, and claim forwarding only when the receipt reports `outcome: delivered` with `delivered: true`. Never treat `executed`, staging, or Enter alone as delivery.
- For long or multiline prompts in Codex targets, `send-zellij-message` adds a delayed confirm Enter only when intended text remains visibly staged after the first Enter.
- Resolve routine, reversible orchestration obstacles autonomously within an approved task. For an already-authorized send, if a target composer holds an unrelated user draft, save that draft into the task scratchpad before replacing it with the intended message and never submit the unrelated draft. Use `--replace-claude-suggestion` only when inspection confirms autocomplete and a flagged preview + cursor probe verifies an empty buffer; confirm the message became a new turn before claiming delivery.
- In non-interactive shells without `XDG_RUNTIME_DIR`, `send-zellij-message` may fall back to `/run/user/<uid>` only when the default zellij namespace has no active exact target and the systemd namespace does (record the selected namespace in the receipt; never switch away from an active default target).
- Treat cross-session message send strictly as bounded prompt delivery into a known live target, not remote control.

## PR Autoreview Loops

- For PR-bearing non-Symphony review loops, use `pr-autoreview-loop` to match current-head reviewer output, address findings, push, and wait until the sweep is clean or genuinely blocked.
- When the loop reports `blocked` or reviewer/check infrastructure fails without an in-session retry path, stop and ask for human input instead of spinning.

## Ralph Loop Boundary

- When a plan uses a Ralph loop, the orchestrator session only prepares the loop files (`PROMPT.md`, `AGENT.md`, `fix_plan.md`, `specs/`, `run-ralph.sh`) and hands off execution (`./run-ralph.sh ...`). Do not implement the code, write the tests, check off `fix_plan.md` items, or commit code changes on behalf of the loop agent.
