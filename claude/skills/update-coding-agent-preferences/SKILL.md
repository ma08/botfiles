---
name: update-coding-agent-preferences
description: Apply persistent or repo-local coding-agent instruction changes across Codex, Claude, and Antigravity in tandem, including related skill updates when a preference changes a skill's behavior or workflow. Use when the user asks to add, revise, or remove preferences in `AGENTS.md`, `CLAUDE.md`, Antigravity `rules/`, or matching skill files and the change must be classified as global botfiles policy, project-local policy, or skill-specific guidance.
---

# Update Coding Agent Preferences

Update the right instruction files together instead of patching one harness and leaving drift behind. Determine scope first, edit the minimum set of files, then sync and validate the resulting Codex, Claude, and Antigravity copies.

## Scope Decision

1. Read the requested preference carefully.
2. Classify the change before editing:
   - Global persistent preference: update `~/pro/botfiles/codex/AGENTS.md`, `~/pro/botfiles/claude/CLAUDE.md`, and `~/pro/botfiles/antigravity/AGENTS.md` (or the relevant modular rule under `~/pro/botfiles/antigravity/rules/`). Keep every single Antigravity rule file strictly under 24,000 bytes so it is never truncated.
   - Project-local preference: update the current repo's `AGENTS.md` and `CLAUDE.md` (plus `.agents/rules/` if present) when they exist. If only one exists, update the existing file and note the asymmetry.
   - Skill-specific behavior: update the matching skill directory in addition to any instruction file that defines the policy.
   - Task-only or temporary preference: keep it out of long-lived instruction files unless the user explicitly asks otherwise.
3. If the preference affects both written policy and a skill workflow, update both.
4. If scope is ambiguous, inspect the user's wording and repo context before asking. Ask only when mis-scoping would create durable drift.

## File Targets

Use these defaults unless the repo has an explicit local override.

- Global Codex instructions: `~/pro/botfiles/codex/AGENTS.md`
- Global Claude instructions: `~/pro/botfiles/claude/CLAUDE.md`
- Global Antigravity core instructions (always on, <24 KB): `~/pro/botfiles/antigravity/AGENTS.md`
- Global Antigravity modular rules (`model_decision`, each <24 KB): `~/pro/botfiles/antigravity/rules/*.md`
- Global canonical skills (Codex + Antigravity via `antigravity/skills.json`): `~/pro/botfiles/codex/skills/<skill-name>/`
- Global Claude skills mirror: `~/pro/botfiles/claude/skills/<skill-name>/`
- Global Antigravity skill exclusions: `~/pro/botfiles/antigravity/skills.json`
- Project instructions: `<repo>/AGENTS.md` and `<repo>/CLAUDE.md` (plus `<repo>/.agents/rules/` when used)
- Project skills: `<repo>/.codex/skills/<skill-name>/`, `<repo>/.claude/skills/<skill-name>/`, or `<repo>/.agents/skills/<skill-name>/` (preserve the repo's established layout)

Do not edit machine-managed system skills under `~/.codex/skills/.system/` unless the user explicitly asks for a machine-local change rather than a source-controlled botfiles change.
The visible botfiles trees exist because `setup.sh` symlinks the user-level global skill directories into source-controlled `~/pro/botfiles/codex/skills` and `~/pro/botfiles/claude/skills` (and exposes `codex/skills` to Antigravity via `~/.gemini/config/botfiles-skills` + `skills.json`) for visibility and shared management. Do not generalize `codex/skills` and `claude/skills` as the normal project-local convention.

## Edit Workflow

1. Locate the existing rule or the nearest relevant section before adding new text.
2. Prefer extending or tightening an existing policy instead of creating a duplicate rule elsewhere.
3. Write Codex, Claude, and Antigravity instructions as semantic counterparts. Preserve each file's local voice, modularity, and byte limits instead of forcing literal line-for-line copies.
4. If a skill changes:
   - Determine whether the target is a global botfiles skill or a project-local skill.
   - Edit the canonical copy first in `codex/skills/` (or the repo's established skill root). Because Antigravity loads `codex/skills` through `antigravity/skills.json`, editing `codex/skills` updates Codex and Antigravity together; check `antigravity/skills.json` only if exclusions should change.
   - Preserve the repo's documented or already-established local skill layout. Do not create a second skill root just because another layout is more common.
   - For ordinary project-local skills, default to `.agents/skills`, `.codex/skills`, and `.claude/skills` as already established in that repo.
   - If a repo intentionally documents or already uses visible `codex/skills` and `claude/skills`, preserve that layout instead of creating hidden roots beside it.
   - Mirror to Claude with the sync workflow when a counterpart already exists, or when the user explicitly wants a new mirror. One-sided skills are valid; do not create a brand-new counterpart by default.
   - Re-read the Claude copy after sync.
5. Keep the change localized. Do not touch unrelated instructions, generated assets, or curated upstream skills unless the preference explicitly requires it.

## Sync Skill Copies

For source-controlled skills in botfiles, prefer the sync script after editing the canonical `codex/skills` copy.

```bash
python ~/pro/botfiles/codex/skills/sync-agent-skills/scripts/sync_skills.py \
  --repo-root ~/pro/botfiles sync --from-side codex --to-side claude \
  --skills <skill-name>
```

Run the sync as a dry-run first. Add `--apply` only after confirming the plan.

For project-local skills, run the same sync against the repo root. The normal project-local layout is hidden `.codex/skills` and `.claude/skills`:

```bash
python ~/pro/botfiles/codex/skills/sync-agent-skills/scripts/sync_skills.py \
  --repo-root <repo> sync --from-side codex --to-side claude \
  --skills <skill-name>
```

The sync script can also operate on botfiles-style visible roots when a repo intentionally uses that exception, but do not create or describe `codex/skills` and `claude/skills` as the default project-local layout.
Preserve the repo's documented layout before applying this default.

If the skill is an intentional local fork or the Claude copy must differ, skip sync and edit both copies manually. State that exception in the final handoff.

## Validation

- Re-read all edited instruction files and confirm the preference lands in equivalent places.
- Verify every edited file in `~/pro/botfiles/antigravity/AGENTS.md` and `~/pro/botfiles/antigravity/rules/*.md` is strictly under 24,000 bytes (`wc -c`) and that rule files under `rules/` have valid YAML frontmatter (`trigger` and `description`).
- For any new or edited skill, run:
  `python ~/pro/botfiles/codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>`
- If a skill was synced, validate the Claude copy too when feasible.
- Summarize the scope classification, files changed, and any intentional asymmetry.

## Common Patterns

- "Make this a standing rule everywhere": update the global instruction set (Codex, Claude, and Antigravity).
- "Only in this repo": update the project instruction files.
- "Change how a global skill behaves": update the existing global skill surface (plus Claude mirror if present), and any instruction files that define the policy.
- "Change how a project-local skill behaves": update the repo-local skill surface in the repo's documented layout, plus any local instruction files that define the policy.
- "Temporary for this task": use task notes or status files instead of long-lived instruction docs.

## Edge Cases

- If the repo has only `AGENTS.md` or only `CLAUDE.md`, update the existing file and note that the counterpart is missing.
- If a global or project-local skill exists on only one side, update the existing side and note the missing counterpart unless the user explicitly wants you to create a new mirrored skill.
- If you see visible `codex/skills` or `claude/skills` in a non-botfiles repo, verify whether that repo is intentionally using a symlink-backed or otherwise exceptional layout before editing it as if it were project-local.
- If the request conflicts with a curated or upstream-managed skill, keep the preference in instruction files unless the user explicitly asks for a protected fork.
- If a preference originated in one ecosystem but changes cross-agent behavior, update Codex, Claude, and Antigravity counterparts so the rule does not drift.
