---
trigger: model_decision
description: "Diagram authoring defaults (Excalidraw for editable polished figures, Mermaid for inline docs) and browser automation / Playwright CLI guidance on SSH VMs. Load when creating diagrams or automating/debugging browsers."
---

# Diagrams and Browser Automation

## Diagram Authoring (Default: Excalidraw + Mermaid)

- **Polished, standalone, or human-editable figures (articles, blogs, architecture explainers):** Default to **Excalidraw (`.excalidraw`)** using the `excalidraw-diagram` skill. `.excalidraw` files are git-versioned, require no external MCP auth across Antigravity, Codex, and Claude, and give humans direct drag, retype, and arrow-rebind editing in excalidraw.com or VS Code.
  - Use `roughness: 0` and clean sans-serif styling when crisp technical/editorial geometry is preferred over hand-drawn sketchiness.
  - Dark background gotcha: Excalidraw's `viewBackgroundColor` is a canvas app setting that does not travel through element export/import. Always bake an explicit background rectangle into the elements when dark backgrounds matter.
- **Quick inline docs, GitHub issues/PRs, and Markdown artifacts:** Default to **Mermaid** so diagrams render inline and stay easy to diff in Git.
- Reach for code-first generators (SVG, PIL, D2) only when bulk generation or data-driven regeneration is specifically needed. Figma is no longer the default diagram tool.

## Browser Automation and Playwright in SSH VMs

- On Antigravity, prefer the native `browser` subagent and the `chrome-devtools` plugin for interactive web navigation, UI inspection, debugging, and live web apps.
- Use the `playwright` CLI skill when scripted headless terminal runs, Playwright snapshots, or traces are specifically needed.
- On SSH-only Linux VMs without an X server, run Playwright headless by default. If a visual browser is required via Playwright, use `xvfb-run -a bash "$PWCLI" open <url> --headed`.
- Invoke the wrapper via `bash` using a harness-independent path:
  - `export PWCLI="$HOME/.gemini/config/botfiles-skills/playwright/scripts/playwright_cli.sh"` (or `$HOME/pro/botfiles/codex/skills/playwright/scripts/playwright_cli.sh`)
  - `bash "$PWCLI" open <url>`
- Always `snapshot` before interacting and re-`snapshot` after navigation or UI changes.
- Save Playwright artifacts (screenshots, traces) in a repo-appropriate location, defaulting to `output/playwright/` when no repo guidance exists.
