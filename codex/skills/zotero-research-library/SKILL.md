---
name: zotero-research-library
description: >-
  Work with a Zotero research library for paper-reading workflows: search local items,
  inspect metadata, read attached PDFs, export notes/highlights/annotations, summarize a
  user's reading state, create child notes via Zotero Web API when explicitly requested,
  and troubleshoot Zotero Connector/API issues. Use when the user asks Codex to interact
  with Zotero, read Zotero annotations, make reading digests, manage paper
  notes/tags/attachments, or investigate whether agent-assisted Zotero edits are possible.
---

# Zotero Research Library

## Operating Rules

- Prefer read-only local access first. Use Zotero Local API if enabled, or open `zotero.sqlite` with `mode=ro&immutable=1`.
- Never write directly to `zotero.sqlite` while Zotero is running. Treat direct SQLite writes as a last-resort experiment requiring explicit user approval, a backup, and Zotero closed.
- For edits, prefer official Zotero Web API writes with an API key. Local API is currently GET-only.
- For native PDF highlights/annotations, prefer Zotero UI or a Zotero-side bridge/plugin/MCP. Do not promise reliable native annotation creation via local API or SQLite alone.
- Preserve provenance: include Zotero item key, itemID, attachment key, page labels, colors, comments, DOI/URL, and local attachment path in digests.

## Tool Selection

Use this skill as the default for lightweight paper-reading work:

- inspect papers already in Zotero
- export notes/highlights/annotations into a digest
- answer questions about the user's reading state
- create a child note only after an explicit write request

Reach for a community tool instead when the request exceeds this skill's scope:

- `54yyyu/zotero-mcp`: best broad MCP choice for semantic search, full-text indexing, native annotation access, DOI import, collections, and hybrid local-read/web-write workflows.
- `cli-anything-zotero`: strongest local-write option when a Zotero JS Bridge plugin is acceptable and the user wants local write operations without a Zotero Web API key.
- `llm-for-zotero`: best in-reader experience when the user wants LLM help inside Zotero while reading PDFs.
- `WenyuChiou/zotero-skills` or `c0mm4nd/zotero-skills`: better than this skill for full Web API CRUD over items, notes, collections, tags, and attachments.
- `drguptavivek/zotero-use`: useful for writing workflows that involve Zotero references and Word `.docx` citation fields.
- `ketthub/zotero-skill`: useful as a minimal read-only search implementation; this skill already covers a similar local-read niche but with annotation digest support.

## Quick Start

Use the bundled read-only helper for local inspection:

```bash
python3 "$CODEX_HOME/skills/zotero-research-library/scripts/zotero_read.py" --db "$HOME/Zotero/zotero.sqlite" search "SABER"
python3 "$CODEX_HOME/skills/zotero-research-library/scripts/zotero_read.py" --db "$HOME/Zotero/zotero.sqlite" digest --item-key ITEMKEY --output reading-digest.md
```

On a remote Mac, run through SSH:

```bash
ssh sourya-mac 'python3 /path/to/zotero_read.py --db "$HOME/Zotero/zotero.sqlite" digest --item-key ITEMKEY'
```

Use the Web API note helper only when the user explicitly wants a Zotero note written:

```bash
ZOTERO_API_KEY=... ZOTERO_USER_ID=... \
python3 "$CODEX_HOME/skills/zotero-research-library/scripts/zotero_web_note.py" \
  --parent ITEMKEY --title "Codex reading synthesis" --markdown notes.md
```

Dry-run is the default. Add `--execute` only after confirming the target item and note body.

## Common Workflows

### Inspect a paper the user is reading

1. Search by title/DOI/arXiv ID with `zotero_read.py search`.
2. Identify the clean parent item, not stale webpage or troubleshooting items.
3. Run `zotero_read.py digest --item-key ...`.
4. Read the digest plus, if needed, extract the attached PDF text with the `pdf` skill.
5. Summarize the user's highlights and answer their margin questions.

### Create a reading digest

Include:

- metadata: title, creators, year, DOI, URL, item key
- child notes
- attachments and local paths
- annotation count by color
- annotations ordered by attachment sort/page order
- comments separately from selected text
- an interpretation section only after raw evidence is captured

### Add or update notes

- Use Zotero Web API writes with a key that has write access.
- Prefer creating a new child note over editing an existing note unless the user asks to modify a specific note.
- Use `--dry-run` first and show the target parent key/title.
- Remind the user that Zotero desktop may need sync before Web API changes appear locally.

### Annotation/highlight edits

- Reading existing annotations is safe via local DB/Local API/Web API.
- Creating native PDF annotations is not reliably supported by Zotero Local API alone. Web API exposes annotations as child items, but local GET-only API cannot create them, and direct DB insertion may not appear in the reader due to runtime/cache internals.
- If native annotation creation is important, consider installing a Zotero MCP/plugin/JS bridge. See `references/web-findings.md`.
- A safe alternative is to create a child note with quoted passages and page labels, then ask the user to apply highlights manually in Zotero.

## Resources

- `scripts/zotero_read.py`: read-only local SQLite search/detail/digest exporter.
- `scripts/zotero_web_note.py`: explicit Web API child-note creation helper with dry-run default.
- `references/web-findings.md`: current API/MCP findings and constraints.
