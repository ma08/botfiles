#!/usr/bin/env python3
"""Verify Codex system/user layering without printing configuration values."""

from __future__ import annotations

import argparse
import json
import os
import selectors
import shutil
import stat
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any


REQUIRED_MCPS = {
    "exa",
    "figma",
    "linear",
    "notion",
    "openaiDeveloperDocs",
    "zotero",
}
REQUIRED_PLUGINS = {
    "sites@openai-bundled",
    "visualize@openai-bundled",
}
FORBIDDEN_PORTABLE_PREFIXES = {
    "apps",
    "desktop",
    "marketplaces",
    "memories",
    "notice",
    "projects",
    "shell_environment_policy",
    "tui.model_availability_nux",
}


def flatten(value: Any, prefix: tuple[str, ...] = ()) -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            result.update(flatten(child, (*prefix, str(key))))
        return result
    return {".".join(prefix): value}


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def run_json(command: list[str], *, cwd: Path, timeout: float) -> Any:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return json.loads(result.stdout)


def send_message(proc: subprocess.Popen[str], message: dict[str, Any]) -> None:
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
    proc.stdin.flush()


def read_response(
    proc: subprocess.Popen[str],
    response_id: int,
    timeout: float,
) -> dict[str, Any]:
    assert proc.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ)
    try:
        events = selector.select(timeout)
        while events:
            line = proc.stdout.readline()
            if not line:
                break
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                events = selector.select(timeout)
                continue
            if message.get("id") == response_id:
                return message
            events = selector.select(timeout)
    finally:
        selector.close()
    raise TimeoutError(f"app-server response {response_id} timed out")


def read_effective_config(
    codex: Path,
    cwd: Path,
    timeout: float,
) -> dict[str, Any]:
    proc = subprocess.Popen(
        [str(codex), "app-server"],
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    try:
        send_message(
            proc,
            {
                "method": "initialize",
                "id": 0,
                "params": {
                    "clientInfo": {
                        "name": "botfiles_config_verifier",
                        "title": "Botfiles Config Verifier",
                        "version": "1.0.0",
                    },
                    "capabilities": {"experimentalApi": True},
                },
            },
        )
        initialized = read_response(proc, 0, timeout)
        if initialized.get("error"):
            raise RuntimeError("Codex app-server initialize failed")

        send_message(proc, {"method": "initialized", "params": {}})
        send_message(
            proc,
            {
                "method": "config/read",
                "id": 1,
                "params": {"cwd": str(cwd), "includeLayers": True},
            },
        )
        response = read_response(proc, 1, timeout)
        if response.get("error"):
            raise RuntimeError("Codex app-server config/read failed")
        return response.get("result") or {}
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)


def source_type(origin: Any) -> str | None:
    if not isinstance(origin, dict):
        return None
    name = origin.get("name")
    if not isinstance(name, dict):
        return None
    value = name.get("type")
    return value if isinstance(value, str) else None


def portable_prefix_violation(key: str) -> bool:
    return any(key == prefix or key.startswith(f"{prefix}.") for prefix in FORBIDDEN_PORTABLE_PREFIXES)


def display_path(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(Path.home().resolve())
    except ValueError:
        return str(path)
    return f"~/{relative}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--machine", required=True)
    parser.add_argument("--codex", type=Path, default=None)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument(
        "--portable",
        type=Path,
        default=None,
        help="Defaults to <repo>/codex/config.system.toml",
    )
    parser.add_argument(
        "--user-config",
        type=Path,
        default=Path.home() / ".codex" / "config.toml",
    )
    parser.add_argument(
        "--system-config",
        type=Path,
        default=Path("/etc/codex/config.toml"),
    )
    parser.add_argument(
        "--allow-user-override",
        action="append",
        default=[],
        metavar="KEY_PATH",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    portable = (
        args.portable.expanduser().resolve()
        if args.portable
        else repo / "codex" / "config.system.toml"
    )
    user_config = args.user_config.expanduser()
    system_config = args.system_config
    cwd = args.cwd.expanduser().resolve()
    if args.codex:
        codex = args.codex.expanduser().resolve()
    else:
        codex_command = shutil.which("codex")
        if not codex_command:
            parser.error("codex executable is not on PATH")
        codex = Path(codex_command).resolve()

    errors: list[str] = []
    checks: dict[str, Any] = {}

    for label, path in (("portable", portable), ("user", user_config)):
        try:
            config = load_toml(path)
        except Exception:
            errors.append(f"{label} TOML parse failed")
            config = {}
        checks[f"{label}Toml"] = "ok" if config else "empty-or-invalid"
        if label == "portable":
            portable_data = config
        else:
            user_data = config

    portable_flat = flatten(portable_data)
    user_flat = flatten(user_data)

    forbidden = sorted(key for key in portable_flat if portable_prefix_violation(key))
    if forbidden:
        errors.extend(f"portable ownership violation: {key}" for key in forbidden)

    portable_mcps = set((portable_data.get("mcp_servers") or {}).keys())
    if portable_mcps != REQUIRED_MCPS:
        for name in sorted(REQUIRED_MCPS - portable_mcps):
            errors.append(f"portable MCP missing: {name}")
        for name in sorted(portable_mcps - REQUIRED_MCPS):
            errors.append(f"unexpected portable MCP: {name}")

    portable_plugins = set((portable_data.get("plugins") or {}).keys())
    if portable_plugins != REQUIRED_PLUGINS:
        for name in sorted(REQUIRED_PLUGINS - portable_plugins):
            errors.append(f"portable plugin missing: {name}")
        for name in sorted(portable_plugins - REQUIRED_PLUGINS):
            errors.append(f"unsupported portable plugin: {name}")

    if not system_config.is_symlink():
        errors.append("system config is not a symlink")
    else:
        if system_config.resolve() != portable:
            errors.append("system config points outside the approved portable source")
        if system_config.lstat().st_uid != 0:
            errors.append("system config symlink is not root-owned")

    try:
        user_stat = user_config.lstat()
    except FileNotFoundError:
        errors.append("user config is missing")
    else:
        if stat.S_ISLNK(user_stat.st_mode) or not stat.S_ISREG(user_stat.st_mode):
            errors.append("user config is not a regular file")
        if stat.S_IMODE(user_stat.st_mode) != 0o600:
            errors.append("user config mode is not 0600")
        if user_stat.st_uid != os.getuid():
            errors.append("user config is not owned by the current user")

    allowed_overrides = set(args.allow_user_override)
    collisions = set(portable_flat) & set(user_flat)
    unexpected_collisions = sorted(collisions - allowed_overrides)
    unused_overrides = sorted(allowed_overrides - collisions)
    errors.extend(f"unapproved user/system collision: {key}" for key in unexpected_collisions)
    errors.extend(f"declared override is not present: {key}" for key in unused_overrides)

    effective = read_effective_config(codex, cwd, args.timeout)
    layers = effective.get("layers") or []
    system_layers = [
        layer
        for layer in layers
        if isinstance(layer, dict)
        and isinstance(layer.get("name"), dict)
        and layer["name"].get("type") == "system"
    ]
    if len(system_layers) != 1:
        errors.append("app-server did not report exactly one system layer")
    elif system_layers[0].get("config") != portable_data:
        errors.append("app-server system layer differs from the portable source")

    effective_flat = flatten(effective.get("config") or {})
    origins = effective.get("origins") or {}
    for key, value in portable_flat.items():
        if key in allowed_overrides:
            expected_source = "user"
            expected_value = user_flat[key]
        else:
            expected_source = "system"
            expected_value = value
        if effective_flat.get(key, object()) != expected_value:
            errors.append(f"effective portable key mismatch: {key}")
        if source_type(origins.get(key)) != expected_source:
            errors.append(f"unexpected effective origin for: {key}")

    mcp_rows = run_json([str(codex), "mcp", "list", "--json"], cwd=cwd, timeout=args.timeout)
    enabled_mcps = {
        row.get("name")
        for row in mcp_rows
        if isinstance(row, dict) and row.get("enabled") is True
    }
    for name in sorted(REQUIRED_MCPS - enabled_mcps):
        errors.append(f"required MCP is not effective: {name}")

    zotero_route = Path.home() / ".local" / "bin" / "zotero-mcp-route"
    if not zotero_route.is_file() or not os.access(zotero_route, os.X_OK):
        errors.append("Zotero MCP route wrapper is unavailable")
        zotero_route_status = "failed"
    else:
        try:
            subprocess.run(
                [str(zotero_route), "--check"],
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
                timeout=args.timeout,
            )
        except Exception:
            errors.append("Zotero MCP route prerequisites failed")
            zotero_route_status = "failed"
        else:
            zotero_route_status = "ok"

    plugin_report = run_json(
        [str(codex), "plugin", "list", "--json"],
        cwd=cwd,
        timeout=args.timeout,
    )
    installed_plugins = {
        row.get("pluginId")
        for row in plugin_report.get("installed", [])
        if isinstance(row, dict)
        and row.get("installed") is True
        and row.get("enabled") is True
    }
    for name in sorted(REQUIRED_PLUGINS - installed_plugins):
        errors.append(f"required plugin is not installed and enabled: {name}")

    checks.update(
        {
            "systemLink": "ok" if not any("system config" in item for item in errors) else "failed",
            "userFile": "ok" if not any("user config" in item for item in errors) else "failed",
            "portableKeyCount": len(portable_flat),
            "localKeyCount": len(user_flat),
            "approvedOverrides": sorted(allowed_overrides),
            "effectiveMcpNames": sorted(name for name in enabled_mcps if isinstance(name, str)),
            "zoteroRoute": zotero_route_status,
            "installedPluginIds": sorted(
                name for name in installed_plugins if isinstance(name, str)
            ),
        }
    )
    report = {
        "schemaVersion": 1,
        "machine": args.machine,
        "containsConfigValues": False,
        "repo": display_path(repo),
        "portable": display_path(portable),
        "status": "ok" if not errors else "failed",
        "checks": checks,
        "errors": errors,
    }

    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        output.chmod(0o600)

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: verification failed without emitting config values: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1) from None
