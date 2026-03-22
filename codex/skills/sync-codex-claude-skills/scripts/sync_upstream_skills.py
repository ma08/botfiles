#!/usr/bin/env python3
"""
Audit and sync local Codex skills against the OpenAI curated skills repo.

Examples:
  python scripts/sync_upstream_skills.py status
  python scripts/sync_upstream_skills.py sync
  python scripts/sync_upstream_skills.py sync --skills screenshot --apply
  python scripts/sync_upstream_skills.py sync --skills transcribe --force-protected --apply
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from skill_sync_common import detect_layout, dir_digest, discover_repo_root, skill_dirs, skills_base


class SyncError(Exception):
    """Raised when upstream sync operations fail."""


@dataclass(frozen=True)
class UpstreamPolicy:
    repo: str
    ref: str
    path: str
    protected_skills: tuple[str, ...]
    mirror_to_claude: bool


@dataclass(frozen=True)
class UpstreamSkillPlan:
    name: str
    source_dir: Path
    target_dir: Path
    action: str
    note: str | None = None


def _default_policy_path() -> Path:
    return Path(__file__).resolve().parent.parent / "upstream_sync_policy.json"


def _load_policy(path: Path) -> UpstreamPolicy:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SyncError(f"Policy file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SyncError(f"Policy file is not valid JSON: {path}") from exc

    try:
        protected = payload.get("protected_skills", [])
        return UpstreamPolicy(
            repo=str(payload["repo"]),
            ref=str(payload["ref"]),
            path=str(payload["path"]),
            protected_skills=tuple(sorted({str(item) for item in protected})),
            mirror_to_claude=bool(payload.get("mirror_to_claude", True)),
        )
    except KeyError as exc:
        raise SyncError(f"Policy file is missing required key: {exc.args[0]}") from exc


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode != 0:
        joined = " ".join(args)
        stderr = result.stderr.strip()
        raise SyncError(f"Command failed ({joined}): {stderr or 'no stderr output'}")
    return result


def _clone_upstream_source(repo: str, ref: str, upstream_path: str, temp_root: Path) -> Path:
    repo_dir = temp_root / "repo"
    repo_url = f"https://github.com/{repo}.git"
    clone_cmd = [
        "git",
        "clone",
        "--filter=blob:none",
        "--depth",
        "1",
        "--sparse",
        "--single-branch",
        "--branch",
        ref,
        repo_url,
        str(repo_dir),
    ]

    try:
        _run(clone_cmd)
        _run(["git", "-C", str(repo_dir), "sparse-checkout", "set", upstream_path])
        _run(["git", "-C", str(repo_dir), "checkout", ref])
    except SyncError:
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        _run(["git", "clone", "--depth", "1", "--single-branch", "--branch", ref, repo_url, str(repo_dir)])

    source_dir = repo_dir / upstream_path
    if not source_dir.is_dir():
        raise SyncError(
            f"Upstream skills path not found in {repo}@{ref}: {upstream_path}"
        )
    return source_dir


def build_status(repo_root: Path, policy: UpstreamPolicy, policy_path: Path, upstream_base: Path) -> dict:
    layout = detect_layout(repo_root)
    codex_map = skill_dirs(skills_base(repo_root, "codex", layout))
    upstream_map = skill_dirs(upstream_base)
    protected = set(policy.protected_skills)

    overlap = sorted(set(codex_map) & set(upstream_map))
    tracked_identical: list[str] = []
    tracked_drifted: list[str] = []
    protected_drifted: list[str] = []
    for name in overlap:
        if dir_digest(codex_map[name]) == dir_digest(upstream_map[name]):
            tracked_identical.append(name)
        elif name in protected:
            protected_drifted.append(name)
        else:
            tracked_drifted.append(name)

    local_only = sorted(set(codex_map) - set(upstream_map))
    upstream_only = sorted(set(upstream_map) - set(codex_map))

    return {
        "repo_root": str(repo_root),
        "layout": layout,
        "policy_path": str(policy_path),
        "upstream": {
            "repo": policy.repo,
            "ref": policy.ref,
            "path": policy.path,
            "protected_skills": list(policy.protected_skills),
            "mirror_to_claude": policy.mirror_to_claude,
        },
        "counts": {
            "codex_skills": len(codex_map),
            "upstream_skills": len(upstream_map),
            "tracked_identical": len(tracked_identical),
            "tracked_drifted": len(tracked_drifted),
            "protected_drifted": len(protected_drifted),
            "local_only": len(local_only),
            "upstream_only": len(upstream_only),
        },
        "tracked_identical": tracked_identical,
        "tracked_drifted": tracked_drifted,
        "protected_drifted": protected_drifted,
        "local_only": local_only,
        "upstream_only": upstream_only,
    }


def _print_group(label: str, items: list[str]) -> None:
    print(f"{label} ({len(items)}):")
    if items:
        for item in items:
            print(f"  - {item}")
    else:
        print("  - (none)")
    print("")


def _print_status(status: dict) -> None:
    counts = status["counts"]
    upstream = status["upstream"]
    print(f"Repo root: {status['repo_root']}")
    print(f"Layout: {status['layout']}")
    print(f"Policy: {status['policy_path']}")
    print(f"Upstream source: {upstream['repo']}@{upstream['ref']}:{upstream['path']}")
    print(f"Protected skills: {', '.join(upstream['protected_skills']) or '(none)'}")
    print(f"Mirror to claude after apply: {'yes' if upstream['mirror_to_claude'] else 'no'}")
    print("")
    print(f"Codex skills: {counts['codex_skills']}")
    print(f"Upstream curated skills: {counts['upstream_skills']}")
    print("")

    _print_group("Tracked identical", status["tracked_identical"])
    _print_group("Tracked drifted", status["tracked_drifted"])
    _print_group("Protected drifted", status["protected_drifted"])
    _print_group("Local only", status["local_only"])
    _print_group("Upstream only", status["upstream_only"])


def _unique_names(items: list[str] | None) -> list[str]:
    if not items:
        return []
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _build_sync_plan(
    repo_root: Path,
    layout: str,
    policy: UpstreamPolicy,
    upstream_base: Path,
    skills: list[str] | None,
    force_protected: bool,
) -> list[UpstreamSkillPlan]:
    codex_map = skill_dirs(skills_base(repo_root, "codex", layout))
    upstream_map = skill_dirs(upstream_base)
    codex_base = skills_base(repo_root, "codex", layout)
    protected = set(policy.protected_skills)

    if skills:
        selected = _unique_names(skills)
    else:
        selected = sorted((set(codex_map) & set(upstream_map)) - protected)

    missing_upstream = [name for name in selected if name not in upstream_map]
    if missing_upstream:
        raise SyncError(
            "Skill(s) not found in upstream curated source: " + ", ".join(missing_upstream)
        )

    plan: list[UpstreamSkillPlan] = []
    for name in selected:
        source_dir = upstream_map[name]
        target_dir = codex_base / name
        local_dir = codex_map.get(name)

        if local_dir is None:
            action = "create"
            note = "missing locally"
        else:
            identical = dir_digest(local_dir) == dir_digest(source_dir)
            if identical:
                action = "unchanged"
                note = None
            elif name in protected and not force_protected:
                action = "skip-protected"
                note = "protected by policy"
            else:
                action = "replace"
                note = None

        plan.append(
            UpstreamSkillPlan(
                name=name,
                source_dir=source_dir,
                target_dir=target_dir,
                action=action,
                note=note,
            )
        )
    return plan


def _print_sync_plan(plan: list[UpstreamSkillPlan], policy: UpstreamPolicy, mirror_to_claude: bool) -> None:
    print(f"Upstream source: {policy.repo}@{policy.ref}:{policy.path}")
    print(f"Protected skills: {', '.join(policy.protected_skills) or '(none)'}")
    print(f"Mirror to claude after apply: {'yes' if mirror_to_claude else 'no'}")
    print("Plan:")
    if not plan:
        print("  - (none)")
        return
    for item in plan:
        suffix = f" [{item.note}]" if item.note else ""
        print(f"  - {item.name}: {item.action}{suffix}")


def _apply_sync_plan(plan: list[UpstreamSkillPlan]) -> list[str]:
    changed_names: list[str] = []
    for item in plan:
        if item.action not in {"create", "replace"}:
            continue
        item.target_dir.parent.mkdir(parents=True, exist_ok=True)
        if item.target_dir.exists():
            shutil.rmtree(item.target_dir)
        shutil.copytree(item.source_dir, item.target_dir)
        changed_names.append(item.name)
    return changed_names


def _mirror_changes_to_claude(repo_root: Path, changed_names: list[str]) -> str:
    if not changed_names:
        return "No codex skill changes to mirror to claude."

    sync_script = Path(__file__).resolve().with_name("sync_skills.py")
    if not sync_script.is_file():
        raise SyncError(f"Local sync script not found: {sync_script}")

    cmd = [
        sys.executable,
        str(sync_script),
        "--repo-root",
        str(repo_root),
        "sync",
        "--from-side",
        "codex",
        "--to-side",
        "claude",
        "--skills",
        *changed_names,
        "--apply",
    ]
    result = _run(cmd)
    return result.stdout.strip()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit and sync local codex skills against openai/skills curated skills."
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repo root containing either botfiles-style visible skill roots "
            "(codex/skills, claude/skills) or hidden project-local skill roots "
            "(.codex/skills, .claude/skills)."
        ),
    )
    parser.add_argument(
        "--policy",
        default=None,
        help="Path to upstream sync policy JSON (defaults to upstream_sync_policy.json beside this skill).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Show upstream drift status")
    status_parser.add_argument("--json", action="store_true", help="Print JSON output")

    sync_parser = subparsers.add_parser("sync", help="Sync local codex skills from upstream curated source")
    sync_parser.add_argument("--skills", nargs="+", help="Specific upstream curated skills to sync or add")
    sync_parser.add_argument(
        "--force-protected",
        action="store_true",
        help="Allow replacing a protected local skill when it drifts from upstream.",
    )
    sync_parser.add_argument(
        "--no-mirror-claude",
        action="store_true",
        help="Do not mirror changed codex skills into claude after apply.",
    )
    sync_parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")

    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    try:
        repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else discover_repo_root(Path.cwd())
        layout = detect_layout(repo_root)
        policy_path = Path(args.policy).expanduser().resolve() if args.policy else _default_policy_path()
        policy = _load_policy(policy_path)
    except (FileNotFoundError, ValueError, SyncError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    try:
        with tempfile.TemporaryDirectory(prefix="skill-sync-upstream-") as tempdir:
            upstream_base = _clone_upstream_source(
                repo=policy.repo,
                ref=policy.ref,
                upstream_path=policy.path,
                temp_root=Path(tempdir),
            )

            if args.command == "status":
                status = build_status(repo_root, policy, policy_path, upstream_base)
                if args.json:
                    print(json.dumps(status, indent=2))
                else:
                    _print_status(status)
                return 0

            if args.command == "sync":
                plan = _build_sync_plan(
                    repo_root=repo_root,
                    layout=layout,
                    policy=policy,
                    upstream_base=upstream_base,
                    skills=args.skills,
                    force_protected=args.force_protected,
                )
                mirror_to_claude = policy.mirror_to_claude and not args.no_mirror_claude
                _print_sync_plan(plan, policy, mirror_to_claude)

                if not args.apply:
                    print("")
                    print("Dry-run only. Re-run with --apply to execute.")
                    return 0

                changed_names = _apply_sync_plan(plan)
                skipped_protected = [item.name for item in plan if item.action == "skip-protected"]

                print("")
                print(
                    "Applied to codex. "
                    f"Skills created/replaced: {len(changed_names)}, "
                    f"protected skips: {len(skipped_protected)}"
                )

                if mirror_to_claude:
                    print("")
                    print(_mirror_changes_to_claude(repo_root, changed_names))
                return 0
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Unsupported command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
