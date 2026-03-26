---
name: gws-drive
description: "Google Drive: List, search, inspect, download, and export files with alias-first `gws-account` flows for `work`, `personal`, and `columbia`."
metadata:
  openclaw:
    category: "productivity"
    requires:
      bins:
        - gws
    cliHelp: "gws drive --help"
---

# drive (v3)

> **PREREQUISITE:** Read `../gws-shared/SKILL.md` for auth, alias selection, global flags, and security rules. If missing, run `gws generate-skills` to create it.

Use this skill when the user wants read-only Google Drive access from a specific saved account on this machine. Prefer `gws-account <alias> ...` over bare `gws ...`.

## Common Read Flows

### List recent files

```bash
gws-account work drive files list --params '{"pageSize": 10, "orderBy": "modifiedTime desc", "q": "trashed=false"}' --format json
```

### Search by title or MIME type

```bash
gws-account personal drive files list --params "{\"pageSize\": 10, \"q\": \"name contains 'tax' and trashed=false\"}" --format json
gws-account columbia drive files list --params "{\"pageSize\": 10, \"q\": \"mimeType='application/vnd.google-apps.document' and trashed=false\"}" --format json
```

### Inspect one file's metadata

```bash
gws-account work drive files get --params '{"fileId": "<FILE_ID>", "fields": "id,name,mimeType,owners,webViewLink"}' --format json
```

### Download or export content

```bash
gws-account personal drive files download --params '{"fileId": "<FILE_ID>"}' -o ./downloaded-file.bin
gws-account columbia drive files export --params '{"fileId": "<FILE_ID>", "mimeType": "text/plain"}' -o ./exported-doc.txt
```

Use `download` for uploaded/binary files and `export` for native Google Docs, Sheets, or Slides files.

## Shared Drives

For shared drives, set both `supportsAllDrives` and `includeItemsFromAllDrives`. Narrow to one shared drive with `corpora=drive` plus `driveId`:

```bash
gws-account work drive files list --params '{"corpora": "drive", "driveId": "<DRIVE_ID>", "includeItemsFromAllDrives": true, "supportsAllDrives": true, "pageSize": 10, "q": "trashed=false"}' --format json
gws-account work drive drives list --format json
```

## Discovering Commands

Before calling an unfamiliar method, inspect it:

```bash
gws-account work drive --help
gws-account work drive files --help
gws-account work schema drive.files.list
```

Use `gws-account <alias> schema drive.<resource>.<method>` to inspect parameters, supported scopes, and response structure before building a command.

## Notes

- Prefer read-only methods such as `files.list`, `files.get`, `files.download`, `files.export`, and `drives.list` unless the user explicitly asks for write access.
- Add `fields` when you only need specific metadata so responses stay small and readable.
- Never dump file contents by default if the document is likely to contain sensitive personal, academic, or company material.
