#!/usr/bin/env python3
"""Generate and securely store a runner-only Claude subscription OAuth token."""

from __future__ import annotations

import argparse
import getpass
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


TOKEN_RELATIVE_PATH = Path("secrets/local/claude-fable-oauth-token")


def default_token_file() -> Path:
    root = os.environ.get("BOTFILES_ROOT")
    if root:
        return Path(root).expanduser() / TOKEN_RELATIVE_PATH
    return Path.home() / "pro/botfiles" / TOKEN_RELATIVE_PATH


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token-file", type=Path, default=default_token_file())
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Skip `claude setup-token` and only prompt for an existing token.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing token file.",
    )
    return parser.parse_args()


def validate_token(token: str) -> str:
    normalized = token.strip()
    if not normalized or any(character.isspace() for character in normalized):
        raise SystemExit("Token must be one non-empty value without whitespace.")
    return normalized


def write_token(path: Path, token: str, *, force: bool) -> None:
    path = path.expanduser()
    if path.is_symlink():
        raise SystemExit(f"Refusing to replace a symlink token path: {path}")
    path = path.resolve()
    if path.exists() and not force:
        raise SystemExit(f"Token file already exists: {path}\nRerun with --force to replace it.")

    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w") as handle:
            handle.write(token + "\n")
        os.replace(temporary_path, path)
        path.chmod(0o600)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def main() -> int:
    args = parse_args()
    if not args.skip_generate:
        claude_bin = shutil.which("claude")
        if not claude_bin:
            raise SystemExit("claude command not found")
        print("Claude will open its subscription OAuth flow and print a long-lived token.")
        print("Keep this terminal private. Copy the token when Claude displays it.")
        completed = subprocess.run([claude_bin, "setup-token"], check=False)
        if completed.returncode != 0:
            return completed.returncode

    token = validate_token(
        getpass.getpass("Paste the generated token here (input is hidden): ")
    )
    write_token(args.token_file, token, force=args.force)
    print(f"Stored the Fable-only OAuth token at {args.token_file.expanduser().resolve()}")
    print("The token value was not echoed or written to shell history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
