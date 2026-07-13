---
name: rename-active-codex-threads
description: Rename all recently active Codex threads across the local app and connected remote hosts using tracker ID, stable task domain, and current status. Use when the user asks to update, refresh, normalize, or rename active/recent Codex thread names in one batch, or invokes $rename-active-codex-threads.
---

# Rename Active Codex Threads

Run the shared thread-naming workflow immediately rather than waiting for the recurring automation.

## Naming Contract

Use the `rename-codex-thread` convention:

```text
<tracker id> · <stable domain> · <current status>
```

- Use a human-facing Linear ID or GitHub issue reference; never use raw tracker UUIDs.
- Use `[no ticker]` when no tracker exists.
- Keep the stable domain to roughly 2–4 words. Preserve an existing compliant middle segment unless it is clearly inaccurate.
- Keep current status to roughly 2–5 words. Change it only after a material state change, not for stylistic rephrasing.
- Use a soft target of roughly 70 characters without forcibly truncating useful status text.

## Eligibility

1. Use `list_threads` to inspect up to 50 recent threads across the local host and connected remote hosts.
2. Select unarchived threads whose `updatedAt` is within the last two hours.
3. Include threads regardless of `active`, `idle`, or `notLoaded` app status when they satisfy the activity window.
4. Exclude automation-generated run threads. Treat a thread as automation-generated when its preview begins with `Automation:`, its metadata identifies it as an automation run, or it is the run thread for the active-thread naming automation itself.
5. If a connected host is unavailable, continue with available hosts and report the skipped host briefly.

## Per-Thread Workflow

1. Call `read_thread` with the candidate's `threadId` and `hostId`, normally using `turnLimit: 6` and `includeOutputs: false`.
2. Determine the tracker from task metadata, a status-file path, explicit tracker references, or the existing title. Prefer the most authoritative recent evidence.
3. Determine the stable domain from the enduring task objective. If the existing title already follows the three-part contract, preserve its middle segment unless clearly wrong.
4. Determine the current status from the most recent material state, such as planning, awaiting approval, implementing, testing, blocked, ready for review, or completed.
5. Compare semantically with the existing title. Leave it unchanged when the tracker and material state are already represented, even if another wording might sound slightly better.
6. When a change is needed, use `set_thread_title` with the exact thread ID. Do not use `--current` in a batch workflow.

## Output

Return a compact summary containing:

- renamed threads as `old title` -> `new title`;
- eligible threads left unchanged;
- skipped automation threads or unavailable hosts;
- any thread whose tracker or status could not be determined confidently.

Do not rename uncertain threads merely to make every candidate conform.
