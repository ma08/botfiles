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
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
ATX_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.*?)\s*$")
BULLET_PREFIX_RE = re.compile(r"^[-*+]\s+")
NUMBERED_PREFIX_RE = re.compile(r"^\d+\.\s+")
GITHUB_ISSUE_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/issues/(?P<number>\d+)(?:[/?#].*)?$",
    re.IGNORECASE,
)
LINEAR_ISSUE_RE = re.compile(
    r"^https?://linear\.app/(?P<workspace>[^/\s]+)/issue/(?P<identifier>[A-Za-z][A-Za-z0-9_]*-\d+)"
    r"(?:/(?P<title_slug>[^?#\s]+))?(?:[/?#].*)?$",
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

TRACKER_KIND_GITHUB = "github"
TRACKER_KIND_LINEAR = "linear"
TRACKER_KIND_NONE = "none"
TRACKER_REMOTE_SESSION_MARKER = "LIVE-SESSION"
LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql"

TASK_METADATA_REQUIRED_FIELDS = (
    "tracker_kind",
    "tracker_url",
    "tracker_human_id",
    "tracker_title",
    "machine",
    "coding_agent",
    "agent_session_id",
    "task_folder",
    "task_status_path",
    "transcript_path",
    "last_synced_at",
)
TASK_METADATA_OPTIONAL_FIELDS = (
    "workspace_path",
    "zellij_session",
    "zellij_link",
    "remote_session_anchor_kind",
    "remote_session_anchor_id",
)
TASK_METADATA_GITHUB_COMPAT_FIELDS = (
    "github_issue",
    "github_repo",
    "github_issue_number",
)
TASK_METADATA_LINEAR_COMPAT_FIELDS = (
    "linear_issue_id",
    "linear_issue_identifier",
    "linear_team_id",
    "linear_team_name",
    "linear_project_id",
    "linear_project_name",
)
TASK_METADATA_RENDER_ORDER = (
    TASK_METADATA_REQUIRED_FIELDS
    + TASK_METADATA_OPTIONAL_FIELDS
    + TASK_METADATA_GITHUB_COMPAT_FIELDS
    + TASK_METADATA_LINEAR_COMPAT_FIELDS
)
TASK_METADATA_FIELD_LABELS = {
    "tracker_kind": "Tracker Kind",
    "tracker_url": "Tracker URL",
    "tracker_human_id": "Tracker Human ID",
    "tracker_title": "Tracker Title",
    "machine": "Machine",
    "coding_agent": "Coding Agent",
    "agent_session_id": "Agent Session ID",
    "task_folder": "Task Folder",
    "task_status_path": "Task Status Path",
    "transcript_path": "Transcript Path",
    "last_synced_at": "Last Synced",
    "workspace_path": "Workspace Path",
    "zellij_session": "Zellij Session",
    "zellij_link": "Zellij Link",
    "remote_session_anchor_kind": "Remote Session Anchor Kind",
    "remote_session_anchor_id": "Remote Session Anchor ID",
    "github_issue": "GitHub Issue",
    "github_repo": "GitHub Repo",
    "github_issue_number": "GitHub Issue Number",
    "linear_issue_id": "Linear Issue ID",
    "linear_issue_identifier": "Linear Issue Identifier",
    "linear_team_id": "Linear Team ID",
    "linear_team_name": "Linear Team Name",
    "linear_project_id": "Linear Project ID",
    "linear_project_name": "Linear Project Name",
}


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
class LinearIssueRef:
    workspace: str
    identifier: str
    url: str
    title_slug: str


@dataclass(frozen=True)
class LinearIssueData:
    ref: LinearIssueRef
    id: str
    identifier: str
    title: str
    url: str
    description: str
    updated_at: str
    created_at: str
    state_name: str
    team_id: str
    team_name: str
    project_id: str
    project_name: str


@dataclass(frozen=True)
class TrackerRef:
    kind: str
    url: str
    human_id: str
    title_slug: str = ""
    github_issue: IssueRef | None = None
    linear_issue: LinearIssueRef | None = None


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
class TrackerTaskHome:
    project_root: Path
    task_status_root: Path
    candidate: TaskCandidate


@dataclass(frozen=True)
class CurrentTaskPointer:
    project_root: Path
    workspace_path: Path | None
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
    for rc_name in ("machine.rc", "linear.rc", "claude-hooks.rc"):
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


def resolve_agent_session_id(
    env: dict[str, str] | None = None,
    *,
    project_root: str | None = None,
) -> str:
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
    # Claude Code doesn't export a session ID env var, so fall back to
    # the most recent history.jsonl entry for the project.
    if source.get("CLAUDECODE", "").strip() in TRUE_VALUES:
        resolved = _resolve_claude_session_from_history(project_root)
        if resolved and resolved != "none":
            return resolved
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
    project_root: str | None = None,
) -> RuntimeTaskContext:
    merged = merged_env_with_botfiles_defaults(env or dict(os.environ), caller_path=caller_path)
    default_agent = infer_agent_from_script(caller_path or Path(__file__))
    zellij_session = resolve_zellij_session(merged)
    return RuntimeTaskContext(
        machine=resolve_machine_name(merged),
        coding_agent=resolve_agent_name(merged, default_agent=default_agent),
        agent_session_id=resolve_agent_session_id(merged, project_root=project_root),
        zellij_session=zellij_session,
        zellij_link=build_zellij_link(zellij_session, merged),
    )


def resolve_codex_home(env: dict[str, str] | None = None) -> Path:
    source = env or {}
    raw_value = source.get("CODEX_HOME", "").strip()
    if raw_value:
        return Path(raw_value).expanduser()
    return Path.home() / ".codex"


def _encode_claude_project_dir(project_root: str) -> str:
    """Encode a project root path to Claude's project directory name.

    Claude stores per-project data under ``~/.claude/projects/<encoded>/``
    where ``<encoded>`` is the absolute path with every character that is
    not alphanumeric or ``-`` replaced by ``-``.  The leading ``-`` (from
    the root ``/``) is kept.
    """
    resolved = Path(project_root).expanduser().resolve()
    return re.sub(r"[^a-zA-Z0-9-]", "-", str(resolved))


def _resolve_claude_session_from_history(project_root: str | None) -> str:
    """Identify the current Claude session via ``~/.claude/history.jsonl``.

    Claude appends a ``{sessionId, project, timestamp, ...}`` entry to
    ``history.jsonl`` when the user submits a prompt, *before* tool
    execution begins.  The most recent entry whose ``project`` matches
    *project_root* therefore identifies the session that is currently
    executing.

    This is preferred over file-mtime heuristics because it is scoped to
    the prompt that triggered the current tool call.  A narrow race
    exists when a second concurrent session submits a prompt between the
    history write and this read, but that window is typically
    sub-second.
    """
    history_path = Path.home() / ".claude" / "history.jsonl"
    if not history_path.is_file():
        return "none"

    root = str(Path(project_root or os.getcwd()).expanduser().resolve())

    try:
        lines = history_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return "none"

    for line in reversed(lines):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            entry = json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            continue
        if entry.get("project") != root:
            continue
        session_id = (entry.get("sessionId") or "").strip()
        if session_id:
            return session_id

    return "none"


def resolve_codex_transcript_path(
    agent_session_id: str,
    env: dict[str, str] | None = None,
) -> str:
    normalized = (agent_session_id or "").strip()
    if not normalized or normalized == "none":
        return "none"

    sessions_root = resolve_codex_home(env) / "sessions"
    if not sessions_root.is_dir():
        return "none"

    matches = sorted(sessions_root.rglob(f"*{normalized}*.jsonl"))
    if not matches:
        return "none"
    return str(matches[0].resolve())


def resolve_claude_transcript_path(
    agent_session_id: str,
    *,
    project_root: str | None = None,
) -> str:
    normalized = (agent_session_id or "").strip()
    if not normalized or normalized == "none":
        return "none"

    # Try per-session JSONL in the project directory first.
    if project_root:
        encoded = _encode_claude_project_dir(project_root)
        session_file = Path.home() / ".claude" / "projects" / encoded / f"{normalized}.jsonl"
        if session_file.is_file():
            return str(session_file.resolve())

    # Fall back: scan all project dirs for a matching session file.
    projects_root = Path.home() / ".claude" / "projects"
    if projects_root.is_dir():
        for project_dir in projects_root.iterdir():
            if not project_dir.is_dir():
                continue
            candidate = project_dir / f"{normalized}.jsonl"
            if candidate.is_file():
                return str(candidate.resolve())

    # Last resort: global history file.
    history_path = Path.home() / ".claude" / "history.jsonl"
    if history_path.is_file():
        return str(history_path.resolve())
    return "none"


def resolve_transcript_path(
    coding_agent: str,
    agent_session_id: str,
    *,
    env: dict[str, str] | None = None,
    project_root: str | None = None,
) -> str:
    normalized_agent = (coding_agent or "").strip().lower()
    normalized_session_id = (agent_session_id or "").strip()
    if not normalized_session_id or normalized_session_id == "none":
        return "none"
    if normalized_agent == "codex":
        return resolve_codex_transcript_path(normalized_session_id, env)
    if normalized_agent == "claude":
        return resolve_claude_transcript_path(normalized_session_id, project_root=project_root)
    return "none"


def slugify(value: str) -> str:
    normalized = value.encode("ascii", errors="ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug or "task"


def humanize_slug(value: str) -> str:
    text = re.sub(r"[-_]+", " ", (value or "").strip()).strip()
    text = re.sub(r"\s{2,}", " ", text)
    return text or TRACKER_KIND_NONE


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


def build_linear_issue_slug(identifier: str, title: str, max_length: int = 60) -> str:
    raw = slugify(identifier)
    title_slug = slugify(title)
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


def parse_linear_issue_url(url: str) -> LinearIssueRef | None:
    match = LINEAR_ISSUE_RE.match(url.strip())
    if not match:
        return None
    workspace = match.group("workspace").strip()
    identifier = match.group("identifier").upper()
    title_slug = (match.group("title_slug") or "").strip().strip("/")
    canonical = f"https://linear.app/{workspace}/issue/{identifier}"
    return LinearIssueRef(
        workspace=workspace,
        identifier=identifier,
        url=canonical,
        title_slug=title_slug,
    )


def parse_tracker_url(url: str) -> TrackerRef | None:
    linear_ref = parse_linear_issue_url(url)
    if linear_ref:
        return TrackerRef(
            kind=TRACKER_KIND_LINEAR,
            url=linear_ref.url,
            human_id=linear_ref.identifier,
            title_slug=linear_ref.title_slug,
            linear_issue=linear_ref,
        )

    github_ref = parse_github_issue_url(url)
    if github_ref:
        return TrackerRef(
            kind=TRACKER_KIND_GITHUB,
            url=github_ref.url,
            human_id=f"{github_ref.repo_key}#{github_ref.number}",
            github_issue=github_ref,
        )

    return None


def extract_primary_issue_ref(text: str) -> IssueRef | None:
    for url in extract_urls(text):
        ref = parse_github_issue_url(url)
        if ref:
            return ref
    return None


def extract_primary_linear_issue_ref(text: str) -> LinearIssueRef | None:
    for url in extract_urls(text):
        ref = parse_linear_issue_url(url)
        if ref:
            return ref
    return None


def extract_primary_tracker_ref(text: str) -> TrackerRef | None:
    linear_ref = extract_primary_linear_issue_ref(text)
    if linear_ref:
        return TrackerRef(
            kind=TRACKER_KIND_LINEAR,
            url=linear_ref.url,
            human_id=linear_ref.identifier,
            title_slug=linear_ref.title_slug,
            linear_issue=linear_ref,
        )

    github_ref = extract_primary_issue_ref(text)
    if github_ref:
        return TrackerRef(
            kind=TRACKER_KIND_GITHUB,
            url=github_ref.url,
            human_id=f"{github_ref.repo_key}#{github_ref.number}",
            github_issue=github_ref,
        )

    return None


def build_tracker_slug(tracker_ref: TrackerRef, title: str, max_length: int = 60) -> str:
    if tracker_ref.kind == TRACKER_KIND_GITHUB and tracker_ref.github_issue:
        return build_issue_slug(
            tracker_ref.github_issue.repo,
            tracker_ref.github_issue.number,
            title,
            max_length=max_length,
        )
    if tracker_ref.kind == TRACKER_KIND_LINEAR:
        return build_linear_issue_slug(tracker_ref.human_id, title, max_length=max_length)

    raw = slugify(f"{tracker_ref.kind}-{tracker_ref.human_id}-{title}")
    return enforce_slug_length(raw, max_length=max_length)


def resolve_tracker_title(tracker_ref: TrackerRef) -> str:
    if tracker_ref.kind == TRACKER_KIND_GITHUB and tracker_ref.github_issue:
        issue_data = fetch_issue_data(tracker_ref.github_issue)
        if issue_data and issue_data.title:
            return issue_data.title
    if tracker_ref.kind == TRACKER_KIND_LINEAR and tracker_ref.linear_issue:
        issue_data = fetch_linear_issue_data(tracker_ref.linear_issue)
        if issue_data and issue_data.title:
            return issue_data.title
    if tracker_ref.title_slug:
        return humanize_slug(tracker_ref.title_slug)
    page_title = fetch_page_title(tracker_ref.url)
    return page_title or TRACKER_KIND_NONE


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


def resolve_linear_api_key(
    env: dict[str, str] | None = None,
    *,
    caller_path: Path | None = None,
) -> str:
    merged = merged_env_with_botfiles_defaults(
        env or dict(os.environ),
        caller_path=caller_path or Path(__file__),
    )
    return merged.get("LINEAR_API_KEY", "").strip()


def run_linear_graphql(
    query: str,
    *,
    variables: dict[str, object] | None = None,
    env: dict[str, str] | None = None,
    caller_path: Path | None = None,
    timeout_seconds: int = 20,
) -> tuple[dict[str, object] | None, str]:
    api_key = resolve_linear_api_key(env, caller_path=caller_path)
    if not api_key:
        return None, "LINEAR_API_KEY is not set"

    req = Request(
        LINEAR_GRAPHQL_URL,
        data=json.dumps({"query": query, "variables": variables or {}}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": api_key,
            "User-Agent": "task-status-helper/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return None, str(exc)

    if not isinstance(payload, dict):
        return None, "invalid Linear API response"
    if payload.get("errors"):
        return None, json.dumps(payload["errors"])

    data = payload.get("data")
    if not isinstance(data, dict):
        return None, "Linear API response missing data"
    return data, ""


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


def fetch_linear_issue_data(
    ref: LinearIssueRef,
    *,
    env: dict[str, str] | None = None,
    caller_path: Path | None = None,
) -> LinearIssueData | None:
    data, _ = run_linear_graphql(
        """
        query IssueByIdentifier($identifier: String!) {
          issue(id: $identifier) {
            id
            identifier
            title
            url
            description
            updatedAt
            createdAt
            state {
              name
            }
            team {
              id
              name
            }
            project {
              id
              name
            }
          }
        }
        """,
        variables={"identifier": ref.identifier},
        env=env,
        caller_path=caller_path,
    )
    if not data:
        return None

    issue = data.get("issue")
    if not isinstance(issue, dict):
        return None

    state = issue.get("state") or {}
    team = issue.get("team") or {}
    project = issue.get("project") or {}

    return LinearIssueData(
        ref=ref,
        id=str(issue.get("id") or "").strip(),
        identifier=str(issue.get("identifier") or ref.identifier).strip(),
        title=str(issue.get("title") or "").strip(),
        url=str(issue.get("url") or ref.url).strip(),
        description=issue.get("description") or "",
        updated_at=str(issue.get("updatedAt") or "").strip(),
        created_at=str(issue.get("createdAt") or "").strip(),
        state_name=str(state.get("name") or "").strip(),
        team_id=str(team.get("id") or "").strip(),
        team_name=str(team.get("name") or "").strip(),
        project_id=str(project.get("id") or "").strip(),
        project_name=str(project.get("name") or "").strip(),
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


def update_linear_issue_body(
    issue_id: str,
    new_body: str,
    *,
    env: dict[str, str] | None = None,
    caller_path: Path | None = None,
) -> tuple[bool, str]:
    if not issue_id.strip():
        return (False, "Linear issue id is required")

    data, error = run_linear_graphql(
        """
        mutation UpdateIssueDescription($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
          }
        }
        """,
        variables={
            "id": issue_id,
            "input": {
                "description": new_body,
            },
        },
        env=env,
        caller_path=caller_path,
    )
    if not data:
        return (False, error or "failed to update Linear issue body")

    mutation = data.get("issueUpdate")
    if not isinstance(mutation, dict) or not mutation.get("success"):
        return (False, "Linear issue update did not report success")
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
    tracker_kind: str,
    tracker_url: str,
    tracker_human_id: str,
    tracker_title: str,
    machine: str,
    coding_agent: str,
    agent_session_id: str,
    task_folder: str,
    task_status_path: str,
    transcript_path: str,
    last_synced_at: str,
    workspace_path: str = TRACKER_KIND_NONE,
    zellij_session: str,
    zellij_link: str,
    remote_session_anchor_kind: str = TRACKER_KIND_NONE,
    remote_session_anchor_id: str = TRACKER_KIND_NONE,
    github_issue: str = TRACKER_KIND_NONE,
    github_repo: str = TRACKER_KIND_NONE,
    github_issue_number: str = TRACKER_KIND_NONE,
    linear_issue_id: str = TRACKER_KIND_NONE,
    linear_issue_identifier: str = TRACKER_KIND_NONE,
    linear_team_id: str = TRACKER_KIND_NONE,
    linear_team_name: str = TRACKER_KIND_NONE,
    linear_project_id: str = TRACKER_KIND_NONE,
    linear_project_name: str = TRACKER_KIND_NONE,
) -> str:
    values = normalize_task_metadata(
        {
            TASK_METADATA_FIELD_LABELS["tracker_kind"]: tracker_kind,
            TASK_METADATA_FIELD_LABELS["tracker_url"]: tracker_url,
            TASK_METADATA_FIELD_LABELS["tracker_human_id"]: tracker_human_id,
            TASK_METADATA_FIELD_LABELS["tracker_title"]: tracker_title,
            TASK_METADATA_FIELD_LABELS["machine"]: machine,
            TASK_METADATA_FIELD_LABELS["coding_agent"]: coding_agent,
            TASK_METADATA_FIELD_LABELS["agent_session_id"]: agent_session_id,
            TASK_METADATA_FIELD_LABELS["task_folder"]: task_folder,
            TASK_METADATA_FIELD_LABELS["task_status_path"]: task_status_path,
            TASK_METADATA_FIELD_LABELS["transcript_path"]: transcript_path,
            TASK_METADATA_FIELD_LABELS["last_synced_at"]: last_synced_at,
            TASK_METADATA_FIELD_LABELS["workspace_path"]: workspace_path,
            TASK_METADATA_FIELD_LABELS["zellij_session"]: zellij_session,
            TASK_METADATA_FIELD_LABELS["zellij_link"]: zellij_link,
            TASK_METADATA_FIELD_LABELS["remote_session_anchor_kind"]: remote_session_anchor_kind,
            TASK_METADATA_FIELD_LABELS["remote_session_anchor_id"]: remote_session_anchor_id,
            TASK_METADATA_FIELD_LABELS["github_issue"]: github_issue,
            TASK_METADATA_FIELD_LABELS["github_repo"]: github_repo,
            TASK_METADATA_FIELD_LABELS["github_issue_number"]: github_issue_number,
            TASK_METADATA_FIELD_LABELS["linear_issue_id"]: linear_issue_id,
            TASK_METADATA_FIELD_LABELS["linear_issue_identifier"]: linear_issue_identifier,
            TASK_METADATA_FIELD_LABELS["linear_team_id"]: linear_team_id,
            TASK_METADATA_FIELD_LABELS["linear_team_name"]: linear_team_name,
            TASK_METADATA_FIELD_LABELS["linear_project_id"]: linear_project_id,
            TASK_METADATA_FIELD_LABELS["linear_project_name"]: linear_project_name,
        }
    )
    lines = [
        TASK_METADATA_START,
        "## Task Metadata",
    ]
    for field_name in TASK_METADATA_RENDER_ORDER:
        label = TASK_METADATA_FIELD_LABELS[field_name]
        lines.append(f"- {label}: {values[field_name]}")
    lines.append(TASK_METADATA_END)
    return "\n".join(lines)


def build_github_authorship_byline(coding_agent: str) -> str | None:
    normalized = (coding_agent or "").strip().lower()
    if normalized == "codex":
        return "_Written by Codex via the developer's authenticated GitHub account._"
    if normalized == "claude":
        return "_Written by Claude Code via the developer's authenticated GitHub account._"
    return None


def build_live_session_block(
    *,
    machine: str,
    coding_agent: str,
    agent_session_id: str,
    zellij_session: str,
    zellij_link: str,
    task_dir: str,
    status_file: str,
    attach_command: str,
    last_updated: str,
    project_root: str | None = None,
    include_authorship_byline: bool = True,
) -> str:
    def plain_value(value: str) -> str:
        return (value or "none").replace("`", "").strip() or "none"

    authorship_byline = build_github_authorship_byline(coding_agent) if include_authorship_byline else None
    transcript_path = resolve_transcript_path(coding_agent, agent_session_id, project_root=project_root)
    lines = [
        LIVE_SESSION_START,
        "## Live Session",
    ]
    if authorship_byline:
        lines.extend(["", authorship_byline, ""])
    lines.extend(
        [
            f"- Machine: `{plain_value(machine)}`",
            f"- Coding Agent: `{plain_value(coding_agent)}`",
            f"- Agent Session ID: `{plain_value(agent_session_id)}`",
            f"- Transcript Path: `{plain_value(transcript_path)}`",
            f"- Zellij Session: `{plain_value(zellij_session)}`",
            f"- Zellij Link: {plain_value(zellij_link)}",
            f"- Task Folder: `{plain_value(task_dir)}`",
            f"- Status File: `{plain_value(status_file)}`",
            f"- Attach Command: `{plain_value(attach_command)}`",
            f"- Last Updated: `{plain_value(last_updated)}`",
            LIVE_SESSION_END,
        ]
    )
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


def _normalize_metadata_value(value: str | None, *, default: str = TRACKER_KIND_NONE) -> str:
    resolved = str(value or "").strip()
    if not resolved or resolved.lower() == TRACKER_KIND_NONE:
        return default
    return resolved


def _first_metadata_value(metadata: dict[str, str], *labels: str, default: str = TRACKER_KIND_NONE) -> str:
    for label in labels:
        resolved = _normalize_metadata_value(metadata.get(label), default="")
        if resolved:
            return resolved
    return default


def _normalize_tracker_kind(value: str | None) -> str:
    normalized = _normalize_metadata_value(value).lower()
    if normalized in {TRACKER_KIND_GITHUB, TRACKER_KIND_LINEAR}:
        return normalized
    return TRACKER_KIND_NONE


def _github_human_id_from_metadata(metadata: dict[str, str]) -> str:
    issue_url = _first_metadata_value(metadata, "GitHub Issue")
    issue_ref = parse_github_issue_url(issue_url) if issue_url != TRACKER_KIND_NONE else None
    if issue_ref:
        return f"{issue_ref.repo_key}#{issue_ref.number}"

    repo = _first_metadata_value(metadata, "GitHub Repo")
    number = _first_metadata_value(metadata, "GitHub Issue Number")
    if repo != TRACKER_KIND_NONE and number != TRACKER_KIND_NONE:
        return f"{repo}#{number}"
    return TRACKER_KIND_NONE


def normalize_task_metadata(
    metadata: dict[str, str] | None,
    *,
    status_file: Path | None = None,
    hydrate_transcript_path: bool = False,
) -> dict[str, str]:
    raw = metadata or {}
    tracker_url = _first_metadata_value(raw, "Tracker URL", "GitHub Issue")
    tracker_ref = parse_tracker_url(tracker_url) if tracker_url != TRACKER_KIND_NONE else None

    tracker_kind = _normalize_tracker_kind(_first_metadata_value(raw, "Tracker Kind"))
    if tracker_kind == TRACKER_KIND_NONE and tracker_ref:
        tracker_kind = tracker_ref.kind
    if tracker_kind == TRACKER_KIND_NONE and _first_metadata_value(raw, "Linear Issue Identifier", "Linear Issue ID") != TRACKER_KIND_NONE:
        tracker_kind = TRACKER_KIND_LINEAR
    if tracker_kind == TRACKER_KIND_NONE and _first_metadata_value(raw, "GitHub Issue", "GitHub Repo", "GitHub Issue Number") != TRACKER_KIND_NONE:
        tracker_kind = TRACKER_KIND_GITHUB

    tracker_human_id = _first_metadata_value(raw, "Tracker Human ID", "Linear Issue Identifier")
    if tracker_human_id == TRACKER_KIND_NONE and tracker_ref:
        tracker_human_id = tracker_ref.human_id
    if tracker_human_id == TRACKER_KIND_NONE and tracker_kind == TRACKER_KIND_GITHUB:
        tracker_human_id = _github_human_id_from_metadata(raw)

    tracker_title = _first_metadata_value(raw, "Tracker Title")
    if tracker_title == TRACKER_KIND_NONE and tracker_ref and tracker_ref.title_slug:
        tracker_title = humanize_slug(tracker_ref.title_slug)

    resolved_task_folder = _first_metadata_value(raw, "Task Folder")
    resolved_status_path = _first_metadata_value(raw, "Task Status Path")
    if status_file:
        resolved_task_folder = (
            resolved_task_folder
            if resolved_task_folder != TRACKER_KIND_NONE
            else str(status_file.parent.resolve())
        )
        resolved_status_path = (
            resolved_status_path
            if resolved_status_path != TRACKER_KIND_NONE
            else str(status_file.resolve())
        )

    workspace_path = _first_metadata_value(raw, "Workspace Path")
    if workspace_path == TRACKER_KIND_NONE and status_file:
        project_root = infer_project_root_from_path(status_file)
        if project_root:
            workspace_path = str(project_root)

    transcript_path = _first_metadata_value(raw, "Transcript Path")
    if transcript_path == TRACKER_KIND_NONE and hydrate_transcript_path:
        transcript_path = resolve_transcript_path(
            _first_metadata_value(raw, "Coding Agent"),
            _first_metadata_value(raw, "Agent Session ID"),
            project_root=workspace_path if workspace_path != TRACKER_KIND_NONE else None,
        )

    github_issue = _first_metadata_value(raw, "GitHub Issue")
    github_repo = _first_metadata_value(raw, "GitHub Repo")
    github_issue_number = _first_metadata_value(raw, "GitHub Issue Number")
    if github_issue == TRACKER_KIND_NONE and tracker_kind == TRACKER_KIND_GITHUB and tracker_ref:
        github_issue = tracker_ref.url
    if github_repo == TRACKER_KIND_NONE and tracker_kind == TRACKER_KIND_GITHUB and tracker_ref and tracker_ref.github_issue:
        github_repo = tracker_ref.github_issue.repo_key
    if (
        github_issue_number == TRACKER_KIND_NONE
        and tracker_kind == TRACKER_KIND_GITHUB
        and tracker_ref
        and tracker_ref.github_issue
    ):
        github_issue_number = str(tracker_ref.github_issue.number)

    linear_issue_id = _first_metadata_value(raw, "Linear Issue ID")
    linear_issue_identifier = _first_metadata_value(raw, "Linear Issue Identifier")
    if linear_issue_identifier == TRACKER_KIND_NONE and tracker_kind == TRACKER_KIND_LINEAR and tracker_ref:
        linear_issue_identifier = tracker_ref.human_id

    normalized = {
        "tracker_kind": tracker_kind,
        "tracker_url": tracker_url,
        "tracker_human_id": tracker_human_id,
        "tracker_title": tracker_title,
        "machine": _first_metadata_value(raw, "Machine"),
        "coding_agent": _first_metadata_value(raw, "Coding Agent"),
        "agent_session_id": _first_metadata_value(raw, "Agent Session ID"),
        "task_folder": resolved_task_folder,
        "task_status_path": resolved_status_path,
        "transcript_path": transcript_path,
        "last_synced_at": _first_metadata_value(raw, "Last Synced", "Last Synced At"),
        "workspace_path": workspace_path,
        "zellij_session": _first_metadata_value(raw, "Zellij Session"),
        "zellij_link": _first_metadata_value(raw, "Zellij Link"),
        "remote_session_anchor_kind": _first_metadata_value(raw, "Remote Session Anchor Kind"),
        "remote_session_anchor_id": _first_metadata_value(raw, "Remote Session Anchor ID"),
        "github_issue": github_issue,
        "github_repo": github_repo,
        "github_issue_number": github_issue_number,
        "linear_issue_id": linear_issue_id,
        "linear_issue_identifier": linear_issue_identifier,
        "linear_team_id": _first_metadata_value(raw, "Linear Team ID"),
        "linear_team_name": _first_metadata_value(raw, "Linear Team Name"),
        "linear_project_id": _first_metadata_value(raw, "Linear Project ID"),
        "linear_project_name": _first_metadata_value(raw, "Linear Project Name"),
    }
    return normalized


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


def normalize_markdown_heading(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower()).strip()


def heading_matches(heading: str, target: str) -> bool:
    return heading == target or heading.startswith(f"{target} ")


def clean_summary_text(text: str) -> str:
    value = text.strip()
    if not value:
        return ""
    value = MARKDOWN_LINK_RE.sub(r"\1", value)
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value)
    value = re.sub(r"__(.*?)__", r"\1", value)
    value = re.sub(r"\*(.*?)\*", r"\1", value)
    value = re.sub(r"_(.*?)_", r"\1", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_markdown_title(text: str) -> str | None:
    in_code_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        match = ATX_HEADING_RE.match(stripped)
        if not match or len(match.group("hashes")) != 1:
            continue
        title = clean_summary_text(match.group("title"))
        if title:
            return title
    return None


def extract_markdown_inline_field(text: str, field_name: str) -> str | None:
    pattern = re.compile(rf"^\*\*{re.escape(field_name)}\*\*:\s*(?P<value>.+?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    value = clean_summary_text(match.group("value"))
    return value or None


def extract_markdown_section(text: str, headings: Iterable[str]) -> str | None:
    targets = [normalize_markdown_heading(heading) for heading in headings if heading]
    if not targets:
        return None

    capture = False
    capture_level = 0
    in_code_block = False
    captured: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if capture:
                captured.append(line)
            continue
        if in_code_block:
            if capture:
                captured.append(line)
            continue

        match = ATX_HEADING_RE.match(stripped)
        if match:
            level = len(match.group("hashes"))
            heading = normalize_markdown_heading(match.group("title"))
            if capture and level <= capture_level:
                break
            if not capture and any(heading_matches(heading, target) for target in targets):
                capture = True
                capture_level = level
                continue

        if capture:
            captured.append(line)

    section_text = "\n".join(captured).strip()
    return section_text or None


def collect_markdown_items(section_text: str | None) -> list[str]:
    if not section_text:
        return []

    items: list[str] = []
    in_code_block = False
    in_comment_block = False

    for raw_line in section_text.splitlines():
        stripped = raw_line.strip()
        if in_comment_block:
            if "-->" in stripped:
                in_comment_block = False
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment_block = True
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not stripped:
            continue
        if stripped in {"---", "***"} or stripped.startswith("|"):
            continue

        text = BULLET_PREFIX_RE.sub("", stripped)
        text = NUMBERED_PREFIX_RE.sub("", text)
        text = clean_summary_text(text)
        if text:
            items.append(text)

    return items


def ensure_sentence(text: str) -> str:
    value = clean_summary_text(text)
    if not value:
        return ""
    if value.endswith((".", "!", "?", "…")):
        return value
    return f"{value}."


def truncate_summary(text: str, *, max_chars: int = 240) -> str:
    value = clean_summary_text(text)
    if len(value) <= max_chars:
        return value
    clipped = value[: max_chars - 3].rsplit(" ", 1)[0].strip()
    if not clipped:
        clipped = value[: max_chars - 3].strip()
    return f"{clipped}..."


def build_task_recap(status_file: Path | None) -> list[str]:
    if not status_file or not status_file.is_file():
        return [
            "What this task is about: Task summary is not available yet.",
            "Current status: Current status is not recorded yet.",
            "Next steps: Add or update the task status file before relying on this recap.",
        ]

    text = read_text(status_file)
    title = extract_markdown_title(text)
    goal = extract_markdown_inline_field(text, "Goal")
    status = extract_markdown_inline_field(text, "Status")
    current_items = collect_markdown_items(extract_markdown_section(text, ["Current State"]))
    next_items = collect_markdown_items(extract_markdown_section(text, ["Next Steps"]))

    about_value = goal or title or (current_items[0] if current_items else "Task summary is not available yet")
    current_value = status or (
        " ".join(current_items[:2]) if current_items else "Current status is not recorded yet"
    )
    next_value = (
        " ".join(next_items[:2])
        if next_items
        else "Review the status file and add the next steps if this task needs a fresh handoff."
    )

    return [
        f"What this task is about: {truncate_summary(ensure_sentence(about_value))}",
        f"Current status: {truncate_summary(ensure_sentence(current_value))}",
        f"Next steps: {truncate_summary(ensure_sentence(next_value))}",
    ]


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


def local_project_roots(current_project_root: Path | None = None) -> list[Path]:
    matches: list[Path] = []
    seen: set[Path] = set()

    def maybe_add(candidate: Path) -> None:
        resolved = candidate.expanduser().resolve()
        project_root = infer_project_root_from_path(resolved) or resolved
        project_root = project_root.expanduser().resolve()
        if project_root in seen or not project_root.is_dir():
            return
        if not (
            (project_root / "AGENTS.md").is_file()
            or (project_root / "CLAUDE.md").is_file()
            or (project_root / ".botrc").is_file()
            or (project_root / ".git").exists()
        ):
            return
        seen.add(project_root)
        matches.append(project_root)

    if current_project_root:
        maybe_add(current_project_root)

    for search_root in local_repo_search_roots(current_project_root):
        for child in sorted(search_root.iterdir()):
            if not child.is_dir():
                continue
            maybe_add(child)

    return matches


def task_candidate_matches_tracker(candidate: TaskCandidate, tracker_ref: TrackerRef) -> bool:
    metadata = normalize_task_metadata(candidate.metadata, status_file=candidate.status_file)
    tracker_url = metadata.get("tracker_url", TRACKER_KIND_NONE).strip().lower()
    if tracker_url and tracker_url != TRACKER_KIND_NONE and tracker_url == tracker_ref.url.lower():
        return True

    if metadata.get("tracker_kind", TRACKER_KIND_NONE).strip().lower() != tracker_ref.kind.lower():
        return False

    tracker_human_id = metadata.get("tracker_human_id", TRACKER_KIND_NONE).strip().lower()
    if tracker_human_id and tracker_human_id != TRACKER_KIND_NONE and tracker_human_id == tracker_ref.human_id.lower():
        return True

    if tracker_ref.kind == TRACKER_KIND_GITHUB and tracker_ref.github_issue:
        github_issue = metadata.get("github_issue", TRACKER_KIND_NONE).strip().lower()
        if github_issue and github_issue != TRACKER_KIND_NONE and github_issue == tracker_ref.github_issue.url.lower():
            return True
        github_repo = metadata.get("github_repo", TRACKER_KIND_NONE).strip().lower()
        github_issue_number = metadata.get("github_issue_number", TRACKER_KIND_NONE).strip()
        return github_repo == tracker_ref.github_issue.repo_key.lower() and github_issue_number == str(
            tracker_ref.github_issue.number
        )

    if tracker_ref.kind == TRACKER_KIND_LINEAR and tracker_ref.linear_issue:
        linear_issue_identifier = metadata.get("linear_issue_identifier", TRACKER_KIND_NONE).strip().lower()
        return (
            linear_issue_identifier
            and linear_issue_identifier != TRACKER_KIND_NONE
            and linear_issue_identifier == tracker_ref.linear_issue.identifier.lower()
        )

    return False


def find_local_task_homes_for_tracker(
    tracker_ref: TrackerRef,
    *,
    current_project_root: Path | None = None,
    caller_path: Path | None = None,
) -> list[TrackerTaskHome]:
    matches: list[TrackerTaskHome] = []
    for project_root in local_project_roots(current_project_root):
        task_status_root = resolve_task_status_root(project_root, caller_path=caller_path)
        candidates = sort_task_candidates_by_recency(load_task_candidates(task_status_root))
        for candidate in candidates:
            if not task_candidate_matches_tracker(candidate, tracker_ref):
                continue
            matches.append(
                TrackerTaskHome(
                    project_root=project_root,
                    task_status_root=task_status_root,
                    candidate=candidate,
                )
            )
            break
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
    normalized_metadata = normalize_task_metadata(candidate.metadata, status_file=candidate.status_file)
    last_synced = parse_pst_label(normalized_metadata.get("last_synced_at", ""))
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


def parse_session_task_key(key: str) -> tuple[Path | None, str, str]:
    parts = key.rsplit("::", 2)
    if len(parts) != 3:
        return None, "", ""

    project_root_raw, coding_agent, agent_session_id = parts
    project_root = None
    if project_root_raw.strip():
        try:
            project_root = Path(project_root_raw).expanduser().resolve()
        except Exception:
            project_root = None

    return project_root, coding_agent.strip(), agent_session_id.strip()


def _resolve_optional_path(raw_value: object) -> Path | None:
    value = str(raw_value or "").strip()
    if not value or value.lower() == TRACKER_KIND_NONE:
        return None
    try:
        return Path(value).expanduser().resolve()
    except Exception:
        return None


def _parse_current_task_pointer(
    raw: dict[str, object],
    *,
    fallback_project_root: Path | None = None,
) -> CurrentTaskPointer | None:
    task_dir = _resolve_optional_path(raw.get("task_dir"))
    status_file = _resolve_optional_path(raw.get("status_file"))
    task_label = str(raw.get("task_label", "")).strip()
    updated_at = str(raw.get("updated_at", "")).strip()
    project_root = _resolve_optional_path(raw.get("project_root")) or fallback_project_root
    workspace_path = _resolve_optional_path(raw.get("workspace_path"))

    if not task_dir or not status_file:
        return None
    if not task_dir.is_dir() or not status_file.is_file():
        return None
    if not project_root:
        project_root = infer_project_root_from_path(status_file) or infer_project_root_from_path(task_dir)
    if not project_root:
        return None

    return CurrentTaskPointer(
        project_root=project_root.resolve(),
        workspace_path=workspace_path,
        task_dir=task_dir,
        status_file=status_file,
        task_label=task_label or extract_full_task_folder_slug(task_dir.name),
        updated_at=updated_at,
    )


def _current_task_pointer_rank(
    pointer: CurrentTaskPointer,
    *,
    requested_project_root: Path,
) -> tuple[int, datetime, int, int]:
    updated_at = parse_pst_label(pointer.updated_at) or datetime.fromtimestamp(
        0,
        tz=ZoneInfo("America/Los_Angeles"),
    )
    workspace_match = pointer.workspace_path == requested_project_root
    project_match = pointer.project_root == requested_project_root
    relevance = 1 if workspace_match or project_match else 0
    return (
        relevance,
        updated_at,
        1 if workspace_match else 0,
        1 if project_match else 0,
    )


def upsert_current_task_pointer(
    status_file: Path,
    *,
    coding_agent: str,
    agent_session_id: str,
    task_label: str | None = None,
    workspace_path: Path | str | None = None,
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
    resolved_workspace_path = _resolve_optional_path(workspace_path)
    entry = {
        "project_root": str(project_root),
        "workspace_path": str(resolved_workspace_path) if resolved_workspace_path else TRACKER_KIND_NONE,
        "coding_agent": coding_agent,
        "agent_session_id": agent_session_id,
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
    requested_project_root = project_root.resolve()
    candidates: list[CurrentTaskPointer] = []

    for key, raw in payload.items():
        if not isinstance(raw, dict):
            continue
        entry_project_root, entry_agent, entry_session_id = parse_session_task_key(key)
        raw_agent = str(raw.get("coding_agent", "")).strip() or entry_agent
        raw_session_id = str(raw.get("agent_session_id", "")).strip() or entry_session_id
        if raw_agent != coding_agent or raw_session_id != agent_session_id:
            continue
        pointer = _parse_current_task_pointer(
            raw,
            fallback_project_root=entry_project_root,
        )
        if pointer:
            candidates.append(pointer)

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda pointer: _current_task_pointer_rank(
            pointer,
            requested_project_root=requested_project_root,
        ),
    )


def non_tracker_urls(urls: Iterable[str], tracker_ref: TrackerRef | None) -> list[str]:
    if not tracker_ref:
        return list(urls)
    filtered: list[str] = []
    for url in urls:
        candidate = parse_tracker_url(url)
        if candidate and candidate.kind == tracker_ref.kind and candidate.human_id == tracker_ref.human_id:
            continue
        if url == tracker_ref.url:
            continue
        filtered.append(url)
    return filtered


def non_issue_urls(urls: Iterable[str], issue_ref: IssueRef | None) -> list[str]:
    if not issue_ref:
        return list(urls)
    tracker_ref = TrackerRef(
        kind=TRACKER_KIND_GITHUB,
        url=issue_ref.url,
        human_id=f"{issue_ref.repo_key}#{issue_ref.number}",
        github_issue=issue_ref,
    )
    return non_tracker_urls(urls, tracker_ref)
