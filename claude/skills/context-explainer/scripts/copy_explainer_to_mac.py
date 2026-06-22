#!/usr/bin/env python3
"""Copy a generated HTML explainer to a Mac over SSH/SCP and optionally open it."""

from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path, PurePosixPath


def run(cmd: list[str]) -> None:
    print("+ " + " ".join(shlex.quote(part) for part in cmd), flush=True)
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path, help="Path to the local HTML explainer")
    parser.add_argument("--machine", default="sourya-mac", help="SSH alias for the Mac")
    parser.add_argument("--dest-dir", default="/Users/sourya4/Desktop", help="Destination directory on the Mac")
    parser.add_argument("--name", help="Destination filename; defaults to source basename")
    parser.add_argument("--open", action="store_true", help="Open the copied HTML on the Mac")
    args = parser.parse_args()

    source = args.html.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"HTML file does not exist: {source}")
    if source.suffix.lower() not in {".html", ".htm"}:
        raise SystemExit(f"Expected an HTML file, got: {source}")

    filename = args.name or source.name
    remote_path = PurePosixPath(args.dest_dir) / filename
    quoted_remote = shlex.quote(str(remote_path))

    run(["ssh", args.machine, "mkdir", "-p", shlex.quote(args.dest_dir)])
    run(["scp", str(source), f"{args.machine}:{quoted_remote}"])
    run(["ssh", args.machine, "ls", "-lh", quoted_remote])
    if args.open:
        run(["ssh", args.machine, "open", quoted_remote])

    print(f"Copied explainer to {args.machine}:{remote_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
