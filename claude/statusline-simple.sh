#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract values from JSON
current_dir="$(echo "$input" | jq -r '.workspace.current_dir')"
model="$(echo "$input" | jq -r '.model.display_name')"
output_style="$(echo "$input" | jq -r '.output_style.name')"

# Change to the current directory
cd "$current_dir" 2>/dev/null

# Get username and hostname (short form)
username="$(whoami)"
hostname="$(hostname -s)"
dir_name="$(basename "$current_dir")"

# Colors (using printf for proper ANSI codes)
# Note: Status line will be displayed with dimmed colors
USER_COLOR="\033[1;36m"    # Cyan (like agnoster's user segment)
DIR_COLOR="\033[1;34m"     # Blue (like agnoster's directory segment)
GIT_CLEAN="\033[1;32m"     # Green (clean repo)
GIT_DIRTY="\033[1;33m"     # Yellow (dirty repo)
MODEL_COLOR="\033[1;35m"   # Magenta
RESET="\033[0m"

# Get git information if in a git repository
git_info=""
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    branch=$(git branch --show-current 2>/dev/null || echo 'detached')

    # Check if repository is clean
    if git diff-index --quiet HEAD -- 2>/dev/null; then
        # Clean repository - use green
        git_info=$(printf "${GIT_CLEAN}⎇ %s${RESET}" "$branch")
    else
        # Dirty repository - use yellow
        git_info=$(printf "${GIT_DIRTY}⎇ %s ✗${RESET}" "$branch")
    fi
fi

# Format model information
if [ "$output_style" != "null" ] && [ "$output_style" != "default" ]; then
    model_info=$(printf "${MODEL_COLOR}%s | %s${RESET}" "$model" "$output_style")
else
    model_info=$(printf "${MODEL_COLOR}%s${RESET}" "$model")
fi

# Build the status line with agnoster-like formatting
# Format: username@hostname in directory [git] [model]
user_segment=$(printf "${USER_COLOR}%s@%s${RESET}" "$username" "$hostname")
dir_segment=$(printf "${DIR_COLOR}%s${RESET}" "$dir_name")

if [ -n "$git_info" ]; then
    printf "%s in %s %s [%s]\n" "$user_segment" "$dir_segment" "$git_info" "$model_info"
else
    printf "%s in %s [%s]\n" "$user_segment" "$dir_segment" "$model_info"
fi