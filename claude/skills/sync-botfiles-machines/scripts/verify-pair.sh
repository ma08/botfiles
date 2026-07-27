#!/usr/bin/env bash
# Verify local and SSH-remote botfiles checkouts are clean main branches at live remote main.

set -euo pipefail

usage() {
    printf 'Usage: %s --local-repo PATH --remote-host HOST --remote-repo PATH\n' "$0" >&2
}

local_repo=""
remote_host=""
remote_repo=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --local-repo)
            local_repo="${2:?missing --local-repo value}"
            shift 2
            ;;
        --remote-host)
            remote_host="${2:?missing --remote-host value}"
            shift 2
            ;;
        --remote-repo)
            remote_repo="${2:?missing --remote-repo value}"
            shift 2
            ;;
        *)
            usage
            exit 2
            ;;
    esac
done

[[ -n "$local_repo" && -n "$remote_host" && -n "$remote_repo" ]] || {
    usage
    exit 2
}

local_branch="$(git -C "$local_repo" branch --show-current)"
local_head="$(git -C "$local_repo" rev-parse HEAD)"
local_remote="$(git -C "$local_repo" ls-remote origin refs/heads/main | awk '{print $1}')"
local_dirty="$(git -C "$local_repo" status --porcelain)"

remote_report="$(
    ssh "$remote_host" "repo=$remote_repo; \
        printf 'branch=%s\\n' \"\$(git -C \"\$repo\" branch --show-current)\"; \
        printf 'head=%s\\n' \"\$(git -C \"\$repo\" rev-parse HEAD)\"; \
        printf 'remote=%s\\n' \"\$(git -C \"\$repo\" ls-remote origin refs/heads/main | awk '{print \$1}')\"; \
        if [[ -n \"\$(git -C \"\$repo\" status --porcelain)\" ]]; then printf 'dirty=yes\\n'; else printf 'dirty=no\\n'; fi"
)"

remote_branch="$(awk -F= '$1 == "branch" {print $2}' <<<"$remote_report")"
remote_head="$(awk -F= '$1 == "head" {print $2}' <<<"$remote_report")"
remote_main="$(awk -F= '$1 == "remote" {print $2}' <<<"$remote_report")"
remote_dirty="$(awk -F= '$1 == "dirty" {print $2}' <<<"$remote_report")"

printf 'local_branch=%s\nlocal_head=%s\nremote_main=%s\n' \
    "$local_branch" "$local_head" "$local_remote"
printf 'client_branch=%s\nclient_head=%s\nclient_remote_main=%s\n' \
    "$remote_branch" "$remote_head" "$remote_main"

[[ "$local_branch" == "main" ]] || {
    printf 'error: local checkout is not on main\n' >&2
    exit 1
}
[[ "$remote_branch" == "main" ]] || {
    printf 'error: client checkout is not on main\n' >&2
    exit 1
}
[[ -z "$local_dirty" ]] || {
    printf 'error: local checkout is dirty\n%s\n' "$local_dirty" >&2
    exit 1
}
[[ "$remote_dirty" == "no" ]] || {
    printf 'error: client checkout is dirty\n' >&2
    exit 1
}
[[ -n "$local_remote" && "$local_remote" == "$remote_main" ]] || {
    printf 'error: machines disagree on live remote main\n' >&2
    exit 1
}
[[ "$local_head" == "$local_remote" && "$remote_head" == "$local_remote" ]] || {
    printf 'error: one or more checkouts do not match remote main\n' >&2
    exit 1
}

printf 'verified=clean-identical-main\n'
