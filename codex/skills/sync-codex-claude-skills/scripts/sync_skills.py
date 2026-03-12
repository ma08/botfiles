#!/usr/bin/env python3
"""
Compare and sync skill folders between claude/skills and codex/skills.

Supports both standard project layouts (`claude/skills`, `codex/skills`) and
hidden project layouts (`.claude/skills`, `.codex/skills`).

Examples:
  python scripts/sync_skills.py status
  python scripts/sync_skills.py sync --from-side claude --to-side codex --all
  python scripts/sync_skills.py sync --from-side claude --to-side codex     --skills start-new-task get-task-details --apply
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

SIDES = ("claude", "codex")
LAYOUTS = ("visible", "hidden")


@dataclass(frozen=True)
class SkillPlan:
    name: str
    source_dir: Path
    target_dir: Path
    action: str  # create | replace | unchanged


def _skills_base(repo_root: Path, side: str, layout: str) -> Path:
    if side not in SIDES:
        raise ValueError(f"Unsupported side: {side}")
    if layout == "visible":
        return repo_root / side / "skills"
    if layout == "hidden":
        return repo_root / f".{side}" / "skills"
    raise ValueError(f"Unsupported layout: {layout}")


def _discover_repo_root(start: Path) -> Path:
    for candidate in [start] + list(start.parents):
        if any(_skills_base(candidate, side, layout).is_dir() for side in SIDES for layout in LAYOUTS):
            return candidate
    raise FileNotFoundError(
        "Could not discover repo root with claude/codex skills directories from current path"
    )


def _detect_layout(repo_root: Path) -> str:
    visible_count = sum(_skills_base(repo_root, side, "visible").is_dir() for side in SIDES)
    hidden_count = sum(_skills_base(repo_root, side, "hidden").is_dir() for side in SIDES)

    if visible_count == 0 and hidden_count == 0:
        raise FileNotFoundError(
            "Could not find any claude/codex skills directories under the repo root"
        )
    if visible_count and hidden_count:
        if visible_count > hidden_count:
            return "visible"
        if hidden_count > visible_count:
            return "hidden"
        raise ValueError(
            "Ambiguous repo layout: found both hidden and non-hidden skills directories. "
            "Use a repo root with one layout at a time."
        )
    return "visible" if visible_count else "hidden"


def _skill_dirs(base: Path) -> dict[str, Path]:
    skills: dict[str, Path] = {}
    if not base.is_dir():
        return skills
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        if not (child / "SKILL.md").is_file():
            continue
        skills[child.name] = child
    return skills


def _file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _dir_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = file_path.relative_to(path).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(_file_digest(file_path).encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()


def build_status(repo_root: Path) -> dict:
    layout = _detect_layout(repo_root)
    claude_map = _skill_dirs(_skills_base(repo_root, "claude", layout))
    codex_map = _skill_dirs(_skills_base(repo_root, "codex", layout))

    only_claude = sorted(set(claude_map) - set(codex_map))
    only_codex = sorted(set(codex_map) - set(claude_map))

    both = sorted(set(claude_map) & set(codex_map))
    both_identical: list[str] = []
    both_different: list[str] = []
    for name in both:
        if _dir_digest(claude_map[name]) == _dir_digest(codex_map[name]):
            both_identical.append(name)
        else:
            both_different.append(name)

    return {
        "repo_root": str(repo_root),
        "layout": layout,
        "counts": {
            "claude_skills": len(claude_map),
            "codex_skills": len(codex_map),
            "only_claude": len(only_claude),
            "only_codex": len(only_codex),
            "both_identical": len(both_identical),
            "both_different": len(both_different),
        },
        "only_claude": only_claude,
        "only_codex": only_codex,
        "both_identical": both_identical,
        "both_different": both_different,
    }


def _print_status(status: dict) -> None:
    counts = status["counts"]
    print(f"Repo root: {status['repo_root']}")
    print(f"Layout: {status['layout']}")
    print(f"Claude skills: {counts['claude_skills']}")
    print(f"Codex skills: {counts['codex_skills']}")
    print("")

    print(f"Only in claude ({counts['only_claude']}):")
    if status["only_claude"]:
        for item in status["only_claude"]:
            print(f"  - {item}")
    else:
        print("  - (none)")
    print("")

    print(f"Only in codex ({counts['only_codex']}):")
    if status["only_codex"]:
        for item in status["only_codex"]:
            print(f"  - {item}")
    else:
        print("  - (none)")
    print("")

    print(f"In both but different ({counts['both_different']}):")
    if status["both_different"]:
        for item in status["both_different"]:
            print(f"  - {item}")
    else:
        print("  - (none)")
    print("")

    print(f"In both and identical ({counts['both_identical']}):")
    if status["both_identical"]:
        for item in status["both_identical"]:
            print(f"  - {item}")
    else:
        print("  - (none)")


def _build_sync_plan(
    repo_root: Path,
    layout: str,
    from_side: str,
    to_side: str,
    skills: list[str] | None,
    sync_all: bool,
) -> list[SkillPlan]:
    source_skills = _skill_dirs(_skills_base(repo_root, from_side, layout))
    target_skills = _skill_dirs(_skills_base(repo_root, to_side, layout))
    target_base = _skills_base(repo_root, to_side, layout)

    if sync_all:
        selected = sorted(source_skills.keys())
    else:
        if not skills:
            raise ValueError("Provide --all or --skills <name...>")
        selected = []
        seen: set[str] = set()
        for skill in skills:
            if skill not in seen:
                selected.append(skill)
                seen.add(skill)

    missing_in_source = [skill for skill in selected if skill not in source_skills]
    if missing_in_source:
        raise FileNotFoundError(
            f"Skill(s) not found in source ({from_side}/skills): {', '.join(missing_in_source)}"
        )

    plan: list[SkillPlan] = []
    for skill in selected:
        source_dir = source_skills[skill]
        target_dir = target_base / skill
        if skill not in target_skills:
            action = "create"
        else:
            action = "replace" if _dir_digest(source_dir) != _dir_digest(target_skills[skill]) else "unchanged"
        plan.append(
            SkillPlan(
                name=skill,
                source_dir=source_dir,
                target_dir=target_dir,
                action=action,
            )
        )
    return plan


def _print_sync_plan(plan: list[SkillPlan], from_side: str, to_side: str, layout: str) -> None:
    print(f"Layout: {layout}")
    print(f"Sync direction: {from_side} -> {to_side}")
    print("Plan:")
    for item in plan:
        print(f"  - {item.name}: {item.action}")


def _apply_plan(
    plan: list[SkillPlan],
    delete_target_extras: bool,
    repo_root: Path,
    layout: str,
    from_side: str,
    to_side: str,
    sync_all: bool,
) -> tuple[int, int]:
    created_or_replaced = 0
    deleted = 0
    for item in plan:
        if item.action == "unchanged":
            continue
        item.target_dir.parent.mkdir(parents=True, exist_ok=True)
        if item.target_dir.exists():
            shutil.rmtree(item.target_dir)
        shutil.copytree(item.source_dir, item.target_dir)
        created_or_replaced += 1

    if delete_target_extras:
        if not sync_all:
            raise ValueError("--delete-target-extras can only be used with --all")
        source_names = set(_skill_dirs(_skills_base(repo_root, from_side, layout)))
        target_map = _skill_dirs(_skills_base(repo_root, to_side, layout))
        extras = sorted(set(target_map) - source_names)
        for name in extras:
            shutil.rmtree(target_map[name])
            deleted += 1

    return created_or_replaced, deleted


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare and sync codex/skills and claude/skills (including hidden .codex/.claude layouts)"
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repo root containing claude/codex skills directories; supports standard "
            "(claude/skills, codex/skills) and hidden (.claude/skills, .codex/skills) layouts"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Show drift status")
    status_parser.add_argument("--json", action="store_true", help="Print JSON output")

    sync_parser = subparsers.add_parser("sync", help="Sync skills from one side to the other")
    sync_parser.add_argument("--from-side", choices=["claude", "codex"], required=True)
    sync_parser.add_argument("--to-side", choices=["claude", "codex"], required=True)
    sync_parser.add_argument("--all", action="store_true", help="Sync all skills from source")
    sync_parser.add_argument("--skills", nargs="+", help="Specific skill names to sync")
    sync_parser.add_argument(
        "--delete-target-extras",
        action="store_true",
        help="Delete target-side skills missing from source (requires --all and --apply)",
    )
    sync_parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")

    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else _discover_repo_root(Path.cwd())
        layout = _detect_layout(repo_root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.command == "status":
        status = build_status(repo_root)
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            _print_status(status)
        return 0

    if args.command == "sync":
        if args.from_side == args.to_side:
            print("Error: --from-side and --to-side must differ", file=sys.stderr)
            return 2

        try:
            plan = _build_sync_plan(
                repo_root=repo_root,
                layout=layout,
                from_side=args.from_side,
                to_side=args.to_side,
                skills=args.skills,
                sync_all=args.all,
            )
        except (ValueError, FileNotFoundError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

        _print_sync_plan(plan, args.from_side, args.to_side, layout)

        if not args.apply:
            print("")
            print("Dry-run only. Re-run with --apply to execute.")
            return 0

        if args.delete_target_extras and not args.all:
            print("Error: --delete-target-extras requires --all", file=sys.stderr)
            return 2

        try:
            changed, deleted = _apply_plan(
                plan=plan,
                delete_target_extras=args.delete_target_extras,
                repo_root=repo_root,
                layout=layout,
                from_side=args.from_side,
                to_side=args.to_side,
                sync_all=args.all,
            )
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

        print("")
        print(f"Applied. Skills copied/replaced: {changed}, deleted: {deleted}")
        return 0

    print(f"Unsupported command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
