---
name: colab-operator
description: Operate Google Colab GPU/TPU runtimes from any coding agent via `colab-account` and `google-colab-cli`. Use when provisioning remote Colab GPUs or TPUs (`T4`, `L4`, `G4`, `A100`, `v5e1`, `v6e1`), running Python scripts or notebooks remotely, checking compute-unit balance (`ccu-info`), transferring files, or cleaning up Colab sessions across Codex, Claude Code, and Antigravity.
---

# Colab Operator (`colab-account` + `google-colab-cli`)

Operate remote Google Colab runtimes non-interactively across Codex, Claude Code, and Antigravity using the keyring-free `colab-account` wrapper in `botfiles/bin`.

## Always Use `colab-account`, Not Bare `colab`

Bare `colab` defaults to `--auth=oauth2`, which uses Linux SecretService / macOS Keychain (blocking or failing in headless/SSH agent sessions), or `--auth=adc` against global `~/.config/gcloud/application_default_credentials.json`.

Instead, always invoke `colab-account <alias> ...`:
- **Default personal account**: `personal` (`<personal-email>`, Google One AI Pro 5TB).
- **Isolated credentials**: `~/.config/colab-cli/accounts/<alias>.json` (`0600`), routed via `GOOGLE_APPLICATION_CREDENTIALS` and `--auth=adc`. Never touches existing machine `gcloud` configs or work accounts.
- **Isolated session state**: `~/.config/colab-cli/account-state/<alias>/sessions.json`.
- **List configured aliases**: `colab-account --list`

## Zero-Burn Inspection Commands (Start Here)

```bash
colab-account personal whoami        # Verify email, scopes, and token expiry
colab-account personal ccu-info      # Balance, hourly burn rate, active count, eligible GPUs/TPUs
colab-account personal ccu-info --json
colab-account personal usage         # Standard CLI balance/rate summary
colab-account personal sessions      # List live server-side assignments (auto-prunes stale local state)
```

## Compute Routing: Local GPU (`Research-GPU-01`) vs Colab

- On **`Research-GPU-01`** (two local A100 80GB GPUs), prefer local compute when appropriate and coordinated with ZON-389/active workload owners.
- Use **Colab** for:
  - Running GPU/TPU workloads from **`sourya-mac`** or **`research-cpu-01`** without SSHing jobs onto the shared GPU host.
  - **TPU workloads** (`v5e1`, `v6e1`) unavailable locally.
  - Disposable, isolated experiments, quick Colab notebook compatibility checks, or overflow capacity when local GPUs are busy.

## Verified Account Entitlements (`<personal-email>`, Google One AI Pro 5TB)

Observed baseline on 2026-11-25 (`500.00` monthly CCU balance):
- **Eligible GPUs**: `T4` (`1.24 CCU/hr`, 15 GB VRAM, 2 vCPU / 12.7 GiB RAM), `L4` (`2.33 CCU/hr`, 22.5 GB VRAM, 12 vCPU / 53 GiB RAM), `G4`, `A100` (`G4` and `A100` are tier-eligible; allocation depends on real-time regional pool capacity and may return `503 Service Unavailable` when busy).
- **Eligible TPUs**: `V5E1`, `V6E1`.
- **Ineligible GPUs**: `H100` (listed in `ineligibleGpus`; backend returns `400 Bad Request`).
- **Unsupported flags**: `--high-mem` may require Colab Pro+ or be ignored for single-shape accelerators (`L4`, `v5e1`, `v6e1`).

## Standard Execution Lifecycle (Agent-Safe)

In `google-colab-cli` `0.8.0`, `colab run` can occasionally hit an initial WebSocket race (`RuntimeError: Connection was lost.`) immediately after VM allocation, and raw `colab stop` lacks `--all`. Follow this reliable lifecycle:

### 1. Provision with an explicit session name
```bash
colab-account personal new -s my-job --gpu T4
# Supported --gpu: T4, L4, G4, A100 (H100 ineligible on AI Pro)
# Supported --tpu: v5e1, v6e1
```
Always pass `-s <name>`. If `new` fails with `503 Service Unavailable` on `A100`/`G4`, fall back to `--gpu L4` or `--gpu T4`.

### 2. Run code (kernel state persists across `exec` calls)
```bash
colab-account personal install -s my-job torch transformers
colab-account personal exec -s my-job -f train.py
colab-account personal exec -s my-job --env DATA_SPLIT=val -f eval.py
echo 'import torch; print(torch.cuda.get_device_name(0))' | colab-account personal exec -s my-job
```
- Default remote working directory is `/content`.
- Kernel variables, imports, and filesystem state in `/content` persist across `exec` calls until `stop` or `restart-kernel`.
- Use `colab-account personal run --gpu T4 script.py` only when you specifically want one-shot ephemeral `new + exec + stop` (note: if `0.8.0` raises `Connection was lost`, use `new` + `exec` + `stop` instead).

### 3. Transfer files or run shell commands
```bash
colab-account personal upload -s my-job local_data.csv /content/local_data.csv
colab-account personal ls -s my-job /content
colab-account personal download -s my-job /content/output.pt ./output.pt
colab-account personal ssh -s my-job -- 'nvidia-smi' </dev/null
```
For multi-line shell commands when SSH is unavailable or throttled (HTTP 429), use `%%bash` via `colab-account personal exec -s my-job`.

### 4. Mandatory Teardown (Never Leave Idle VMs)
Idle runtimes keep burning CCUs (`1.24+ CCU/hr`). Always stop and verify `Active assignments: 0`:
```bash
colab-account personal stop -s my-job
# Or tear down every local + orphaned server session via wrapper helper:
colab-account personal stop --all
colab-account personal sessions
colab-account personal usage
```

### Parallel Agent Isolation
If multiple agents share the same alias concurrently, isolate local session state with `COLAB_SESSION_CONFIG=/path/to/scratch-sessions.json` (or `--config /path/to/scratch-sessions.json`) and use distinct `-s <name>` session names.

## Commands Agents Must Never Run Interactively
- Never run `colab-account <alias> repl`, `colab-account <alias> auth`, `colab-account <alias> drivemount`, or bare `colab-account <alias> ssh` (without `-- CMD`). They expect an interactive TTY and will hang.
- Never paste or print contents of `~/.config/colab-cli/accounts/*.json`.

## Bootstrap on Another Machine (`sourya-mac` or `research-cpu-01`)

Never copy OAuth credential JSON files between machines. On a new machine with `botfiles` checked out:
```bash
uv tool install --python 3.12 google-colab-cli
colab-account personal login --login-hint <you>@gmail.com --expect-email <you>@gmail.com
colab-account personal whoami
colab-account personal ccu-info
```
On headless hosts without a desktop browser (`research-cpu-01`), pass `--remote` to `colab-account personal login` and complete the consent URL in any browser.
