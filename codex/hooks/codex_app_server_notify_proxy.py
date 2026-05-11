#!/usr/bin/env python3
"""
Proxy Codex App Server WebSocket traffic and notify on request_user_input.

The proxy is intentionally transparent: all frames are forwarded unchanged.
Only server-to-client `item/tool/requestUserInput` frames produce notifications.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import websockets


_UTILS_DIR = Path(__file__).resolve().parents[2] / "utils"
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

from notify_utils import _log, send_notification  # noqa: E402


DEFAULT_STATE_DIR = Path(
    os.getenv(
        "CODEX_APP_NOTIFY_STATE_DIR",
        str(Path.home() / ".cache" / "botfiles" / "codex-app-server-notify"),
    )
).expanduser()
DEFAULT_LISTEN = f"ws://127.0.0.1:{os.getenv('CODEX_APP_NOTIFY_PROXY_PORT', '17371')}"
DEFAULT_UPSTREAM = os.getenv(
    "CODEX_APP_NOTIFY_UPSTREAM",
    f"ws://127.0.0.1:{os.getenv('CODEX_APP_SERVER_PORT', '17370')}",
)
STATE_SCHEMA_VERSION = 1
MAX_SEEN_REQUESTS = 500
MAX_STATE_AGE_SECONDS = 7 * 24 * 60 * 60


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_bool(value: str | bool | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def json_dumps(data: Any) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def decode_json_frame(message: Any) -> dict[str, Any] | None:
    if not isinstance(message, str):
        return None
    try:
        payload = json.loads(message)
    except (TypeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _short(value: str, length: int = 8) -> str:
    return value[:length] if value else "none"


def _request_id_from_payload(payload: dict[str, Any]) -> Any:
    params = payload.get("params")
    if isinstance(params, dict) and "requestId" in params:
        return params.get("requestId")
    return payload.get("id")


@dataclass(frozen=True)
class RequestUserInputEvent:
    request_id: Any
    thread_id: str
    turn_id: str
    item_id: str
    questions: list[dict[str, Any]]
    cwd: str = ""

    @property
    def dedupe_key(self) -> str:
        return "|".join(
            [
                self.thread_id,
                self.turn_id,
                self.item_id,
                str(self.request_id),
            ]
        )


@dataclass
class ThreadContext:
    cwd_by_thread: dict[str, str] = field(default_factory=dict)
    pending_start_cwd_by_request_id: dict[str, str] = field(default_factory=dict)
    owned_thread_ids: set[str] = field(default_factory=set)

    def note_client_request(self, payload: dict[str, Any]) -> None:
        method = payload.get("method")
        params = payload.get("params")
        if not isinstance(params, dict):
            return

        if method in {"thread/start", "thread/resume", "thread/fork"}:
            cwd = _string_value(params.get("cwd"))
            request_id = _string_value(payload.get("id"))
            thread_id = _string_value(params.get("threadId"))
            if thread_id:
                self.owned_thread_ids.add(thread_id)
                if cwd:
                    self.cwd_by_thread[thread_id] = cwd
            if cwd and request_id:
                self.pending_start_cwd_by_request_id[request_id] = cwd
            return

        if method == "turn/start":
            thread_id = _string_value(params.get("threadId"))
            cwd = _string_value(params.get("cwd"))
            if thread_id:
                self.owned_thread_ids.add(thread_id)
                if cwd:
                    self.cwd_by_thread[thread_id] = cwd

    def note_server_payload(self, payload: dict[str, Any]) -> None:
        method = payload.get("method")
        params = payload.get("params")
        if not isinstance(params, dict):
            return

        if method == "thread/started":
            thread = params.get("thread")
            if isinstance(thread, dict):
                thread_id = _string_value(thread.get("id"))
                cwd = _string_value(thread.get("cwd"))
                if thread_id and cwd:
                    self.cwd_by_thread[thread_id] = cwd
                    if self.pending_start_cwd_by_request_id:
                        self.owned_thread_ids.add(thread_id)
                        self.pending_start_cwd_by_request_id.pop(
                            next(iter(self.pending_start_cwd_by_request_id)),
                            None,
                        )
                    return

            thread_id = _string_value(params.get("threadId"))
            cwd = _string_value(params.get("cwd"))
            if thread_id and cwd:
                self.cwd_by_thread[thread_id] = cwd
                if self.pending_start_cwd_by_request_id:
                    self.owned_thread_ids.add(thread_id)
                    self.pending_start_cwd_by_request_id.pop(
                        next(iter(self.pending_start_cwd_by_request_id)),
                        None,
                    )
                return

            request_id = _string_value(payload.get("id"))
            if request_id and thread_id and request_id in self.pending_start_cwd_by_request_id:
                self.cwd_by_thread[thread_id] = self.pending_start_cwd_by_request_id[request_id]
                self.owned_thread_ids.add(thread_id)
                self.pending_start_cwd_by_request_id.pop(request_id, None)

        if method == "thread/status/changed":
            thread = params.get("thread")
            if isinstance(thread, dict):
                thread_id = _string_value(thread.get("id"))
                cwd = _string_value(thread.get("cwd"))
                if thread_id and cwd:
                    self.cwd_by_thread[thread_id] = cwd

    def cwd_for_thread(self, thread_id: str) -> str:
        return self.cwd_by_thread.get(thread_id, "")

    def owns_thread(self, thread_id: str) -> bool:
        return thread_id in self.owned_thread_ids

    def thread_ids(self) -> list[str]:
        return sorted(self.cwd_by_thread)


class JsonlLogger:
    def __init__(self, path: Path, *, verbose: bool = False) -> None:
        self.path = path
        self.verbose = verbose
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def write(self, event: dict[str, Any]) -> None:
        event = {"ts": utc_now(), **event}
        line = json.dumps(event, sort_keys=True, ensure_ascii=False)
        async with self._lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        if self.verbose:
            print(line, flush=True)


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text())
        except Exception:
            return self._empty()
        if not isinstance(data, dict):
            return self._empty()
        data.setdefault("schema_version", STATE_SCHEMA_VERSION)
        data.setdefault("seen_requests", {})
        data.setdefault("pending_requests", {})
        if not isinstance(data["seen_requests"], dict):
            data["seen_requests"] = {}
        if not isinstance(data["pending_requests"], dict):
            data["pending_requests"] = {}
        return data

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {
            "schema_version": STATE_SCHEMA_VERSION,
            "seen_requests": {},
            "pending_requests": {},
        }

    def _save_unlocked(self) -> None:
        self._prune_unlocked()
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n")
        tmp_path.replace(self.path)

    def _prune_unlocked(self) -> None:
        now = time.time()
        seen = self.data.get("seen_requests", {})
        if isinstance(seen, dict):
            keep_items: list[tuple[str, dict[str, Any]]] = []
            for key, record in seen.items():
                if not isinstance(record, dict):
                    continue
                first_seen = float(record.get("first_seen_epoch", now))
                if now - first_seen <= MAX_STATE_AGE_SECONDS:
                    keep_items.append((str(key), record))
            keep_items.sort(key=lambda item: float(item[1].get("first_seen_epoch", 0)))
            self.data["seen_requests"] = dict(keep_items[-MAX_SEEN_REQUESTS:])

    async def mark_request_seen(self, event: RequestUserInputEvent) -> bool:
        async with self._lock:
            seen = self.data.setdefault("seen_requests", {})
            pending = self.data.setdefault("pending_requests", {})
            duplicate = event.dedupe_key in seen
            if not duplicate:
                now = time.time()
                record = {
                    "first_seen_at": utc_now(),
                    "first_seen_epoch": now,
                    "thread_id": event.thread_id,
                    "turn_id": event.turn_id,
                    "item_id": event.item_id,
                    "request_id": event.request_id,
                    "cwd": event.cwd,
                }
                seen[event.dedupe_key] = record
                pending[event.dedupe_key] = record
                self._save_unlocked()
            return duplicate

    async def clear_resolved(self, *, thread_id: str, request_id: Any, reason: str) -> list[str]:
        async with self._lock:
            pending = self.data.setdefault("pending_requests", {})
            cleared: list[str] = []
            for key, record in list(pending.items()):
                if not isinstance(record, dict):
                    continue
                if _string_value(record.get("thread_id")) != thread_id:
                    continue
                if str(record.get("request_id")) != str(request_id):
                    continue
                cleared.append(str(key))
                pending.pop(key, None)
            if cleared:
                self.data["last_resolved_at"] = utc_now()
                self.data["last_resolved_reason"] = reason
                self._save_unlocked()
            return cleared

    async def cleanup_thread_turn(
        self,
        *,
        thread_id: str,
        turn_id: str | None = None,
        reason: str,
    ) -> list[str]:
        async with self._lock:
            pending = self.data.setdefault("pending_requests", {})
            cleared: list[str] = []
            for key, record in list(pending.items()):
                if not isinstance(record, dict):
                    continue
                if thread_id and _string_value(record.get("thread_id")) != thread_id:
                    continue
                if turn_id and _string_value(record.get("turn_id")) != turn_id:
                    continue
                cleared.append(str(key))
                pending.pop(key, None)
            if cleared:
                self.data["last_cleanup_at"] = utc_now()
                self.data["last_cleanup_reason"] = reason
                self._save_unlocked()
            return cleared


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "null"}:
        return ""
    return text


def summarize_message(message: Any) -> dict[str, Any]:
    if isinstance(message, bytes):
        return {"kind": "bytes", "bytes": len(message), "json": False}
    if not isinstance(message, str):
        return {"kind": type(message).__name__, "bytes": 0, "json": False}

    summary: dict[str, Any] = {
        "kind": "text",
        "bytes": len(message),
        "json": False,
    }
    payload = decode_json_frame(message)
    if not payload:
        return summary

    summary["json"] = True
    summary["method"] = payload.get("method")
    if "id" in payload:
        summary["id"] = payload.get("id")
    params = payload.get("params")
    if isinstance(params, dict):
        for key in ("threadId", "turnId", "itemId", "requestId"):
            if key in params:
                summary[key] = params[key]
        thread = params.get("thread")
        if isinstance(thread, dict):
            thread_id = thread.get("id")
            if thread_id:
                summary["threadId"] = thread_id
    return summary


def parse_request_user_input(
    payload: dict[str, Any],
    *,
    context: ThreadContext | None = None,
) -> RequestUserInputEvent | None:
    if payload.get("method") != "item/tool/requestUserInput":
        return None
    params = payload.get("params")
    if not isinstance(params, dict):
        return None

    thread_id = _string_value(params.get("threadId"))
    turn_id = _string_value(params.get("turnId"))
    item_id = _string_value(params.get("itemId"))
    if not thread_id or not turn_id or not item_id:
        return None

    questions = params.get("questions")
    if not isinstance(questions, list):
        questions = []

    cwd = context.cwd_for_thread(thread_id) if context else ""
    return RequestUserInputEvent(
        request_id=_request_id_from_payload(payload),
        thread_id=thread_id,
        turn_id=turn_id,
        item_id=item_id,
        questions=[question for question in questions if isinstance(question, dict)],
        cwd=cwd,
    )


def first_question_summary(event: RequestUserInputEvent) -> dict[str, Any]:
    first = event.questions[0] if event.questions else {}
    options = first.get("options") if isinstance(first, dict) else None
    labels: list[str] = []
    recommended = ""
    if isinstance(options, list):
        for option in options:
            if not isinstance(option, dict):
                continue
            label = _string_value(option.get("label"))
            if label:
                labels.append(label)
            if parse_bool(option.get("recommended"), default=False):
                recommended = label
            if not recommended and "recommended" in label.lower():
                recommended = label
    return {
        "question_count": len(event.questions),
        "first_question_id": first.get("id") if isinstance(first, dict) else None,
        "first_question_header": first.get("header") if isinstance(first, dict) else None,
        "first_question": first.get("question") if isinstance(first, dict) else None,
        "option_count": len(labels),
        "recommended_option": recommended or (labels[0] if labels else ""),
    }


def build_notification_message(event: RequestUserInputEvent) -> str:
    summary = first_question_summary(event)
    question_header = _string_value(summary.get("first_question_header"))
    question_text = _string_value(summary.get("first_question"))
    question_count = int(summary.get("question_count") or 0)
    recommended = _string_value(summary.get("recommended_option"))

    lines = ["Awaiting Your Input"]
    if question_text:
        prefix = f"Question 1/{question_count}" if question_count else "Question"
        if question_header:
            lines.append(f"{prefix} - {question_header}: {question_text}")
        else:
            lines.append(f"{prefix}: {question_text}")
    elif question_header:
        lines.append(f"Question: {question_header}")
    else:
        lines.append("Codex is waiting for a request_user_input response.")

    if recommended:
        lines.append(f"Suggested: {recommended}")

    lines.extend(
        [
            f"Thread: {_short(event.thread_id)}",
            f"Turn: {_short(event.turn_id)}",
            f"Item: {_short(event.item_id)}",
        ]
    )
    if event.cwd:
        lines.append(f"Cwd: {event.cwd}")
    return "\n".join(lines)


async def send_request_user_input_notification(
    event: RequestUserInputEvent,
    *,
    logger: JsonlLogger,
    dry_run: bool,
) -> None:
    message = build_notification_message(event)
    await logger.write(
        {
            "event": "notification_attempt",
            "dry_run": dry_run,
            "thread_id": event.thread_id,
            "turn_id": event.turn_id,
            "item_id": event.item_id,
            "request_id": event.request_id,
        }
    )

    try:
        if dry_run:
            _log(
                "Codex App Server request_user_input dry-run: "
                f"thread_id={event.thread_id}, turn_id={event.turn_id}, item_id={event.item_id}"
            )
            return

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: send_notification(
                title="Codex Needs Input",
                message=message,
                send_local=False,
                agent_session_id_override=event.thread_id,
                coding_agent_override="codex",
                working_directory_override=event.cwd or Path.cwd(),
            ),
        )
        await logger.write(
            {
                "event": "notification_completed",
                "thread_id": event.thread_id,
                "turn_id": event.turn_id,
                "item_id": event.item_id,
                "request_id": event.request_id,
            }
        )
    except Exception as exc:
        _log(f"Codex App Server request_user_input notification failed: {exc!r}")
        await logger.write(
            {
                "event": "notification_error",
                "thread_id": event.thread_id,
                "turn_id": event.turn_id,
                "item_id": event.item_id,
                "request_id": event.request_id,
                "error": repr(exc),
            }
        )


async def handle_server_payload(
    payload: dict[str, Any],
    *,
    context: ThreadContext,
    state: StateStore,
    logger: JsonlLogger,
    notification_tasks: set[asyncio.Task[Any]],
    dry_run: bool,
) -> None:
    context.note_server_payload(payload)
    method = payload.get("method")

    event = parse_request_user_input(payload, context=context)
    if event:
        if not context.owns_thread(event.thread_id):
            await logger.write(
                {
                    "event": "request_user_input_ignored",
                    "reason": "unowned_thread",
                    "request_id": event.request_id,
                    "thread_id": event.thread_id,
                    "turn_id": event.turn_id,
                    "item_id": event.item_id,
                    "cwd": event.cwd,
                    **first_question_summary(event),
                }
            )
            return

        duplicate = await state.mark_request_seen(event)
        await logger.write(
            {
                "event": "request_user_input",
                "duplicate": duplicate,
                "request_id": event.request_id,
                "thread_id": event.thread_id,
                "turn_id": event.turn_id,
                "item_id": event.item_id,
                "cwd": event.cwd,
                **first_question_summary(event),
            }
        )
        if not duplicate:
            task = asyncio.create_task(
                send_request_user_input_notification(
                    event,
                    logger=logger,
                    dry_run=dry_run,
                )
            )
            notification_tasks.add(task)
            task.add_done_callback(notification_tasks.discard)
        return

    params = payload.get("params")
    if not isinstance(params, dict):
        return

    if method == "serverRequest/resolved":
        thread_id = _string_value(params.get("threadId"))
        request_id = params.get("requestId")
        cleared = await state.clear_resolved(
            thread_id=thread_id,
            request_id=request_id,
            reason="serverRequest/resolved",
        )
        if cleared:
            await logger.write(
                {
                    "event": "request_user_input_resolved",
                    "thread_id": thread_id,
                    "request_id": request_id,
                    "cleared": cleared,
                }
            )
        return

    if method in {"turn/completed", "turn/interrupt", "thread/closed"}:
        thread_id = _string_value(params.get("threadId"))
        turn_id = _string_value(params.get("turnId"))
        cleared = await state.cleanup_thread_turn(
            thread_id=thread_id,
            turn_id=turn_id or None,
            reason=str(method),
        )
        if cleared:
            await logger.write(
                {
                    "event": "request_user_input_cleanup",
                    "method": method,
                    "thread_id": thread_id,
                    "turn_id": turn_id,
                    "cleared": cleared,
                }
            )


async def forward_messages(
    *,
    direction: str,
    source: Any,
    target: Any,
    context: ThreadContext,
    state: StateStore,
    logger: JsonlLogger,
    notification_tasks: set[asyncio.Task[Any]],
    dry_run: bool,
) -> None:
    async for message in source:
        payload = decode_json_frame(message)
        if payload and direction == "client_to_server":
            context.note_client_request(payload)

        if payload and direction == "server_to_client":
            await handle_server_payload(
                payload,
                context=context,
                state=state,
                logger=logger,
                notification_tasks=notification_tasks,
                dry_run=dry_run,
            )

        await logger.write({"event": "frame", "direction": direction, **summarize_message(message)})
        await target.send(message)


async def proxy_connection(
    client_ws: Any,
    *,
    upstream_url: str,
    state: StateStore,
    logger: JsonlLogger,
    dry_run: bool,
    notification_tasks: set[asyncio.Task[Any]],
) -> None:
    connection_id = f"conn-{int(time.time() * 1000)}"
    context = ThreadContext()
    await logger.write(
        {
            "event": "connection_started",
            "connection_id": connection_id,
            "upstream_url": upstream_url,
        }
    )
    try:
        async with websockets.connect(upstream_url, max_size=None) as upstream_ws:
            await asyncio.gather(
                forward_messages(
                    direction="client_to_server",
                    source=client_ws,
                    target=upstream_ws,
                    context=context,
                    state=state,
                    logger=logger,
                    notification_tasks=notification_tasks,
                    dry_run=dry_run,
                ),
                forward_messages(
                    direction="server_to_client",
                    source=upstream_ws,
                    target=client_ws,
                    context=context,
                    state=state,
                    logger=logger,
                    notification_tasks=notification_tasks,
                    dry_run=dry_run,
                ),
            )
    except Exception as exc:
        await logger.write(
            {
                "event": "connection_error",
                "connection_id": connection_id,
                "error": repr(exc),
            }
        )
        raise
    finally:
        for thread_id in context.thread_ids():
            await state.cleanup_thread_turn(thread_id=thread_id, reason="connection_closed")
        await logger.write({"event": "connection_closed", "connection_id": connection_id})


def parse_listen_url(listen_url: str) -> tuple[str, int]:
    if not listen_url.startswith("ws://"):
        raise ValueError("Only ws:// listen URLs are supported")
    host_port = listen_url[len("ws://") :].split("/", 1)[0]
    if ":" not in host_port:
        raise ValueError("Listen URL must include host and port")
    host, raw_port = host_port.rsplit(":", 1)
    return host, int(raw_port)


async def run(args: argparse.Namespace) -> int:
    host, port = parse_listen_url(args.listen)
    logger = JsonlLogger(Path(args.event_log).expanduser(), verbose=args.verbose)
    state = StateStore(Path(args.state_path).expanduser())
    notification_tasks: set[asyncio.Task[Any]] = set()

    await logger.write(
        {
            "event": "proxy_starting",
            "listen": args.listen,
            "upstream": args.upstream,
            "dry_run": args.dry_run,
            "state_path": str(state.path),
        }
    )

    if args.once_until_ready:
        async with websockets.serve(lambda *_: None, host, port, max_size=None):
            await logger.write({"event": "proxy_ready", "listen": args.listen})
            print(args.listen)
            return 0

    async def handler(*handler_args: Any) -> None:
        client_ws = handler_args[0]
        await proxy_connection(
            client_ws,
            upstream_url=args.upstream,
            state=state,
            logger=logger,
            dry_run=args.dry_run,
            notification_tasks=notification_tasks,
        )

    async with websockets.serve(handler, host, port, max_size=None):
        await logger.write({"event": "proxy_ready", "listen": args.listen})
        print(f"Codex App Server notify proxy listening on {args.listen}", flush=True)
        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        finally:
            if notification_tasks:
                await asyncio.gather(*notification_tasks, return_exceptions=True)
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Proxy Codex App Server WebSocket traffic and notify on request_user_input.",
    )
    parser.add_argument("--listen", default=DEFAULT_LISTEN, help="Local ws:// listen URL")
    parser.add_argument("--upstream", default=DEFAULT_UPSTREAM, help="Upstream app-server ws:// URL")
    parser.add_argument(
        "--state-path",
        default=str(DEFAULT_STATE_DIR / "state.json"),
        help="Persistent dedupe/pending state JSON path",
    )
    parser.add_argument(
        "--event-log",
        default=str(DEFAULT_STATE_DIR / "events.jsonl"),
        help="Sanitized JSONL event log path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=parse_bool(os.getenv("CODEX_APP_NOTIFY_DRY_RUN"), default=False),
        help="Log notification attempts without sending WhatsApp/Gmail",
    )
    parser.add_argument(
        "--once-until-ready",
        action="store_true",
        help="Bind the listener, print the URL, then exit",
    )
    parser.add_argument("--verbose", action="store_true", help="Mirror JSONL events to stdout")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
