# Codex Skills

Store custom Codex skills in this directory so they are versioned in
`botfiles` and shared across machines.

`setup.sh` symlinks `~/.codex/skills` to this folder.

Keep skill instructions machine-agnostic: prefer `~/pro/...` paths over
machine-specific absolute paths.

Note: `~/.codex/skills/.system/` is machine-managed and intentionally
git-ignored, since Codex/system skill versions can differ across OS and
installation versions.
