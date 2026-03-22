---
name: update-coding-agent-preferences
description: Apply persistent or repo-local coding-agent instruction changes across Codex and Claude in tandem, including related skill updates when a preference changes a skill's behavior or workflow. Use when the user asks to add, revise, or remove preferences in `AGENTS.md`, `CLAUDE.md`, or matching skill files and the change must be classified as global botfiles policy, project-local policy, or skill-specific guidance.
---

# Update Coding Agent Preferences

Update the right instruction files together instead of patching one side and leaving drift behind. Determine scope first, edit the minimum set of files, then sync and validate the resulting Codex and Claude copies.

## Scope Decision

1. Read the requested preference carefully.
2. Classify the change before editing:
   - Global persistent preference: update `~/pro/botfiles/codex/AGENTS.md` and `~/pro/botfiles/claude/CLAUDE.md`.
   - Project-local preference: update the current repo's `AGENTS.md` and `CLAUDE.md` when both exist. If only one exists, update the existing file and note the asymmetry.
   - Skill-specific behavior: update the matching skill directory in addition to any instruction file that defines the policy.
   - Task-only or temporary preference: keep it out of long-lived instruction files unless the user explicitly asks otherwise.
3. If the preference affects both written policy and a skill workflow, update both.
4. If scope is ambiguous, inspect the user's wording and repo context before asking. Ask only when mis-scoping would create durable drift.

## File Targets

Use these defaults unless the repo has an explicit local override.

- Global Codex instructions: `~/pro/botfiles/codex/AGENTS.md`
- Global Claude instructions: `~/pro/botfiles/claude/CLAUDE.md`
- Global Codex skills: `~/pro/botfiles/codex/skills/<skill-name>/`
- Global Claude skills: `~/pro/botfiles/claude/skills/<skill-name>/`
- Project Codex instructions: `<repo>/AGENTS.md`
- Project Claude instructions: `<repo>/CLAUDE.md`
- Project Codex skills: `<repo>/.codex/skills/<skill-name>/`
- Project Claude skills: `<repo>/.claude/skills/<skill-name>/`

Do not edit machine-managed system skills under `~/.codex/skills/.system/` unless the user explicitly asks for a machine-local change rather than a source-controlled botfiles change.
The visible botfiles trees exist because `setup.sh` symlinks the user-level global skill directories into source-controlled `~/pro/botfiles/codex/skills` and `~/pro/botfiles/claude/skills` for visibility and shared management. Do not generalize `codex/skills` and `claude/skills` as the normal project-local convention.

## Edit Workflow

1. Locate the existing rule or the nearest relevant section before adding new text.
2. Prefer extending or tightening an existing policy instead of creating a duplicate rule elsewhere.
3. Write Codex and Claude instructions as semantic counterparts. Preserve each file's local voice and structure instead of forcing literal line-for-line copies.
4. If a skill changes:
   - Determine whether the target is a global botfiles skill or a project-local skill.
   - Edit the Codex copy first in the matching skill root.
   - Preserve the repo's documented or already-established local skill layout. Do not create a second skill root just because another layout is more common.
   - For ordinary project-local skills, default to `.codex/skills` and `.claude/skills`.
   - If a repo intentionally documents or already uses visible `codex/skills` and `claude/skills`, preserve that layout instead of creating hidden roots beside it.
   - Mirror to Claude with the sync workflow when a counterpart already exists, or when the user explicitly wants a new mirror. One-sided skills are valid; do not create a brand-new counterpart by default.
   - Re-read the Claude copy after sync
5. Keep the change localized. Do not touch unrelated instructions, generated assets, or curated upstream skills unless the preference explicitly requires it.

## Sync Skill Copies

For source-controlled skills in botfiles, prefer the sync script after editing the Codex copy.

```bash
python ~/pro/botfiles/codex/skills/sync-codex-claude-skills/scripts/sync_skills.py \
  --repo-root ~/pro/botfiles sync --from-side codex --to-side claude \
  --skills <skill-name>
```

Run the sync as a dry-run first. Add `--apply` only after confirming the plan.

For project-local skills, run the same sync against the repo root. The normal project-local layout is hidden `.codex/skills` and `.claude/skills`:

```bash
python ~/pro/botfiles/codex/skills/sync-codex-claude-skills/scripts/sync_skills.py \
  --repo-root <repo> sync --from-side codex --to-side claude \
  --skills <skill-name>
```

The sync script can also operate on botfiles-style visible roots when a repo intentionally uses that exception, but do not create or describe `codex/skills` and `claude/skills` as the default project-local layout.
Preserve the repo's documented layout before applying this default.

If the skill is an intentional local fork or the Claude copy must differ, skip sync and edit both copies manually. State that exception in the final handoff.

## Validation

- Re-read both instruction files or both skill copies and confirm the preference lands in equivalent places.
- For any new or edited Codex skill, run:
  `python ~/pro/botfiles/codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>`
- If a skill was synced, validate the Claude copy too when feasible.
- Summarize the scope classification, files changed, and any intentional asymmetry.

## Common Patterns

- "Make this a standing rule everywhere": update the global instruction pair.
- "Only in this repo": update the project instruction pair.
- "Change how a global skill behaves": update the existing global skill surface, plus any instruction file that defines the policy. Create a new mirror only if the counterpart already exists or the user explicitly wants one.
- "Change how a project-local skill behaves": update the repo-local skill surface in the repo's documented layout, plus any local instruction file that defines the policy. Create a new mirror only if the counterpart already exists or the user explicitly wants one.
- "Temporary for this task": use task notes or status files instead of long-lived instruction docs.

## Edge Cases

- If the repo has only `AGENTS.md` or only `CLAUDE.md`, update the existing file and note that the counterpart is missing.
- If a global or project-local skill exists on only one side, update the existing side and note the missing counterpart unless the user explicitly wants you to create a new mirrored skill.
- If you see visible `codex/skills` or `claude/skills` in a non-botfiles repo, verify whether that repo is intentionally using a symlink-backed or otherwise exceptional layout before editing it as if it were project-local.
- If the request conflicts with a curated or upstream-managed skill, keep the preference in instruction files unless the user explicitly asks for a protected fork.
- If a preference originated in one ecosystem but changes cross-agent behavior, update both Codex and Claude counterparts so the rule does not drift.
