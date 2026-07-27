#!/usr/bin/env bash
# Capture a recoverable Git-only botfiles snapshot without archiving untracked contents.

set -euo pipefail

usage() {
    printf 'Usage: %s --repo PATH --output PATH\n' "$0" >&2
}

repo_path=""
output_dir=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)
            repo_path="${2:?missing --repo value}"
            shift 2
            ;;
        --output)
            output_dir="${2:?missing --output value}"
            shift 2
            ;;
        *)
            usage
            exit 2
            ;;
    esac
done

[[ -n "$repo_path" && -n "$output_dir" ]] || {
    usage
    exit 2
}

repo_path="$(cd "$repo_path" && pwd -P)"
git -C "$repo_path" rev-parse --is-inside-work-tree >/dev/null
mkdir -p "$output_dir"
output_dir="$(cd "$output_dir" && pwd -P)"
if find "$output_dir" -mindepth 1 -print -quit | grep -q .; then
    printf 'error: output directory must be empty: %s\n' "$output_dir" >&2
    exit 1
fi

git -C "$repo_path" status --short --branch >"$output_dir/status.txt"
git -C "$repo_path" show-ref --head >"$output_dir/refs.txt"
git -C "$repo_path" log --all --date=iso-strict \
    --format='%H %ad %D %s' >"$output_dir/history.txt"
if git -C "$repo_path" show-ref --verify --quiet refs/heads/main &&
   git -C "$repo_path" show-ref --verify --quiet refs/remotes/origin/main; then
    git -C "$repo_path" log --left-right --cherry-mark --oneline \
        main...origin/main >"$output_dir/divergence.txt"
else
    : >"$output_dir/divergence.txt"
fi
git -C "$repo_path" diff --binary \
    --output="$output_dir/tracked-worktree.patch"
git -C "$repo_path" ls-files --others --exclude-standard \
    >"$output_dir/untracked-manifest.txt"
git -C "$repo_path" bundle create "$output_dir/main-refs.bundle" \
    HEAD main origin/main
git -C "$repo_path" ls-remote origin HEAD refs/heads/main \
    >"$output_dir/remote-main.txt"
if command -v sha256sum >/dev/null 2>&1; then
    find "$output_dir" -maxdepth 1 -type f ! -name sha256sums.txt \
        -print0 | sort -z | xargs -0 sha256sum >"$output_dir/sha256sums.txt"
else
    find "$output_dir" -maxdepth 1 -type f ! -name sha256sums.txt \
        -print0 | sort -z | xargs -0 shasum -a 256 >"$output_dir/sha256sums.txt"
fi

printf 'snapshot=%s\n' "$output_dir"
