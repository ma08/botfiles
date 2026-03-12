#!/usr/bin/env python3
"""Shared helpers for task-status skills."""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
from dataclasses import dataclass
from datetime import date, datetime
from html import unescape
from pathlib import Path
from shlex import quote as shell_quote
from shutil import which
from typing import Iterable
from urllib.parse import quote as url_quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

TRUE_VALUES = {"1", "true", "yes", "y", "on"}
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
URL_RE = re.compile(r"https?://[^\s<>()]+")
GITHUB_ISSUE_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/issues/(?P<number>\d+)(?:[/?#].*)?$",
    re.IGNORECASE,
)
GITHUB_REMOTE_RE = re.compile(
    r"^(?:https?://github\.com/|ssh://git@github\.com/|git@github\.com:)"
    r"(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ROOT_OVERRIDE_RE = re.compile(r"^\s*task-status-root:\s*(?P<value>.+?)\s*$")
BULLET_KV_RE = re.compile(r"^\s*-\s*([^:]+):\s*(.*)\s*$")
TASK_FOLDER_TIME_PREFIX_RE = re.compile(r"^\d{2}h\d{2}m\d{2}sPST-")
TASK_HASH_SUFFIX_RE = re.compile(r"-[0-9a-f]{8,}$")
ISSUE_SLUG_WITH_SEMANTIC_RE = re.compile(r"^(.+-issue-\d+)(?:-(.+))?$")
PST_LABEL_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2}) ~(?P<hour>\d{2}):(?P<minute>\d{2})(?P<ampm>am|pm) PST$"
)

TASK_METADATA_START = "<!-- TASK-METADATA:START -->"
TASK_METADATA_END = "<!-- TASK-METADATA:END -->"
LIVE_SESSION_START = "<!-- LIVE-SESSION:START -->"
LIVE_SESSION_END = "<!-- LIVE-SESSION:END -->"
TASK_STATUS_STATE_FILENAME = "task-status-state.json"


@dataclass(frozen=True)
class IssueRef:
    owner: str
    repo: str
    number: int
    url: str

    @property
    def repo_key(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass(frozen=True)
class IssueData:
    ref: IssueRef
    title: str
    body: str
    state: str
    updated_at: str
    created_at: str
    author_login: str


@dataclass(frozen=True)
class RuntimeTaskContext:
    machine: str
    coding_agent: str
    agent_session_id: str
    zellij_session: str
    zellij_link: str


@dataclass(frozen=True)
class TaskCandidate:
    task_dir: Path
    status_file: Path | None
    metadata: dict[str, str]


@dataclass(frozen=True)
class CurrentTaskPointer:
    project_root: Path
    task_dir: Path
    status_file: Path
    task_label: str
    updated_at: str


def now_pst_label() -> str:
    now = datetime.now(ZoneInfo("America/Los_Angeles"))
    return now.strftime("%Y-%m-%d ~%I:%M%p PST").replace("AM", "am").replace("PM", "pm")


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in TRUE_VALUES


def parse_rc_env_file(path: Path) -> dict[str, str]:
    env_map: dict[str, str] = {}
    if not path.is_file():
        return env_map

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].strip()
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        env_map[key] = value

    return env_map


def discover_botfiles_root(start_path: Path | None = None) -> Path | None:
    cursor = (start_path or Path(__file__)).resolve()
    for candidate in [cursor] + list(cursor.parents):
        if (candidate / ".botrc").is_file() and (candidate / "secrets").is_dir():
            return candidate
    return None


def merged_env_with_botfiles_defaults(
    base_env: dict[str, str] | None = None,
    *,
    caller_path: Path | None = None,
) -> dict[str, str]:
    merged = dict(base_env or dict(os.environ))
    root = discover_botfiles_root(caller_path or Path(__file__))
    if not root:
        return merged

    local_dir = root / "secrets" / "local"
    for rc_name in ("machine.rc", "claude-hooks.rc"):
        rc_path = local_dir / rc_name
        for key, value in parse_rc_env_file(rc_path).items():
            if key not in merged or not str(merged.get(key, "")).strip():
                merged[key] = value

    return merged


def resolve_machine_name(env: dict[str, str] | None = None) -> str:
    source = env or {}
    value = source.get("SYSTEM_NAME", "").strip()
    if value:
        return value
    host = socket.gethostname().strip()
    return host or "unknown"


def resolve_zellij_session(env: dict[str, str] | None = None) -> str:
    source = env or {}
    session = source.get("ZELLIJ_SESSION_NAME", "").strip()
    return session or "none"


def infer_agent_from_script(script_path: Path) -> str:
    path = str(script_path).lower()
    if "/codex/" in path:
        return "codex"
    if "/claude/" in path:
        return "claude"
    return "unknown"


def resolve_agent_name(
    env: dict[str, str] | None = None,
    *,
    default_agent: str = "unknown",
) -> str:
    source = env or {}
    explicit = source.get("CODING_AGENT", "").strip().lower()
    if explicit:
        return explicit
    if source.get("CODEX_THREAD_ID", "").strip() or source.get("CODEX_SESSION_ID", "").strip():
        return "codex"
    if source.get("CLAUDE_CODE_SESSION_ID", "").strip() or source.get("CLAUDE_SESSION_ID", "").strip():
        return "claude"
    return default_agent


def resolve_agent_session_id(env: dict[str, str] | None = None) -> str:
    source = env or {}
    for key in (
        "CODEX_THREAD_ID",
        "CODEX_SESSION_ID",
        "AGENT_SESSION_ID",
        "CLAUDE_CODE_SESSION_ID",
        "CLAUDE_SESSION_ID",
        "SESSION_ID",
    ):
        value = source.get(key, "").strip()
        if value:
            return value
    return "none"


def build_zellij_link(session_name: str, env: dict[str, str] | None = None) -> str:
    source = env or {}
    enabled = parse_bool(source.get("ZELLIJ_WEB_ENABLE_LINKS"), default=False)
    base_url = source.get("ZELLIJ_WEB_BASE_URL", "").strip().rstrip("/")
    if not enabled or not base_url or session_name == "none":
        return "none"
    return f"{base_url}/{url_quote(session_name, safe='')}"


def build_attach_command(session_name: str) -> str:
    if session_name == "none":
        return "none"
    return f"zellij attach {shell_quote(session_name)}"


def resolve_runtime_task_context(
    *,
    env: dict[str, str] | None = None,
    caller_path: Path | None = None,
) -> RuntimeTaskContext:
    merged = merged_env_with_botfiles_defaults(env or dict(os.environ), caller_path=caller_path)
    default_agent = infer_agent_from_script(caller_path or Path(__file__))
    zellij_session = resolve_zellij_session(merged)
    return RuntimeTaskContext(
        machine=resolve_machine_name(merged),
        coding_agent=resolve_agent_name(merged, default_agent=default_agent),
        agent_session_id=resolve_agent_session_id(merged),
        zellij_session=zellij_session,
        zellij_link=build_zellij_link(zellij_session, merged),
    )


def slugify(value: str) -> str:
    normalized = value.encode("ascii", errors="ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug or "task"


def enforce_slug_length(slug: str, max_length: int) -> str:
    if max_length < 16:
        max_length = 16
    if len(slug) <= max_length:
        return slug
    digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:8]
    head_length = max_length - len(digest) - 1
    head = slug[:head_length].rstrip("-")
    if not head:
        head = slug[:head_length]
    return f"{head}-{digest}"


def build_issue_slug(repo: str, number: int, title: str, max_length: int = 60) -> str:
    repo_slug = slugify(repo)
    title_slug = slugify(title)
    raw = f"{repo_slug}-issue-{number}"
    if title_slug:
        raw = f"{raw}-{title_slug}"
    return enforce_slug_length(raw, max_length=max_length)


def extract_urls(text: str) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for match in URL_RE.finditer(text or ""):
        url = match.group(0).rstrip(".,);:!?'\"")
        if not url or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def parse_github_issue_url(url: str) -> IssueRef | None:
    match = GITHUB_ISSUE_RE.match(url.strip())
    if not match:
        return None
    owner = match.group("owner")
    repo = match.group("repo")
    number = int(match.group("number"))
    canonical = f"https://github.com/{owner}/{repo}/issues/{number}"
    return IssueRef(owner=owner, repo=repo, number=number, url=canonical)


def extract_primary_issue_ref(text: str) -> IssueRef | None:
    for url in extract_urls(text):
        ref = parse_github_issue_url(url)
        if ref:
            return ref
    return None


def run_command(
    cmd: list[str],
    *,
    input_text: str | None = None,
    timeout_seconds: int = 20,
) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError:
        return (127, "", f"command not found: {cmd[0]}")
    except subprocess.TimeoutExpired:
        return (124, "", f"command timed out: {' '.join(cmd)}")
    return (proc.returncode, proc.stdout, proc.stderr)


def gh_available() -> bool:
    return which("gh") is not None


def gh_authenticated() -> bool:
    if not gh_available():
        return False
    code, _, _ = run_command(["gh", "auth", "status", "-h", "github.com"], timeout_seconds=10)
    return code == 0


def fetch_issue_data(ref: IssueRef) -> IssueData | None:
    if not gh_available():
        return None
    code, stdout, _ = run_command(
        [
            "gh",
            "issue",
            "view",
            str(ref.number),
            "--repo",
            ref.repo_key,
            "--json",
            "number,title,body,state,updatedAt,createdAt,author,url",
        ],
        timeout_seconds=20,
    )
    if code != 0:
        return None
    payload = json.loads(stdout)
    author = payload.get("author") or {}
    return IssueData(
        ref=ref,
        title=(payload.get("title") or "").strip(),
        body=payload.get("body") or "",
        state=(payload.get("state") or "").strip(),
        updated_at=(payload.get("updatedAt") or "").strip(),
        created_at=(payload.get("createdAt") or "").strip(),
        author_login=(author.get("login") or "").strip(),
    )


def update_issue_body(ref: IssueRef, new_body: str) -> tuple[bool, str]:
    if not gh_available():
        return (False, "gh is not available")
    code, _, stderr = run_command(
        [
            "gh",
            "issue",
            "edit",
            str(ref.number),
            "--repo",
            ref.repo_key,
            "--body-file",
            "-",
        ],
        input_text=new_body,
        timeout_seconds=20,
    )
    if code != 0:
        return (False, stderr.strip() or "failed to update issue body")
    return (True, "updated")


def fetch_page_title(url: str, timeout_seconds: int = 4) -> str | None:
    req = Request(url, headers={"User-Agent": "task-status-helper/1.0"})
    try:
        with urlopen(req, timeout=timeout_seconds) as response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                return None
            raw = response.read(200_000)
    except Exception:
        return None

    text = raw.decode("utf-8", errors="ignore")
    match = TITLE_RE.search(text)
    if not match:
        return None
    title = unescape(match.group(1))
    title = re.sub(r"\s+", " ", title).strip()
    if not title:
        return None
    return title[:200]


def build_task_metadata_block(
    *,
    machine: str,
    coding_agent: str,
    agent_session_id: str,
    issue_url: str,
    issue_repo: str,
    issue_number: str,
    zellij_session: str,
    zellij_link: str,
    last_synced: str,
) -> str:
    lines = [
        TASK_METADATA_START,
        "## Task Metadata",
        f"- Machine: {machine}",
        f"- Coding Agent: {coding_agent}",
        f"- Agent Session ID: {agent_session_id}",
        f"- GitHub Issue: {issue_url}",
        f"- GitHub Repo: {issue_repo}",
        f"- GitHub Issue Number: {issue_number}",
        f"- Zellij Session: {zellij_session}",
        f"- Zellij Link: {zellij_link}",
        f"- Last Synced: {last_synced}",
        TASK_METADATA_END,
    ]
    return "\n".join(lines)


def build_live_session_block(
    *,
    machine: str,
    coding_agent: str,
    agent_session_id: str,
    zellij_session: str,
    zellij_link: str,
    attach_command: str,
    last_updated: str,
) -> str:
    def plain_value(value: str) -> str:
        return (value or "none").replace("`", "").strip() or "none"

    lines = [
        LIVE_SESSION_START,
        "## Live Session",
        f"- Machine: `{plain_value(machine)}`",
        f"- Coding Agent: `{plain_value(coding_agent)}`",
        f"- Agent Session ID: `{plain_value(agent_session_id)}`",
        f"- Zellij Session: `{plain_value(zellij_session)}`",
        f"- Zellij Link: {plain_value(zellij_link)}",
        f"- Attach Command: `{plain_value(attach_command)}`",
        f"- Last Updated: `{plain_value(last_updated)}`",
        LIVE_SESSION_END,
    ]
    return "\n".join(lines)


def upsert_marked_block(
    original_text: str,
    block: str,
    *,
    start_marker: str,
    end_marker: str,
    prefer_top: bool,
) -> str:
    text = original_text or ""
    block_text = block.strip("\n")
    marker_span = find_unfenced_marker_span(text, start_marker=start_marker, end_marker=end_marker)

    if marker_span:
        start_line, end_line = marker_span
        lines = text.splitlines()
        prefix = "\n".join(lines[:start_line]).rstrip("\n")
        suffix = "\n".join(lines[end_line + 1 :]).lstrip("\n")
        chunks = [part for part in [prefix, block_text, suffix] if part]
        return "\n\n".join(chunks).rstrip() + "\n"

    stripped = text.strip("\n")
    if prefer_top:
        if stripped:
            return f"{block_text}\n\n{stripped}\n"
        return f"{block_text}\n"

    if stripped:
        return f"{stripped}\n\n{block_text}\n"
    return f"{block_text}\n"


def extract_marked_block(text: str, *, start_marker: str, end_marker: str) -> str | None:
    marker_span = find_unfenced_marker_span(text, start_marker=start_marker, end_marker=end_marker)
    if not marker_span:
        return None
    start_line, end_line = marker_span
    lines = text.splitlines()
    return "\n".join(lines[start_line : end_line + 1])


def find_unfenced_marker_span(
    text: str,
    *,
    start_marker: str,
    end_marker: str,
) -> tuple[int, int] | None:
    lines = text.splitlines()
    in_code_block = False
    start_line = -1

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if start_line < 0 and stripped == start_marker:
            start_line = index
            continue
        if start_line >= 0 and stripped == end_marker:
            return (start_line, index)
    return None


def parse_bullet_metadata(block: str | None) -> dict[str, str]:
    if not block:
        return {}
    values: dict[str, str] = {}
    for line in block.splitlines():
        match = BULLET_KV_RE.match(line)
        if not match:
            continue
        key = match.group(1).strip()
        value = match.group(2).strip()
        values[key] = value
    return values


def resolve_status_file(task_dir: Path) -> Path | None:
    status = task_dir / "status.md"
    if status.is_file():
        return status
    legacy = task_dir / "README.md"
    if legacy.is_file():
        return legacy
    return None


def parse_task_date(task_dir: Path) -> date | None:
    parent_name = task_dir.parent.name
    if not DATE_RE.match(parent_name):
        return None
    try:
        return datetime.strptime(parent_name, "%Y-%m-%d").date()
    except ValueError:
        return None


def task_age_days(task_dir: Path, today: date) -> int | None:
    task_date = parse_task_date(task_dir)
    if not task_date:
        return None
    return (today - task_date).days


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def sanitize_task_label(raw_value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw_value.strip())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        return ""
    return normalized[:80]


def extract_full_task_folder_slug(raw_value: str) -> str:
    sanitized = sanitize_task_label(raw_value)
    if not sanitized:
        return ""
    without_time_prefix = TASK_FOLDER_TIME_PREFIX_RE.sub("", sanitized)
    return sanitize_task_label(without_time_prefix) or without_time_prefix


def extract_semantic_task_label(raw_value: str) -> str:
    sanitized = extract_full_task_folder_slug(raw_value)
    if not sanitized:
        return ""

    candidate = TASK_HASH_SUFFIX_RE.sub("", sanitized).strip("-")
    if not candidate:
        candidate = sanitized

    issue_match = ISSUE_SLUG_WITH_SEMANTIC_RE.match(candidate)
    if issue_match:
        issue_prefix = issue_match.group(1).strip("-")
        semantic_suffix = (issue_match.group(2) or "").strip("-")
        candidate = f"{issue_prefix}-{semantic_suffix}" if semantic_suffix else issue_prefix

    return sanitize_task_label(candidate)


def normalize_repo_slug(raw_value: str) -> str:
    return slugify(raw_value)


def parse_github_repo_key(raw_value: str) -> str | None:
    candidate = (raw_value or "").strip()
    if not candidate:
        return None
    if "/" in candidate and not candidate.startswith(("http://", "https://", "ssh://", "git@")):
        owner, repo = candidate.split("/", 1)
        owner = owner.strip().strip("/")
        repo = repo.strip().strip("/").removesuffix(".git")
        if owner and repo:
            return f"{owner.lower()}/{repo.lower()}"
        return None

    match = GITHUB_REMOTE_RE.match(candidate)
    if not match:
        return None
    owner = match.group("owner").strip().lower()
    repo = match.group("repo").strip().lower()
    if not owner or not repo:
        return None
    return f"{owner}/{repo}"


def resolve_git_origin_repo_key(repo_root: Path) -> str | None:
    resolved_root = repo_root.expanduser().resolve()
    if not resolved_root.is_dir():
        return None
    code, stdout, _ = run_command(
        ["git", "-C", str(resolved_root), "remote", "get-url", "origin"],
        timeout_seconds=10,
    )
    if code != 0:
        return None
    return parse_github_repo_key(stdout.strip())


def local_repo_search_roots(current_project_root: Path | None = None) -> list[Path]:
    candidates: list[Path] = []
    if current_project_root:
        candidates.append(current_project_root.expanduser().resolve().parent)
    candidates.append((Path.home() / "pro").resolve())

    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen or not candidate.is_dir():
            continue
        seen.add(candidate)
        unique.append(candidate)
    return unique


def find_local_repo_roots_for_github_repo(
    repo_key: str,
    *,
    current_project_root: Path | None = None,
) -> list[Path]:
    target_repo_key = parse_github_repo_key(repo_key)
    if not target_repo_key:
        return []

    matches: list[Path] = []
    seen: set[Path] = set()

    def maybe_add(repo_root: Path) -> None:
        resolved = repo_root.expanduser().resolve()
        if resolved in seen or not resolved.is_dir():
            return
        seen.add(resolved)
        if resolve_git_origin_repo_key(resolved) == target_repo_key:
            matches.append(resolved)

    if current_project_root:
        maybe_add(current_project_root)

    for search_root in local_repo_search_roots(current_project_root):
        for child in sorted(search_root.iterdir()):
            if not child.is_dir():
                continue
            if not (child / ".git").exists():
                continue
            maybe_add(child)

    return matches


def parse_pst_label(value: str) -> datetime | None:
    match = PST_LABEL_RE.match((value or "").strip())
    if not match:
        return None

    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    ampm = match.group("ampm")
    if ampm == "am":
        hour = 0 if hour == 12 else hour
    else:
        hour = 12 if hour == 12 else hour + 12

    try:
        date_part = datetime.strptime(match.group("date"), "%Y-%m-%d").date()
    except ValueError:
        return None

    return datetime(
        date_part.year,
        date_part.month,
        date_part.day,
        hour,
        minute,
        tzinfo=ZoneInfo("America/Los_Angeles"),
    )


def read_task_metadata(status_file: Path | None) -> dict[str, str]:
    if not status_file:
        return {}
    text = read_text(status_file)
    block = extract_marked_block(
        text,
        start_marker=TASK_METADATA_START,
        end_marker=TASK_METADATA_END,
    )
    return parse_bullet_metadata(block)


def resolve_task_status_root(project_root: Path, *, caller_path: Path | None = None) -> Path:
    filenames = ("AGENTS.md", "CLAUDE.md")
    if caller_path:
        inferred = infer_agent_from_script(caller_path)
        if inferred == "claude":
            filenames = ("CLAUDE.md", "AGENTS.md")
        elif inferred == "codex":
            filenames = ("AGENTS.md", "CLAUDE.md")

    for filename in filenames:
        path = project_root / filename
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            match = ROOT_OVERRIDE_RE.match(line)
            if not match:
                continue
            raw_value = match.group("value").strip().strip('"').strip("'")
            if not raw_value:
                continue
            # Normalize patterns like .../YYYY-MM-DD/<task-slug>/
            for marker in ("/YYYY-MM-DD", "YYYY-MM-DD", "<task-slug>"):
                if marker in raw_value:
                    raw_value = raw_value.split(marker, 1)[0]
            raw_value = raw_value.rstrip("/")
            if not raw_value:
                continue
            candidate = Path(raw_value).expanduser()
            return candidate if candidate.is_absolute() else project_root / candidate
    return project_root / "context" / "daily"


def find_task_dirs(root: Path, slug: str | None = None) -> list[Path]:
    if not root.is_dir():
        return []
    candidates: list[Path] = []
    slug_token = slug.lower() if slug else None
    for date_dir in sorted(root.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for task_dir in sorted(date_dir.iterdir(), reverse=True):
            if not task_dir.is_dir():
                continue
            if slug_token and slug_token not in task_dir.name.lower():
                continue
            candidates.append(task_dir)
    return candidates


def load_task_candidates(root: Path, slug: str | None = None) -> list[TaskCandidate]:
    candidates: list[TaskCandidate] = []
    for task_dir in find_task_dirs(root, slug=slug):
        status_file = resolve_status_file(task_dir)
        candidates.append(
            TaskCandidate(
                task_dir=task_dir,
                status_file=status_file,
                metadata=read_task_metadata(status_file),
            )
        )
    return candidates


def task_candidate_sort_key(candidate: TaskCandidate) -> tuple[float, float, str]:
    last_synced = parse_pst_label(candidate.metadata.get("Last Synced", ""))
    last_synced_ts = last_synced.timestamp() if last_synced else 0.0
    status_mtime = 0.0
    if candidate.status_file and candidate.status_file.is_file():
        try:
            status_mtime = candidate.status_file.stat().st_mtime
        except OSError:
            status_mtime = 0.0
    return (last_synced_ts, status_mtime, candidate.task_dir.name)


def sort_task_candidates_by_recency(candidates: list[TaskCandidate]) -> list[TaskCandidate]:
    return sorted(candidates, key=task_candidate_sort_key, reverse=True)


def session_matching_candidates(
    candidates: list[TaskCandidate],
    agent_session_id: str,
) -> list[TaskCandidate]:
    if not agent_session_id or agent_session_id == "none":
        return []
    return [
        candidate
        for candidate in candidates
        if candidate.metadata.get("Agent Session ID", "").strip() == agent_session_id
    ]


def resolve_task_status_state_path(*, caller_path: Path | None = None) -> Path | None:
    root = discover_botfiles_root(caller_path or Path(__file__))
    if not root:
        return None
    return root / "secrets" / "local" / TASK_STATUS_STATE_FILENAME


def infer_project_root_from_path(path: Path) -> Path | None:
    resolved = path.expanduser().resolve()
    start = resolved if resolved.is_dir() else resolved.parent
    for candidate in [start] + list(start.parents):
        if (
            (candidate / "AGENTS.md").is_file()
            or (candidate / "CLAUDE.md").is_file()
            or (candidate / ".botrc").is_file()
        ):
            return candidate
    return None


def build_session_task_key(project_root: Path, coding_agent: str, agent_session_id: str) -> str:
    return f"{project_root.resolve()}::{(coding_agent or 'unknown').strip() or 'unknown'}::{agent_session_id.strip()}"


def load_json_map(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def save_json_map(path: Path, payload: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def upsert_current_task_pointer(
    status_file: Path,
    *,
    coding_agent: str,
    agent_session_id: str,
    task_label: str | None = None,
    caller_path: Path | None = None,
) -> bool:
    if not agent_session_id or agent_session_id == "none":
        return False

    state_path = resolve_task_status_state_path(caller_path=caller_path)
    project_root = infer_project_root_from_path(status_file)
    if not state_path or not project_root:
        return False

    resolved_status = status_file.expanduser().resolve()
    task_dir = resolved_status.parent
    key = build_session_task_key(project_root, coding_agent, agent_session_id)
    payload = load_json_map(state_path)
    entry = {
        "project_root": str(project_root),
        "task_dir": str(task_dir),
        "status_file": str(resolved_status),
        "task_label": task_label or extract_full_task_folder_slug(task_dir.name),
        "updated_at": now_pst_label(),
    }
    if payload.get(key) == entry:
        return False
    payload[key] = entry
    save_json_map(state_path, payload)
    return True


def delete_current_task_pointer(
    project_root: Path,
    *,
    coding_agent: str,
    agent_session_id: str,
    caller_path: Path | None = None,
) -> bool:
    if not agent_session_id or agent_session_id == "none":
        return False

    state_path = resolve_task_status_state_path(caller_path=caller_path)
    if not state_path:
        return False

    payload = load_json_map(state_path)
    key = build_session_task_key(project_root, coding_agent, agent_session_id)
    if key not in payload:
        return False

    payload.pop(key, None)
    if payload:
        save_json_map(state_path, payload)
    else:
        state_path.unlink(missing_ok=True)
    return True


def resolve_current_task_pointer(
    project_root: Path,
    *,
    coding_agent: str,
    agent_session_id: str,
    caller_path: Path | None = None,
) -> CurrentTaskPointer | None:
    if not agent_session_id or agent_session_id == "none":
        return None

    state_path = resolve_task_status_state_path(caller_path=caller_path)
    if not state_path:
        return None
    payload = load_json_map(state_path)
    key = build_session_task_key(project_root, coding_agent, agent_session_id)
    raw = payload.get(key)
    if not isinstance(raw, dict):
        return None

    task_dir_raw = str(raw.get("task_dir", "")).strip()
    status_file_raw = str(raw.get("status_file", "")).strip()
    task_label = str(raw.get("task_label", "")).strip()
    updated_at = str(raw.get("updated_at", "")).strip()
    if not task_dir_raw or not status_file_raw:
        return None

    task_dir = Path(task_dir_raw).expanduser().resolve()
    status_file = Path(status_file_raw).expanduser().resolve()
    if not task_dir.is_dir() or not status_file.is_file():
        return None

    return CurrentTaskPointer(
        project_root=project_root.resolve(),
        task_dir=task_dir,
        status_file=status_file,
        task_label=task_label or extract_full_task_folder_slug(task_dir.name),
        updated_at=updated_at,
    )


def non_issue_urls(urls: Iterable[str], issue_ref: IssueRef | None) -> list[str]:
    if not issue_ref:
        return list(urls)
    issue_url = issue_ref.url
    return [url for url in urls if url != issue_url]
