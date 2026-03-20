# Task-Status Tracker Contract

This document defines the shared tracker-aware contract for `botfiles` task-status workflows across Codex and Claude.

## Locked Defaults

- `tracker_kind` can be `linear`, `github`, or `none`.
- When both Linear and GitHub references exist, Linear is the primary tracker.
- New logic should prefer the common tracker fields first and treat GitHub-only fields as compatibility data.
- The same tracker-linked task should be consumable from both Codex and Claude task-status flows without field-name drift.

## Task Metadata Block

Task status files keep the human-readable bullet block inside `<!-- TASK-METADATA:START -->` and `<!-- TASK-METADATA:END -->`.
Code should treat the snake_case field names below as canonical, even though the rendered bullets use Title Case labels.

### Common Required Fields

| Canonical field | Rendered label | Notes |
| --- | --- | --- |
| `tracker_kind` | `Tracker Kind` | Primary tracker kind. Prefer `linear` over `github` when both exist. |
| `tracker_url` | `Tracker URL` | Canonical primary tracker URL. |
| `tracker_human_id` | `Tracker Human ID` | Human identifier such as `ZON-8` or `owner/repo#123`. |
| `tracker_title` | `Tracker Title` | Best-effort tracker title. |
| `machine` | `Machine` | `SYSTEM_NAME`, hostname fallback, or `unknown`. |
| `coding_agent` | `Coding Agent` | Usually `codex` or `claude`. |
| `agent_session_id` | `Agent Session ID` | Session identifier for the active run. |
| `task_folder` | `Task Folder` | Absolute path to the local task folder. |
| `task_status_path` | `Task Status Path` | Absolute path to `status.md` or legacy `README.md`. |
| `transcript_path` | `Transcript Path` | Absolute transcript path when the agent can resolve one. |
| `last_synced_at` | `Last Synced` | PST timestamp for the last metadata sync. |

### Common Optional Fields

| Canonical field | Rendered label | Notes |
| --- | --- | --- |
| `workspace_path` | `Workspace Path` | Absolute project/workspace root associated with the task. |
| `zellij_session` | `Zellij Session` | Session name or `none`. |
| `zellij_link` | `Zellij Link` | Browser link or `none`. |
| `remote_session_anchor_kind` | `Remote Session Anchor Kind` | Intended remote publication surface, such as `linear_issue_body` or `github_issue_body`. |
| `remote_session_anchor_id` | `Remote Session Anchor ID` | Managed anchor identifier. Default `LIVE-SESSION` when a remote anchor exists. |

### Compatibility Fields

GitHub compatibility fields stay present during migration:

| Canonical field | Rendered label |
| --- | --- |
| `github_issue` | `GitHub Issue` |
| `github_repo` | `GitHub Repo` |
| `github_issue_number` | `GitHub Issue Number` |

Linear-specific fields are written when the tracker is Linear or when the caller provides them:

| Canonical field | Rendered label |
| --- | --- |
| `linear_issue_id` | `Linear Issue ID` |
| `linear_issue_identifier` | `Linear Issue Identifier` |
| `linear_team_id` | `Linear Team ID` |
| `linear_team_name` | `Linear Team Name` |
| `linear_project_id` | `Linear Project ID` |
| `linear_project_name` | `Linear Project Name` |

## Managed Remote Live-Session Block

The managed remote block uses the existing markers:

```markdown
<!-- LIVE-SESSION:START -->
...
<!-- LIVE-SESSION:END -->
```

Rules:

- For Linear, the managed block belongs at the top of the ticket body.
- For GitHub, the same markers remain the compatibility pattern for issue-body sync.
- Updates must replace only the managed block.
- Content below the managed block must be preserved.
- The managed block owns the canonical tracker-facing live-session payload for the active run.

## Current Implementation Boundary

- `sync_task_metadata.py` writes the shared tracker-aware metadata block locally.
- `resolve_task_context.py`, `get_task_details.py`, and `utils/notify_utils.py` prefer the common tracker fields.
- `--sync-github-issue` remains the compatibility flag that triggers managed remote live-session publication on the primary tracker.
- For GitHub trackers, the managed block is written to the issue body via `gh`.
- For Linear trackers, the managed block is written to the issue description via `LINEAR_API_KEY`.
