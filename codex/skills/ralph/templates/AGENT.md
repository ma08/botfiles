# Agent Instructions

## Environment Setup

```bash
# Example: Activate conda environment
# conda activate myenv

# Example: Set PATH
# export PATH="/path/to/bin:$PATH"

# Example: Verify critical secrets are available
# grep MY_API_KEY .env.local
# If missing: feature calls will silently fail
```

---

## Validation — Tiered Testing

Run the appropriate tiers after each change. Higher tiers run less frequently.

### Tier 1 — Static Validation (run after EVERY change, ~2-5s)

```bash
# Build / compile check
# npm run build
# python setup.py build
# deno check --no-lock src/main.ts

# Type checking
# mypy src/ --ignore-missing-imports
# npx tsc --noEmit

# Structural verification (grep for expected patterns)
# grep -n "function myNewFunction\|class MyNewClass" src/main.ts
```

### Tier 2 — Runtime Smoke Test (run after EVERY change, ~3-5s)

Quick check that the code loads and doesn't crash at runtime.
Expects a non-500/non-crash response. If the service isn't running, skip to Tier 1 only.

```bash
# HTTP endpoint example:
# HTTP_CODE=$(curl -s -o /tmp/smoke.json -w '%{http_code}' \
#   -X GET http://localhost:8080/health)
# echo "HTTP $HTTP_CODE"
# 200 = PASS, 500 = FAIL (runtime error), connection refused = skip

# Python module example:
# python -c "import mymodule; print('PASS: module loads')"

# CLI tool example:
# ./mytool --version && echo "PASS" || echo "FAIL"

# Node.js module example:
# node -e "require('./src/main'); console.log('PASS: module loads')"
```

**If Tier 2 returns 500 or crashes**: Fix before committing. The code broke at runtime.
**If Tier 2 returns connection refused**: Service not running. Skip Tier 2-3 and rely on Tier 1 only. Do NOT attempt to start services.

### Tier 3 — Functional / Integration Test (run at [MILESTONE] tasks in fix_plan.md, 10-60s)

Real data through the feature. Only run at tasks marked `[MILESTONE]` in fix_plan.md.

```bash
# Full test suite:
# pytest tests/test_feature.py -v

# Integration test via HTTP:
# curl -X POST http://localhost:8080/api/process -d '{"real": "data"}' | jq .

# End-to-end CLI:
# ./mytool process --input test_data.json --output /tmp/result.json
# diff /tmp/result.json expected_result.json

# External API smoke test (verify key works):
# node -e "fetch('https://api.example.com/v1/test?key=' + process.env.API_KEY)
#   .then(r => r.json()).then(j => console.log(j.ok ? 'PASS' : 'FAIL'))"
```

---

## Git Workflow

```bash
# Commit after each completed fix_plan item
git add -A
git commit -m "<prefix>: <description of what was implemented>"
```

## Key File Locations

| File | Purpose |
|------|---------|
| `src/main.ts` | **Primary target** — main code lives here |

## Notes

- Ralph updates this file when learning new commands
- Keep commands specific and tested
- Include the actual paths used in this project
- Tier 1 + Tier 2 run after every change. Tier 3 only at milestones.
