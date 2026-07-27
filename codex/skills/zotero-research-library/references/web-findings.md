# Zotero Agent Access Findings

## Official APIs

- Zotero Local API runs at `http://localhost:23119/api/` when enabled in Zotero Settings -> Advanced. It is local, fast, and read-only: official docs say only `GET` is accepted and write requests are unsupported for now.
- Zotero Web API v3 supports write requests with an API key that has write access. Use it for creating child notes, changing tags/metadata, or importing items.
- Zotero annotations are represented as child items of PDF attachments with `itemType=annotation` in the synced data model, but local write support is absent and native annotation creation remains fragile outside Zotero/plugin contexts.

Primary references:

- https://www.zotero.org/support/dev/web_api/v3/local_api
- https://www.zotero.org/support/dev/web_api/v3/basics
- https://www.zotero.org/support/dev/web_api/v3/write_requests
- https://forums.zotero.org/discussion/105207/access-pdf-annotations-via-zotero-web-api

## Existing Projects To Consider

- `54yyyu/zotero-mcp`: broad MCP server for local/web Zotero access; advertises annotation extraction/search and note/annotation write operations, plus hybrid local reads and web writes.
- `WenyuChiou/zotero-skills`: AI-assistant skill using dual local-read + web-write architecture for Zotero CRUD.
- `PiaoyangGuohai1/cli-anything-zotero`: CLI/MCP with many commands, including item annotations, PDF attachment, tags/collections, arbitrary Zotero JavaScript, and a JS Bridge plugin path.
- `Renaaa1a/Zotero-Paper-Notes`: focused Codex skill for creating structured child notes under Zotero items.
- `drguptavivek/zotero-use`: agent skill for searching/retrieving Zotero references, reviewing PDFs, brainstorming from Zotero evidence, and working with Word documents containing Zotero citations.
- `c0mm4nd/zotero-skills`: Web API CRUD skills plus Better BibTeX JSON-RPC workflows.
- `Kt-L/zotero-skill`: small local-library search skill with one Python file and no server dependency.
- `yilewang/llm-for-zotero`: Zotero plugin that brings LLM assistance into the Zotero reader and advertises Codex/Claude Code bridge support.
- `MuiseDestiny/zotero-gpt`: mature Zotero GPT plugin for reader-side LLM workflows.

Project links:

- https://github.com/54yyyu/zotero-mcp
- https://github.com/WenyuChiou/zotero-skills/
- https://github.com/PiaoyangGuohai1/cli-anything-zotero/blob/main/cli_anything/zotero/skills/SKILL.md
- https://github.com/Renaaa1a/Zotero-Paper-Notes
- https://github.com/drguptavivek/zotero-use
- https://github.com/c0mm4nd/zotero-skills
- https://github.com/Kt-L/zotero-skill
- https://github.com/yilewang/llm-for-zotero
- https://github.com/MuiseDestiny/zotero-gpt

## Practical Policy

- Current recommendation: keep this local skill as the default paper-reading harness, because it is simple, read-only-first, tested against the user's SABER item, and tuned for digests. Do not pretend it replaces community tools.
- Install or invoke `54yyyu/zotero-mcp` when semantic search, collection-wide full-text search, DOI imports, duplicate handling, or richer MCP tool access matters.
- Install or invoke `cli-anything-zotero` when local write operations or native Zotero JavaScript access matters and the user accepts installing a Zotero JS Bridge plugin.
- Install `llm-for-zotero` when the target workflow is interactive in-reader assistance rather than Codex-side library inspection.
- For reliable read workflows, use local DB/API.
- For reliable write workflows, use Web API notes/tags/metadata and let Zotero sync.
- For native PDF highlight/annotation creation, install/use a Zotero-side plugin/MCP/JS bridge rather than direct DB insertion.
- If the user asks for automatic highlights, propose creating a child note with page-labeled suggested highlights unless a trusted annotation-writing bridge is installed.
