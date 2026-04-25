#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "python-dotenv",
#   "requests",
# ]
# ///
"""Run OpenAI deep research jobs through the Responses API.

Purpose:
- Submit/check/poll deep research jobs.
- Persist raw snapshots and extracted report artifacts.

Inputs:
- OPENAI_API_KEY (environment or .env near cwd)
- Optional Azure deep-research route via:
  - AZURE_OPENAI_DEEP_RESEARCH_ENDPOINT or AZURE_OPENAI_DEEP_RESEARCH_BASE_URL
  - AZURE_OPENAI_DEEP_RESEARCH_API_KEY (falls back to AZURE_OPENAI_API_KEY)
  - AZURE_OPENAI_DEEP_RESEARCH_DEPLOYMENTS (comma-separated Azure deployment names)
- Prompt text from --prompt or --prompt-file

Outputs (under --outdir):
- openai-submit-*.json
- openai-check-*.json
- openai-provider-used.txt
- openai-response-id.txt
- openai-model-used.txt
- openai-report-<response_id>.md
- openai-sources-<response_id>.md
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

import requests
from dotenv import load_dotenv

OPENAI_API_BASE = "https://api.openai.com/v1"
OPENAI_DEFAULT_MODELS = ["o3-deep-research", "o4-mini-deep-research"]
AZURE_DEFAULT_DEPLOYMENTS = ["o3-deep-research"]
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


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_azure_base_url(value: str) -> str:
    base = value.strip().rstrip("/")
    if not base:
        return ""
    if base.endswith("/openai/v1"):
        return base
    return f"{base}/openai/v1"


def load_api_config(env_file: Path | None = None) -> dict[str, Any]:
    if env_file and env_file.exists():
        load_dotenv(env_file)
    else:
        for candidate in find_env_candidates(Path.cwd().resolve()):
            load_dotenv(candidate)
            break

    azure_base = normalize_azure_base_url(
        os.getenv("AZURE_OPENAI_DEEP_RESEARCH_BASE_URL", "")
        or os.getenv("AZURE_OPENAI_DEEP_RESEARCH_ENDPOINT", "")
    )
    azure_key = (
        os.getenv("AZURE_OPENAI_DEEP_RESEARCH_API_KEY", "").strip()
        or os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    )
    azure_models = split_csv(os.getenv("AZURE_OPENAI_DEEP_RESEARCH_DEPLOYMENTS", ""))

    if azure_base:
        if not azure_key:
            raise RuntimeError(
                "Azure deep-research route configured but no Azure API key was found. "
                "Set AZURE_OPENAI_DEEP_RESEARCH_API_KEY or AZURE_OPENAI_API_KEY."
            )
        return {
            "provider": "azure",
            "api_base": azure_base,
            "api_key": azure_key,
            "default_models": azure_models or AZURE_DEFAULT_DEPLOYMENTS,
        }

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not found and no Azure deep-research endpoint was configured."
        )
    return {
        "provider": "openai",
        "api_base": OPENAI_API_BASE,
        "api_key": api_key,
        "default_models": OPENAI_DEFAULT_MODELS,
    }


def build_headers(api_config: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_config["provider"] == "azure":
        headers["api-key"] = str(api_config["api_key"])
    else:
        headers["Authorization"] = f"Bearer {api_config['api_key']}"
    return headers


def post_response(api_config: dict[str, Any], payload: dict[str, Any]) -> requests.Response:
    return requests.post(
        f"{api_config['api_base']}/responses",
        headers=build_headers(api_config),
        data=json.dumps(payload),
        timeout=180,
    )


def get_response(api_config: dict[str, Any], response_id: str) -> requests.Response:
    return requests.get(
        f"{api_config['api_base']}/responses/{response_id}",
        headers=build_headers(api_config),
        timeout=180,
    )


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def extract_text_and_urls(payload: dict[str, Any]) -> tuple[str, list[str]]:
    texts: list[str] = []
    urls: list[str] = []

    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        texts.append(output_text.strip())

    for item in payload.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            content_type = content.get("type", "")
            if content_type in {"output_text", "text"}:
                text = content.get("text", "")
                if isinstance(text, str) and text.strip():
                    texts.append(text.strip())
                for ann in content.get("annotations", []) or []:
                    url = ann.get("url") or ann.get("target")
                    if isinstance(url, str) and url.startswith("http"):
                        urls.append(url)

    # Fallback URL scrape for payload shapes without annotations.
    if not urls:
        blob = json.dumps(payload, ensure_ascii=False)
        urls.extend(re.findall(r"https?://[^\s\"'<>]+", blob))

    deduped_urls: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped_urls.append(url)

    merged_text = "\n\n".join(chunk for chunk in texts if chunk)
    return merged_text, deduped_urls


def submit_job(
    api_config: dict[str, Any],
    prompt: str,
    models: list[str],
    outdir: Path,
    include_code_interpreter: bool,
) -> tuple[str, str]:
    last_error = ""

    tools: list[dict[str, str]] = [{"type": "web_search_preview"}]
    if include_code_interpreter:
        tools.append({"type": "code_interpreter"})

    for model in models:
        payload = {
            "model": model,
            "background": True,
            "input": prompt,
            "tools": tools,
        }
        response = post_response(api_config, payload)

        ts = iso_now()
        snapshot = outdir / f"openai-submit-{model}-{ts}.json"
        try:
            data = response.json()
        except Exception:
            data = {"raw_text": response.text, "status_code": response.status_code}
        save_json(snapshot, data)

        if response.status_code < 300 and isinstance(data, dict) and data.get("id"):
            response_id = str(data["id"])
            (outdir / "openai-provider-used.txt").write_text(
                f"{api_config['provider']}\n", encoding="utf-8"
            )
            (outdir / "openai-response-id.txt").write_text(
                f"{response_id}\n", encoding="utf-8"
            )
            (outdir / "openai-model-used.txt").write_text(
                f"{model}\n", encoding="utf-8"
            )
            return response_id, model

        last_error = (
            f"model={model} status={response.status_code} "
            f"body={json.dumps(data, ensure_ascii=False)[:1200]}"
        )

    raise RuntimeError(f"Unable to submit deep research request. Last error: {last_error}")


def check_job(
    api_config: dict[str, Any], response_id: str, outdir: Path
) -> tuple[str, dict[str, Any]]:
    response = get_response(api_config, response_id)
    response.raise_for_status()
    data = response.json()
    ts = iso_now()
    save_json(outdir / f"openai-check-{response_id}-{ts}.json", data)
    return str(data.get("status", "unknown")), data


def write_extracted_outputs(outdir: Path, response_id: str, payload: dict[str, Any]) -> None:
    text, urls = extract_text_and_urls(payload)
    report_path = outdir / f"openai-report-{response_id}.md"
    sources_path = outdir / f"openai-sources-{response_id}.md"

    if not text.strip():
        text = "(No textual output extracted from response payload.)"

    report_path.write_text(text + "\n", encoding="utf-8")

    lines = ["# Sources extracted from response", ""]
    if urls:
        for i, url in enumerate(urls, start=1):
            lines.append(f"{i}. {url}")
    else:
        lines.append("No URLs extracted.")
    sources_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run OpenAI deep research via the Responses API"
    )
    parser.add_argument(
        "--action",
        choices=["submit", "check", "submit_and_check"],
        default="submit_and_check",
    )
    parser.add_argument("--prompt", default="", help="Prompt text")
    parser.add_argument("--prompt-file", type=Path, help="Path to prompt markdown/text file")
    parser.add_argument("--response-id", default="", help="Existing response id to check")
    parser.add_argument(
        "--models",
        default="",
        help="Comma-separated model or Azure deployment fallback order",
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
        default=90,
        help="Timeout for submit_and_check",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional explicit .env path",
    )
    parser.add_argument(
        "--include-code-interpreter",
        action="store_true",
        help="Also enable code_interpreter tool on submission",
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


def main() -> int:
    args = parse_args()
    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    api_config = load_api_config(args.env_file)

    response_id = str(args.response_id or "").strip()
    if args.action in {"submit", "submit_and_check"}:
        prompt = resolve_prompt(args)
        models = split_csv(str(args.models or "")) or list(api_config["default_models"])
        response_id, model = submit_job(
            api_config=api_config,
            prompt=prompt,
            models=models,
            outdir=outdir,
            include_code_interpreter=bool(args.include_code_interpreter),
        )
        print(f"submitted response_id={response_id} model={model}")
        if args.action == "submit":
            return 0

    if not response_id:
        rid_file = outdir / "openai-response-id.txt"
        if rid_file.exists():
            response_id = rid_file.read_text(encoding="utf-8").strip()
    if not response_id:
        raise RuntimeError("No response id provided and outdir/openai-response-id.txt not found")

    if args.action == "check":
        status, payload = check_job(api_config, response_id, outdir)
        print(f"response_id={response_id} status={status}")
        if status in TERMINAL_STATUSES:
            write_extracted_outputs(outdir, response_id, payload)
            return 0 if status == "completed" else 2
        return 0

    start = time.time()
    timeout_seconds = args.timeout_minutes * 60
    no_timeout = args.timeout_minutes <= 0

    while True:
        status, payload = check_job(api_config, response_id, outdir)
        print(f"response_id={response_id} status={status}")

        if status in TERMINAL_STATUSES:
            write_extracted_outputs(outdir, response_id, payload)
            print(f"terminal_status={status}")
            return 0 if status == "completed" else 2

        if not no_timeout and (time.time() - start) > timeout_seconds:
            print("timeout reached", file=sys.stderr)
            return 3

        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
