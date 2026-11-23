#!/usr/bin/env python3
"""Shared helpers for skill directory discovery and content comparison."""

from __future__ import annotations

import hashlib
from pathlib import Path

SIDES = ("claude", "codex")
LAYOUTS = ("visible", "hidden")


def skills_base(repo_root: Path, side: str, layout: str) -> Path:
    if side not in SIDES:
        raise ValueError(f"Unsupported side: {side}")
    if layout == "visible":
        return repo_root / side / "skills"
    if layout == "hidden":
        return repo_root / f".{side}" / "skills"
    raise ValueError(f"Unsupported layout: {layout}")


def discover_repo_root(start: Path) -> Path:
    for candidate in [start] + list(start.parents):
        if any(skills_base(candidate, side, layout).is_dir() for side in SIDES for layout in LAYOUTS):
            return candidate
    raise FileNotFoundError(
        "Could not discover repo root with claude/codex skills directories from current path"
    )


def detect_layout(repo_root: Path) -> str:
    visible_count = sum(skills_base(repo_root, side, "visible").is_dir() for side in SIDES)
    hidden_count = sum(skills_base(repo_root, side, "hidden").is_dir() for side in SIDES)

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


def skill_dirs(base: Path) -> dict[str, Path]:
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


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def dir_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = file_path.relative_to(path).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(file_digest(file_path).encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()
