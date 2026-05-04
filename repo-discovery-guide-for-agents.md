# Repo Discovery Guide — skill-image-comprehension-ollama

> A cached map of non-obvious truths for coding agents working in this repository.

## Maintenance Mandate

1. **Before every commit**, ask: did I change anything this guide documents? If yes, update the guide in the same commit. No exceptions.
2. **At session start**, spot-check 2-3 key facts against the actual codebase (paths, versions, script names). If anything drifted, update immediately.
3. **Quarterly minimum**, re-verify if the repo hasn't been touched. Stale guidance is worse than no guidance.

- Last verified: 2026-04-30
- Changes since last verify: initial creation

## Project Overview

A single-file Agent Skill that gives AI coding agents the ability to "see" images. It wraps a local Ollama vision model (default: `moondream:1.8b`, ~1.6 GB) via a Python-only (stdlib) script that base64-encodes an image, sends it to Ollama's `/api/generate` endpoint, and prints a text description to stdout. Everything runs locally — no API keys, no cloud, no external Python deps. Follows the Agent Skills specification. GitHub source: `aosama/image-comprehension-ollama`, installs via `npx skills add`. The single most important architectural fact: **two copies of the skill exist in this repo — `skills/image-comprehension-ollama/` (canonical source) and `.agents/skills/image-comprehension-ollama/` (installed copy from `npx skills add`) — and they are byte-for-byte identical. Do not deduplicate or symlink them.**

## Known Gotchas

- **Byte-for-byte identical copies** in `skills/` and `.agents/skills/` — intentional (source vs installed). Do not deduplicate.
- **Dual timeout is contradictory**: shell wrapper timeout is configurable via `COMPREHEND_IMAGE_TIMEOUT_SECONDS` (default 180s), but Python inner timeout is hardcoded at 180s and says "fixed in the skill." Adjusting the env var only changes the outer wrapper — inner Python timeout stays 180s regardless.
- **`ensure_model_present()` does substring check** — e.g., having `my-moondream:1.8b` installed would incorrectly satisfy the check for `moondream:1.8b`. False positive.
- **Windows CI bypasses shell wrapper entirely** — runs Python script directly. Timeout wrapper layer never tested on Windows in CI.
- **`.gitignore` gitignores `.agents/skills/`** but the directory is already committed. Intended to prevent `npx skills add` from creating dirty working copies in the same repo.
- **`__pycache__/` is tracked** under `skills/image-comprehension-ollama/scripts/` — committed before gitignore was applied.
- **`prog="comprehend_image.sh"` in argparse** even though actual program is `comprehend_image.py` — so help text matches the user-facing shell wrapper.
- **No `references/` directory exists** anywhere — the skill has no reference files.
- **Old hardcoded JWT/keys may exist in git history** — from earlier commits. Rotate secrets if public.

## Conventions

- **Skill naming**: lowercase letters, numbers, hyphens only. `name` in SKILL.md frontmatter must match directory.
- **Python**: stdlib ONLY — no pip packages, no virtualenvs. Uses only stdlib modules.
- **Shell**: `set -euo pipefail`. Minimal — just a configurable timeout + path-to-python3 discovery.
- **Output discipline**: stdout = description only, stderr = all logs/errors/status. Allows `$(script.sh --image img.png 2>/dev/null)` for clean capture.
- **Model lifecycle**: loads on demand, processes one image, immediately unloads (`keep_alive: "0"`). `atexit` handler kills managed Ollama server.
- **Model resolution**: `--model` flag > `OLLAMA_VISION_MODEL` env > hardcoded `moondream:1.8b`.
- **Conventional Commits**: `feat:`, `fix:`, `docs:`. Branch: `feature/*`, `fix/*`, `docs/*`.
- **PR checklist**: validate name matches directory, description 1-1024 chars, SKILL.md under 500 lines, no secrets, Python syntax passes.
- **No concurrency** — each call monopolizes GPU/CPU. Run one at a time.

## Structure Map

```
skill-image-comprehension-ollama/
├── AGENTS.md                          — Agent guidelines (build/test/PR checklist)
├── CONTRIBUTING.md                    — Contributor setup + testing guide
├── LICENSE                            — MIT
├── README.md                          — User-facing install & usage docs
├── VERSIONS.md                        — Semver history (current: 1.0.0)
├── skills-lock.json                   — npx skills lockfile
├── .gitignore                         — __pycache__, venv, .DS_Store, IDE dirs, /.agents/skills/
├── docs/
│   └── hero.png                       — Hero image for README
├── .github/
│   └── workflows/
│       └── ci.yml                     — Cross-platform CI (ubuntu/macos/windows)
├── skills/
│   └── image-comprehension-ollama/    — ← CANONICAL SKILL COPY
│       ├── SKILL.md                   — Agent instructions (198 lines)
│       └── scripts/
│           ├── comprehend_image.sh    — Outer shell wrapper (timeout)
│           └── comprehend_image.py    — Core: validates image, calls Ollama /api/generate
└── .agents/
    └── skills/
        └── image-comprehension-ollama/    — ← INSTALLED COPY (identical)
```

## Entry Points

All usage from repo root:

| Action | Command |
|--------|---------|
| Describe image (defaults) | `./skills/.../scripts/comprehend_image.sh --image /path/to/img.png` |
| Ask specific question | `./skills/.../scripts/comprehend_image.sh --image chart.png --prompt "Key trends?"` |
| Extract text (OCR-like) | `./skills/.../scripts/comprehend_image.sh --image receipt.jpg --prompt "Transcribe all text."` |
| Different model | `./skills/.../scripts/comprehend_image.sh --image photo.png --model llava:7b` |
| Env var model | `OLLAMA_VISION_MODEL=llava:7b ./skills/.../scripts/comprehend_image.sh --image photo.png` |
| Smoke test | `./skills/.../scripts/comprehend_image.sh --test` |
| Clean output capture | `description=$(./skills/.../scripts/comprehend_image.sh --image img.png 2>/dev/null)` |
| Custom timeout | `COMPREHEND_IMAGE_TIMEOUT_SECONDS=600 ./skills/.../scripts/comprehend_image.sh --image img.png` |
| Install via npx | `npx skills add aosama/image-comprehension-ollama` → `~/.agents/skills/` |
| Clone + symlink | `git clone <repo> && ln -s "$(pwd)/skills/image-comprehension-ollama" "$HOME/.agents/skills/"` |

**Prerequisites**: Ollama installed + running (`ollama serve`), Python 3 on PATH, vision model pulled (`ollama pull moondream:1.8b`). Supported formats: PNG, JPEG, GIF, WebP, BMP.

## What to Verify

1. **Python syntax**: `python3 -m py_compile comprehend_image.py`.
2. **Shell syntax**: `shellcheck comprehend_image.sh`.
3. **Smoke test**: `--test` creates minimal PNG, runs comprehension, verifies model loads/describes/unloads, temp dir cleaned.
4. **Model resolution order**: `--model` > `OLLAMA_VISION_MODEL` > `moondream:1.8b`.
5. **Output separation**: stdout = description, stderr = logs.
6. **Model substring false-positive**: test with models whose names contain other model names.
7. **Dual timeout**: verify behavior when outer timeout > inner timeout. Inner timeout message says "fixed" — misleading.
8. **CI** — Cross-platform (ubuntu/macos/windows), Ollama installs, server starts, model pulls, syntax check, smoke test.
9. **Skill spec compliance**: `npx skills-ref validate ./skills/image-comprehension-ollama`.
10. **Security** — No API keys, no network beyond localhost:11434, no file writes (besides temp test images), no shell injection (subprocess args).
11. **Git history** — Old JWT/keys in earlier commits. Rotate if repo is public.

## Maintenance Snapshot

- Last verified: 2026-04-30
- Changes since last verify: initial creation
