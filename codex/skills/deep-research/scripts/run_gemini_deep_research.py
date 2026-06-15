#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "python-dotenv",
#   "requests",
# ]
# ///
"""Run Gemini Deep Research jobs through the Interactions API.

Purpose:
- Submit/check/poll Gemini Deep Research jobs.
- Persist raw snapshots and extracted report artifacts.

Inputs:
- GEMINI_API_KEY (or GOOGLE_API_KEY) in environment, explicit --env-file,
  nearest .env, or ~/pro/botfiles/secrets/local/deep-research.rc
- Prompt text from --prompt or --prompt-file

Outputs (under --outdir):
- gemini-submit-*.json
- gemini-check-*.json
- gemini-interaction-id.txt
- gemini-agent-used.txt
- gemini-report-<interaction_id>.md
- gemini-sources-<interaction_id>.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_AGENT = "deep-research-max-preview-04-2026"
DEFAULT_API_REVISION = "2026-05-20"
TERMINAL_STATUSES = {"completed", "failed", "cancelled", "expired"}


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

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found in environment, explicit --env-file, nearest "
            ".env, or ~/pro/botfiles/secrets/local/deep-research.rc"
        )
    return api_key


def build_headers(api_key: str, api_revision: str) -> dict[str, str]:
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    if api_revision:
        headers["Api-Revision"] = api_revision
    return headers


def post_interaction(
    api_key: str, payload: dict[str, Any], api_revision: str
) -> requests.Response:
    return requests.post(
        f"{API_BASE}/interactions",
        headers=build_headers(api_key, api_revision),
        data=json.dumps(payload),
        timeout=180,
    )


def get_interaction(
    api_key: str, interaction_id: str, api_revision: str
) -> requests.Response:
    return requests.get(
        f"{API_BASE}/interactions/{interaction_id}",
        headers=build_headers(api_key, api_revision),
        timeout=180,
    )


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_status(raw_status: Any) -> str:
    if not isinstance(raw_status, str):
        return "unknown"
    status = raw_status.strip().lower()
    mapping = {
        "succeeded": "completed",
        "success": "completed",
        "done": "completed",
        "completed": "completed",
        "running": "in_progress",
        "queued": "in_progress",
        "pending": "in_progress",
        "processing": "in_progress",
        "in progress": "in_progress",
        "in_progress": "in_progress",
        "failed": "failed",
        "error": "failed",
        "cancelled": "cancelled",
        "canceled": "cancelled",
        "expired": "expired",
    }
    return mapping.get(status, status or "unknown")


def collect_text_and_urls(
    node: Any,
    texts: list[str],
    urls: list[str],
    *,
    include_any_text: bool = False,
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            key_lower = str(key).lower()

            if isinstance(value, str):
                if key_lower in {"url", "uri", "target", "link"} and value.startswith("http"):
                    urls.append(value)

                if key_lower in {"text", "output_text"} and value.strip():
                    texts.append(value.strip())
                elif include_any_text and value.strip() and key_lower in {
                    "summary",
                    "content",
                    "message",
                }:
                    texts.append(value.strip())

            if isinstance(value, (dict, list)):
                collect_text_and_urls(
                    value, texts, urls, include_any_text=include_any_text
                )

    elif isinstance(node, list):
        for item in node:
            collect_text_and_urls(item, texts, urls, include_any_text=include_any_text)


def model_generated_steps(steps: Any) -> list[Any]:
    """Return non-user steps for progress diagnostics."""
    if not isinstance(steps, list):
        return []
    return [
        step
        for step in steps
        if not (
            isinstance(step, dict)
            and str(step.get("type", "")).lower() == "user_input"
        )
    ]


def final_output_steps(steps: Any) -> list[Any]:
    """Return final answer steps suitable for report extraction."""
    if not isinstance(steps, list):
        return []
    return [
        step
        for step in steps
        if isinstance(step, dict)
        and str(step.get("type", "")).lower() in {"model_output", "assistant_output"}
    ]


def extract_text_and_urls(payload: dict[str, Any]) -> tuple[str, list[str]]:
    texts: list[str] = []
    urls: list[str] = []

    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        texts.append(output_text.strip())

    steps = payload.get("steps")
    if isinstance(steps, list):
        collect_text_and_urls(
            final_output_steps(steps), texts, urls, include_any_text=True
        )

    outputs = payload.get("outputs")
    if isinstance(outputs, list):
        collect_text_and_urls(outputs, texts, urls, include_any_text=True)

    if not texts:
        collect_text_and_urls(payload.get("response", {}), texts, urls, include_any_text=True)

    if not urls and (isinstance(steps, list) or isinstance(outputs, list)):
        url_source = final_output_steps(steps) if isinstance(steps, list) else outputs
        blob = json.dumps(url_source, ensure_ascii=False)
        urls.extend(re.findall(r"https?://[^\s\"'<>]+", blob))

    deduped_texts: list[str] = []
    seen_texts: set[str] = set()
    for text in texts:
        normalized = re.sub(r"\s+", " ", text.strip())
        if normalized and normalized not in seen_texts:
            seen_texts.add(normalized)
            deduped_texts.append(text.strip())

    deduped_urls: list[str] = []
    seen_urls: set[str] = set()
    for url in urls:
        clean_url = url.strip()
        if clean_url and clean_url not in seen_urls:
            seen_urls.add(clean_url)
            deduped_urls.append(clean_url)

    merged_text = "\n\n".join(chunk for chunk in deduped_texts if chunk)
    return merged_text, deduped_urls


def has_model_generated_output(payload: dict[str, Any]) -> bool:
    text, urls = extract_text_and_urls(payload)
    if text.strip() or urls:
        return True
    steps = model_generated_steps(payload.get("steps"))
    return bool(payload.get("outputs") or payload.get("response") or steps)


def deep_research_agent_config(
    *,
    enabled: bool,
    thinking_summaries: str,
    visualization: str,
    collaborative_planning: bool,
) -> dict[str, Any] | None:
    if not enabled:
        return None

    config: dict[str, Any] = {
        "type": "deep-research",
        "thinking_summaries": thinking_summaries,
        "collaborative_planning": collaborative_planning,
    }
    if visualization:
        config["visualization"] = visualization
    return config


def submit_job(
    api_key: str,
    prompt: str,
    agent: str,
    outdir: Path,
    background: bool,
    store: bool,
    api_revision: str,
    agent_config: dict[str, Any] | None,
) -> str:
    payload = {
        "input": prompt,
        "agent": agent,
        "background": background,
        "store": store,
    }
    if agent_config:
        payload["agent_config"] = agent_config
    ts = iso_now()
    save_json(outdir / f"gemini-submit-request-{agent}-{ts}.json", payload)
    response = post_interaction(api_key, payload, api_revision)
    snapshot = outdir / f"gemini-submit-{agent}-{ts}.json"

    try:
        data = response.json()
    except Exception:
        data = {"raw_text": response.text, "status_code": response.status_code}
    save_json(snapshot, data)

    if response.status_code < 300 and isinstance(data, dict):
        interaction_id = str(data.get("id") or data.get("name") or "").strip()
        if interaction_id:
            (outdir / "gemini-interaction-id.txt").write_text(
                f"{interaction_id}\n", encoding="utf-8"
            )
            (outdir / "gemini-agent-used.txt").write_text(
                f"{agent}\n", encoding="utf-8"
            )
            return interaction_id

    raise RuntimeError(
        "Unable to submit Gemini deep research request. "
        f"status={response.status_code} body={json.dumps(data, ensure_ascii=False)[:1200]}"
    )


def check_job(
    api_key: str, interaction_id: str, outdir: Path, api_revision: str
) -> tuple[str, dict[str, Any]]:
    response = get_interaction(api_key, interaction_id, api_revision)
    response.raise_for_status()
    data = response.json()
    ts = iso_now()
    save_json(outdir / f"gemini-check-{interaction_id.replace('/', '_')}-{ts}.json", data)

    status = normalize_status(data.get("state") or data.get("status"))
    if status == "unknown" and data.get("done") is True:
        status = "completed"
    if status == "unknown" and isinstance(data.get("error"), dict):
        status = "failed"
    return status, data


def payload_progress_fingerprint(payload: dict[str, Any]) -> str:
    progress_shape = {
        "status": payload.get("status") or payload.get("state"),
        "error": payload.get("error"),
        "output_text": payload.get("output_text"),
        "steps": payload.get("steps"),
        "outputs": payload.get("outputs"),
        "response": payload.get("response"),
    }
    blob = json.dumps(progress_shape, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def classify_incomplete_payload(status: str, payload: dict[str, Any]) -> str:
    has_output = has_model_generated_output(payload)
    if status == "in_progress" and not has_output:
        return "provider_stalled_or_long_running_no_output"
    if status == "unknown":
        return "unknown_status_payload"
    return "non_terminal"


def write_timeout_summary(
    outdir: Path,
    interaction_id: str,
    status: str,
    payload: dict[str, Any],
    *,
    elapsed_seconds: int,
    attempt: int,
    stable_polls: int,
) -> None:
    safe_id = interaction_id.replace("/", "_")
    path = outdir / f"gemini-timeout-summary-{safe_id}.md"
    classification = classify_incomplete_payload(status, payload)
    keys = ", ".join(sorted(str(key) for key in payload.keys())) or "(none)"
    lines = [
        "# Gemini Timeout Summary",
        "",
        f"- Interaction ID: `{interaction_id}`",
        f"- Status: `{status}`",
        f"- Classification: `{classification}`",
        f"- Attempt: {attempt}",
        f"- Elapsed seconds: {elapsed_seconds}",
        f"- Stable progress polls: {stable_polls}",
        f"- Payload keys: {keys}",
        "",
        "Resume polling with:",
        "",
        "```bash",
        (
            "uv run ~/.codex/skills/deep-research/scripts/run_gemini_deep_research.py "
            f"--action check --interaction-id {interaction_id} --outdir {outdir}"
        ),
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_terminal_summary(
    outdir: Path,
    interaction_id: str,
    status: str,
    payload: dict[str, Any],
) -> None:
    safe_id = interaction_id.replace("/", "_")
    path = outdir / f"gemini-terminal-summary-{safe_id}.md"
    keys = ", ".join(sorted(str(key) for key in payload.keys())) or "(none)"
    error = payload.get("error")
    error_text = json.dumps(error, ensure_ascii=False, indent=2) if error else "null"
    text, urls = extract_text_and_urls(payload)
    lines = [
        "# Gemini Terminal Summary",
        "",
        f"- Interaction ID: `{interaction_id}`",
        f"- Status: `{status}`",
        f"- Payload keys: {keys}",
        f"- Model/agent output extracted: {'yes' if text.strip() else 'no'}",
        f"- Source URLs extracted from model/agent output: {len(urls)}",
        "",
        "## Error",
        "",
        "```json",
        error_text,
        "```",
        "",
        "No `gemini-report-*.md` was written because the interaction did not complete.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_terminal_outputs(
    outdir: Path, interaction_id: str, status: str, payload: dict[str, Any]
) -> None:
    if status == "completed":
        write_extracted_outputs(outdir, interaction_id, payload)
    else:
        write_terminal_summary(outdir, interaction_id, status, payload)


def poll_until_terminal(
    api_key: str,
    interaction_id: str,
    outdir: Path,
    *,
    poll_seconds: int,
    timeout_minutes: int,
    api_revision: str,
) -> tuple[str, dict[str, Any], bool, int, int]:
    start = time.time()
    timeout_seconds = None if timeout_minutes <= 0 else timeout_minutes * 60
    last_fingerprint = ""
    stable_polls = 0

    while True:
        status, payload = check_job(api_key, interaction_id, outdir, api_revision)
        elapsed_seconds = int(time.time() - start)
        fingerprint = payload_progress_fingerprint(payload)
        if fingerprint == last_fingerprint:
            stable_polls += 1
        else:
            stable_polls = 0
            last_fingerprint = fingerprint
        print(
            f"interaction_id={interaction_id} status={status} "
            f"elapsed_seconds={elapsed_seconds} stable_polls={stable_polls}",
            flush=True,
        )

        if status in TERMINAL_STATUSES:
            return status, payload, False, elapsed_seconds, stable_polls

        if timeout_seconds is not None and elapsed_seconds > timeout_seconds:
            return status, payload, True, elapsed_seconds, stable_polls

        time.sleep(poll_seconds)


def write_extracted_outputs(outdir: Path, interaction_id: str, payload: dict[str, Any]) -> None:
    text, urls = extract_text_and_urls(payload)
    safe_id = interaction_id.replace("/", "_")
    report_path = outdir / f"gemini-report-{safe_id}.md"
    sources_path = outdir / f"gemini-sources-{safe_id}.md"

    if not text.strip():
        text = "(No textual output extracted from Gemini interaction payload.)"

    report_path.write_text(text + "\n", encoding="utf-8")

    lines = ["# Sources extracted from Gemini interaction", ""]
    if urls:
        for i, url in enumerate(urls, start=1):
            lines.append(f"{i}. {url}")
    else:
        lines.append("No URLs extracted.")
    sources_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Gemini Deep Research via the Interactions API"
    )
    parser.add_argument(
        "--action",
        choices=["submit", "check", "submit_and_check"],
        default="submit_and_check",
    )
    parser.add_argument("--prompt", default="", help="Prompt text")
    parser.add_argument(
        "--prompt-file", type=Path, help="Path to prompt markdown/text file"
    )
    parser.add_argument(
        "--interaction-id", default="", help="Existing interaction id to check"
    )
    parser.add_argument(
        "--agent",
        default=DEFAULT_AGENT,
        help="Gemini interaction agent id",
    )
    parser.add_argument(
        "--no-agent-config",
        dest="agent_config",
        action="store_false",
        help="Do not send Deep Research agent_config",
    )
    parser.set_defaults(agent_config=True)
    parser.add_argument(
        "--thinking-summaries",
        default="auto",
        choices=["auto", "none"],
        help="Deep Research thinking_summaries agent_config value",
    )
    parser.add_argument(
        "--visualization",
        default="",
        choices=["", "auto"],
        help="Optional Deep Research visualization agent_config value",
    )
    parser.add_argument(
        "--collaborative-planning",
        action="store_true",
        help=(
            "Enable Deep Research collaborative planning instead of direct "
            "report generation"
        ),
    )
    parser.add_argument(
        "--api-revision",
        default=os.getenv("GEMINI_INTERACTIONS_API_REVISION", DEFAULT_API_REVISION),
        help="Gemini Interactions API revision header (empty string disables header)",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("."),
        help="Output directory for snapshots and extracted artifacts",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=45,
        help="Polling interval for submit_and_check",
    )
    parser.add_argument(
        "--timeout-minutes",
        type=int,
        default=120,
        help="Timeout for submit_and_check (<=0 means no timeout)",
    )
    parser.add_argument(
        "--max-timeout-retries",
        type=int,
        default=1,
        help=(
            "When submit_and_check times out, resubmit this many times before "
            "giving up"
        ),
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional explicit .env or botfiles .rc path",
    )
    parser.add_argument(
        "--foreground",
        dest="background",
        action="store_false",
        help="Disable background execution (not supported for deep-research agents)",
    )
    parser.set_defaults(background=True)
    parser.add_argument(
        "--no-store",
        dest="store",
        action="store_false",
        help="Disable server-side storage (not recommended for background mode)",
    )
    parser.set_defaults(store=True)
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


def main() -> int:
    args = parse_args()
    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    if args.poll_seconds <= 0:
        raise RuntimeError("--poll-seconds must be > 0")
    if args.max_timeout_retries < 0:
        raise RuntimeError("--max-timeout-retries must be >= 0")
    if not args.background:
        raise RuntimeError(
            "Gemini deep-research interactions require background=true. "
            "Remove --foreground."
        )

    api_key = load_api_key(args.env_file)

    prompt = ""
    interaction_id = str(args.interaction_id or "").strip()
    if args.action in {"submit", "submit_and_check"}:
        prompt = resolve_prompt(args)
        interaction_id = submit_job(
            api_key=api_key,
            prompt=prompt,
            agent=str(args.agent),
            outdir=outdir,
            background=bool(args.background),
            store=bool(args.store),
            api_revision=str(args.api_revision or ""),
            agent_config=deep_research_agent_config(
                enabled=bool(args.agent_config),
                thinking_summaries=str(args.thinking_summaries),
                visualization=str(args.visualization),
                collaborative_planning=bool(args.collaborative_planning),
            ),
        )
        print(
            f"submitted interaction_id={interaction_id} agent={args.agent}",
            flush=True,
        )
        if args.action == "submit":
            return 0

    if not interaction_id:
        iid_file = outdir / "gemini-interaction-id.txt"
        if iid_file.exists():
            interaction_id = iid_file.read_text(encoding="utf-8").strip()
    if not interaction_id:
        raise RuntimeError(
            "No interaction id provided and outdir/gemini-interaction-id.txt not found"
        )

    if args.action == "check":
        status, payload = check_job(
            api_key, interaction_id, outdir, str(args.api_revision or "")
        )
        print(f"interaction_id={interaction_id} status={status}", flush=True)
        if status in TERMINAL_STATUSES:
            write_terminal_outputs(outdir, interaction_id, status, payload)
            return 0 if status == "completed" else 2
        return 0

    if not prompt:
        raise RuntimeError(
            "submit_and_check requires --prompt or --prompt-file so retries can resubmit"
        )

    retries_remaining = args.max_timeout_retries
    attempt = 1

    while True:
        status, payload, timed_out, elapsed_seconds, stable_polls = poll_until_terminal(
            api_key,
            interaction_id,
            outdir,
            poll_seconds=args.poll_seconds,
            timeout_minutes=args.timeout_minutes,
            api_revision=str(args.api_revision or ""),
        )

        if status in TERMINAL_STATUSES:
            write_terminal_outputs(outdir, interaction_id, status, payload)
            print(f"terminal_status={status}", flush=True)
            return 0 if status == "completed" else 2

        if not timed_out:
            raise RuntimeError(
                "Polling exited without terminal status or timeout; this should not happen"
            )

        timeout_text = (
            "no timeout"
            if args.timeout_minutes <= 0
            else f"{args.timeout_minutes} minute timeout"
        )
        print(
            f"timeout reached after {timeout_text} for interaction_id={interaction_id} "
            f"(attempt={attempt})",
            file=sys.stderr,
            flush=True,
        )

        if retries_remaining <= 0:
            write_timeout_summary(
                outdir,
                interaction_id,
                status,
                payload,
                elapsed_seconds=elapsed_seconds,
                attempt=attempt,
                stable_polls=stable_polls,
            )
            print(
                "no timeout retries remaining; keep polling later with:\n"
                "  --action check --interaction-id <id>",
                file=sys.stderr,
                flush=True,
            )
            return 3

        retries_remaining -= 1
        attempt += 1
        interaction_id = submit_job(
            api_key=api_key,
            prompt=prompt,
            agent=str(args.agent),
            outdir=outdir,
            background=bool(args.background),
            store=bool(args.store),
            api_revision=str(args.api_revision or ""),
        )
        print(
            f"resubmitted interaction_id={interaction_id} "
            f"attempt={attempt} retries_remaining={retries_remaining}",
            flush=True,
        )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
