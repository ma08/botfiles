#!/usr/bin/env python3
"""Compile a LaTeX research explainer reproducibly and retain one build log."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def scan_latex_warnings(log_path: Path) -> list[str]:
    """Return distinct warning/error-shape lines from the final LaTeX pass."""
    if not log_path.is_file():
        raise SystemExit(f"Expected final LaTeX log was not produced: {log_path}")

    warnings: list[str] = []
    for raw_line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        tracked = (
            "LaTeX Warning:" in line
            or (line.startswith(("Package ", "Class ")) and " Warning:" in line)
            or line.startswith(("Overfull \\hbox", "Underfull \\hbox"))
            or line.startswith(("Overfull \\vbox", "Underfull \\vbox"))
            or line.startswith("Missing character:")
            or "multiply defined" in line
            or "undefined references" in line
        )
        if tracked and line not in warnings:
            warnings.append(line)
    return warnings


def resolve_engine(requested: str) -> str:
    if requested != "auto":
        path = shutil.which(requested)
        if path is None:
            raise SystemExit(f"LaTeX engine is not available: {requested}")
        return path

    for candidate in ("lualatex", "pdflatex"):
        path = shutil.which(candidate)
        if path is not None:
            return path
    raise SystemExit("No supported LaTeX engine found (tried lualatex and pdflatex)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to the LaTeX source")
    parser.add_argument("--output", type=Path, help="Final PDF path; defaults beside the source")
    parser.add_argument(
        "--build-dir",
        type=Path,
        required=True,
        help="Directory for LaTeX auxiliary files and compile.log",
    )
    parser.add_argument(
        "--engine",
        choices=("auto", "lualatex", "pdflatex"),
        default="auto",
        help="LaTeX engine; auto prefers lualatex",
    )
    parser.add_argument("--passes", type=int, default=2, help="Compilation passes (2-4)")
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Return exit code 2 when the final LaTeX log contains tracked warnings",
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".tex":
        raise SystemExit(f"Expected an existing .tex source: {source}")
    if not 2 <= args.passes <= 4:
        raise SystemExit("--passes must be between 2 and 4")

    output = (args.output or source.with_suffix(".pdf")).expanduser().resolve()
    build_dir = args.build_dir.expanduser().resolve()
    build_dir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    engine = resolve_engine(args.engine)
    command = [
        engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        f"-output-directory={build_dir}",
        source.name,
    ]
    environment = os.environ.copy()
    environment.setdefault("TEXMFVAR", str(build_dir / "texmf-var"))
    environment.setdefault("TEXMFCACHE", str(build_dir / "texmf-cache"))

    log_path = build_dir / "compile.log"
    with log_path.open("w", encoding="utf-8") as log:
        for pass_number in range(1, args.passes + 1):
            log.write(f"\n=== pass {pass_number}/{args.passes}: {' '.join(command)} ===\n")
            log.flush()
            result = subprocess.run(
                command,
                cwd=source.parent,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if result.returncode != 0:
                print(f"LaTeX pass {pass_number} failed; inspect {log_path}")
                return result.returncode

    built_pdf = build_dir / source.with_suffix(".pdf").name
    if not built_pdf.is_file():
        raise SystemExit(f"LaTeX completed without producing the expected PDF: {built_pdf}")
    if built_pdf != output:
        shutil.copy2(built_pdf, output)

    final_latex_log = build_dir / source.with_suffix(".log").name
    warnings = scan_latex_warnings(final_latex_log)
    with log_path.open("a", encoding="utf-8") as log:
        log.write("\n=== final LaTeX log warning scan ===\n")
        if warnings:
            for warning in warnings:
                log.write(warning + "\n")
        else:
            log.write("No tracked warnings.\n")

    print(f"Compiled {source} -> {output}")
    print(f"Build log: {log_path}")
    if warnings:
        print(f"Final LaTeX log: {len(warnings)} distinct tracked warning line(s)")
        for warning in warnings[:20]:
            print(f"  - {warning}")
        if len(warnings) > 20:
            print(f"  - ... {len(warnings) - 20} additional warning line(s); inspect the log")
        if args.fail_on_warnings:
            return 2
    else:
        print("Final LaTeX log: no tracked warnings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
