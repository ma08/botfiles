---
name: transcribe
description: Transcribe audio/video files using speech-to-text providers. Use when user has audio or video files to transcribe.
---

# Transcribe Skill

Transcribe audio and video files to text using speech-to-text providers (currently Soniox).

## When to Use

- User has audio or video files to transcribe
- User wants to convert meeting recordings, interviews, or media to text
- User needs batch transcription of a directory of files
- User mentions transcription, speech-to-text, or converting audio/video to text

## How to Use

### Single file
```bash
uv run scripts/transcribe.py --input recording.mp4
```

### Directory of files
```bash
uv run scripts/transcribe.py --input /path/to/videos/ --output-dir /path/to/output/
```

### With domain context and terms
```bash
uv run scripts/transcribe.py --input meeting.m4a \
  --context "Board meeting Q4 review" \
  --terms "EBITDA,YoY,ARR,Zone,Simply South"
```

## Arguments Reference

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--input` | `-i` | Audio/video file or directory (required) | -- |
| `--output-dir` | `-o` | Output directory | Same as input |
| `--provider` | `-p` | STT provider (`soniox`) | `soniox` |
| `--context` | `-c` | Free-text context for accuracy | `""` |
| `--terms` | `-t` | Comma-separated domain terms | `""` |
| `--language` | `-l` | Language hint ISO code | `en` |
| `--no-cleanup` | | Keep remote files after transcription | `false` |
| `--no-combined` | | Skip combined transcript for directories | `false` |

## Supported Formats

`.mov`, `.mp4`, `.m4a`, `.mp3`, `.wav`, `.webm`, `.ogg`, `.flac`, `.aac`, `.aiff`, `.amr`, `.asf`

## Output Files

For each input file `example.mp4`:
- `example-transcript.json` - Raw API response with tokens
- `example-transcript.md` - Readable markdown with speaker labels

For multi-file runs (unless `--no-combined`):
- `combined-transcript.md` - All transcripts in one file

## Requirements

- `SONIOX_API_KEY` must be set in the environment or in `~/pro/personal_os/.env`
- Get an API key at https://console.soniox.com

## Typical Workflow

1. User provides audio/video file(s)
2. Run the transcribe script with appropriate context/terms
3. Review the generated markdown transcript
4. Use the transcript for meeting notes, documentation, or content

## Examples in Context

**Meeting recording:**
```bash
uv run scripts/transcribe.py -i ~/Downloads/standup-2026-02-05.m4a \
  -o context/daily/2026-02-05/standup/ \
  --context "Daily standup meeting, Zone team" \
  --terms "Zone,ZonEye,Simply South,Vinoz"
```

**Batch factory tour videos:**
```bash
uv run scripts/transcribe.py -i /path/to/factory-videos/ \
  -o context/daily/2026-02-05/factory-tour/ \
  --context "Factory tour at candy manufacturing facility" \
  --terms "tempering,enrobing,fondant,ganache"
```
