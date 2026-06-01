#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "exa-py",
#   "python-dotenv",
# ]
# ///
"""Run Exa Research API jobs and persist durable artifacts.

Purpose:
- Submit/check/poll Exa Research API jobs.
- Persist raw snapshots and extracted report artifacts.

Inputs:
- EXA_API_KEY in environment, explicit --env-file, nearest .env, or
  ~/pro/botfiles/secrets/local/deep-research.rc
- Prompt text from --prompt or --prompt-file

Outputs (under --outdir):
- exa-submit-*.json
- exa-check-*.json
- exa-research-id.txt
- exa-model-used.txt
- exa-report-<research_id>.md
- exa-sources-<research_id>.md
- exa-cost-dollars.txt when returned by the API
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from exa_py import Exa

DEFAULT_MODEL = "exa-research"
TERMINAL_STATUSES = {"completed", "failed", "cancelled", "canceled", "expired"}


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def find_env_candidates(start: Path) -> list[Path]:
    candidates: list[Path] = []
    for path in [start, *start.parents]:
        env_path = path / ".env"
        if env_path.exists():
            candidates.append(env_path)
    return candidates


def botfiles_secret_candidates(names: list[str]) -> list[Path]:
    roots: list[Path] = []
    botfiles_root = os.getenv("BOTFILES_ROOT", "").strip()
    if botfiles_root:
        roots.append(Path(botfiles_root).expanduser())
    roots.append(Path.home() / "pro/botfiles")

    candidates: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        for name in names:
            candidate = (root / "secrets/local" / name).resolve()
            if candidate not in seen and candidate.exists():
                candidates.append(candidate)
                seen.add(candidate)
    return candidates


def load_env_sources(env_file: Path | None, botfiles_secret_names: list[str]) -> None:
    if env_file and env_file.exists():
        load_dotenv(env_file)
        return

    for candidate in find_env_candidates(Path.cwd().resolve()):
        load_dotenv(candidate)
        break

    for candidate in botfiles_secret_candidates(botfiles_secret_names):
        load_dotenv(candidate)


def load_api_key(env_file: Path | None = None) -> str:
    load_env_sources(env_file, ["deep-research.rc"])

    api_key = os.getenv("EXA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "EXA_API_KEY not found in environment, explicit --env-file, nearest .env, "
            "or ~/pro/botfiles/secrets/local/deep-research.rc"
        )
    return api_key


def to_plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return to_plain(value.model_dump())
    if hasattr(value, "dict"):
        try:
            return to_plain(value.dict())
        except TypeError:
            pass
    if isinstance(value, dict):
        return {str(key): to_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def get_field(value: Any, *names: str) -> Any:
    if isinstance(value, dict):
        for name in names:
            if name in value:
                return value[name]
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return None


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(to_plain(data), indent=2, ensure_ascii=False), encoding="utf-8")


def extract_urls(node: Any, urls: list[str]) -> None:
    if isinstance(node, dict):
        for value in node.values():
            extract_urls(value, urls)
    elif isinstance(node, list):
        for item in node:
            extract_urls(item, urls)
    elif isinstance(node, str):
        urls.extend(re.findall(r"https?://[^\s\"'<>]+", node))


def write_extracted_outputs(outdir: Path, research_id: str, payload: dict[str, Any]) -> None:
    output = payload.get("output") or payload.get("report") or payload.get("text")
    if isinstance(output, str):
        report = output.strip()
    elif output:
        report = "```json\n" + json.dumps(output, indent=2, ensure_ascii=False) + "\n```"
    else:
        report = "(No output extracted from Exa research payload.)"

    safe_id = research_id.replace("/", "_")
    (outdir / f"exa-report-{safe_id}.md").write_text(report + "\n", encoding="utf-8")

    urls: list[str] = []
    extract_urls(payload, urls)
    deduped_urls = list(dict.fromkeys(urls))

    lines = ["# Sources extracted from Exa research", ""]
    if deduped_urls:
        for i, url in enumerate(deduped_urls, start=1):
            lines.append(f"{i}. {url}")
    else:
        lines.append("No URLs extracted.")
    (outdir / f"exa-sources-{safe_id}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    cost = payload.get("cost_dollars") or payload.get("costDollars")
    if cost is not None:
        (outdir / "exa-cost-dollars.txt").write_text(
            json.dumps(cost, ensure_ascii=False) + "\n", encoding="utf-8"
        )


def submit_job(
    client: Exa,
    prompt: str,
    model: str,
    outdir: Path,
    output_schema: dict[str, Any] | None,
) -> str:
    kwargs: dict[str, Any] = {
        "instructions": prompt,
        "model": model,
    }
    if output_schema is not None:
        kwargs["output_schema"] = output_schema

    research = client.research.create(**kwargs)
    data = to_plain(research)
    ts = iso_now()
    save_json(outdir / f"exa-submit-{model}-{ts}.json", data)

    research_id = str(
        get_field(research, "research_id", "researchId", "id")
        or get_field(data, "research_id", "researchId", "id")
        or ""
    ).strip()
    if not research_id:
        raise RuntimeError("Exa Research API did not return a research id")

    (outdir / "exa-research-id.txt").write_text(f"{research_id}\n", encoding="utf-8")
    (outdir / "exa-model-used.txt").write_text(f"{model}\n", encoding="utf-8")
    return research_id


def check_job(client: Exa, research_id: str, outdir: Path) -> tuple[str, dict[str, Any]]:
    result = client.research.get(research_id)
    data = to_plain(result)
    ts = iso_now()
    save_json(outdir / f"exa-check-{research_id}-{ts}.json", data)
    status = str(get_field(result, "status") or data.get("status") or "unknown").lower()
    return status, data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Exa Research API jobs")
    parser.add_argument(
        "--action",
        choices=["submit", "check", "submit_and_check"],
        default="submit_and_check",
    )
    parser.add_argument("--prompt", default="", help="Prompt text")
    parser.add_argument("--prompt-file", type=Path, help="Path to prompt markdown/text file")
    parser.add_argument("--research-id", default="", help="Existing research id to check")
    parser.add_argument(
        "--model",
        choices=["exa-research-fast", "exa-research", "exa-research-pro"],
        default=DEFAULT_MODEL,
    )
    parser.add_argument(
        "--output-schema-file",
        type=Path,
        default=None,
        help="Optional JSON Schema file for structured output",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("."),
        help="Output directory for snapshots and extracted artifacts",
    )
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--timeout-minutes", type=int, default=5)
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional explicit .env or botfiles .rc path",
    )
    return parser.parse_args()


def resolve_prompt(args: argparse.Namespace) -> str:
    prompt_inline = str(args.prompt or "").strip()
    prompt_file = args.prompt_file
    if prompt_inline and prompt_file:
        raise RuntimeError("Use either --prompt or --prompt-file, not both")
    if prompt_file:
        return prompt_file.read_text(encoding="utf-8")
    if prompt_inline:
        return prompt_inline
    raise RuntimeError("Provide --prompt or --prompt-file for submit actions")


def resolve_schema(args: argparse.Namespace) -> dict[str, Any] | None:
    if not args.output_schema_file:
        return None
    return json.loads(args.output_schema_file.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    if args.poll_seconds <= 0:
        raise RuntimeError("--poll-seconds must be > 0")

    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    client = Exa(load_api_key(args.env_file))

    research_id = str(args.research_id or "").strip()
    if args.action in {"submit", "submit_and_check"}:
        prompt = resolve_prompt(args)
        research_id = submit_job(
            client,
            prompt,
            str(args.model),
            outdir,
            resolve_schema(args),
        )
        print(f"submitted research_id={research_id} model={args.model}", flush=True)
        if args.action == "submit":
            return 0

    if not research_id:
        rid_file = outdir / "exa-research-id.txt"
        if rid_file.exists():
            research_id = rid_file.read_text(encoding="utf-8").strip()
    if not research_id:
        raise RuntimeError("No research id provided and outdir/exa-research-id.txt not found")

    if args.action == "check":
        status, payload = check_job(client, research_id, outdir)
        print(f"research_id={research_id} status={status}", flush=True)
        if status in TERMINAL_STATUSES:
            write_extracted_outputs(outdir, research_id, payload)
            return 0 if status == "completed" else 2
        return 0

    start = time.time()
    timeout_seconds = None if args.timeout_minutes <= 0 else args.timeout_minutes * 60

    while True:
        status, payload = check_job(client, research_id, outdir)
        elapsed_seconds = int(time.time() - start)
        print(
            f"research_id={research_id} status={status} elapsed_seconds={elapsed_seconds}",
            flush=True,
        )

        if status in TERMINAL_STATUSES:
            write_extracted_outputs(outdir, research_id, payload)
            print(f"terminal_status={status}", flush=True)
            return 0 if status == "completed" else 2

        if timeout_seconds is not None and elapsed_seconds > timeout_seconds:
            print("timeout reached", file=sys.stderr, flush=True)
            return 3

        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
