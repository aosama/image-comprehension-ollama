# AGENTS.md

Guidelines for AI agents working in this repository.

## Repository Overview

This repository contains the **image-comprehension-ollama** skill — an Agent Skill that gives AI coding agents the ability to understand images by running a local Ollama vision model.

- **Name**: image-comprehension-ollama
- **GitHub**: [aosama/image-comprehension-ollama](https://github.com/aosama/image-comprehension-ollama)
- **License**: MIT

## Repository Structure

```
image-comprehension-ollama/
├── AGENTS.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── VERSIONS.md
└── skills/
    └── image-comprehension-ollama/
        ├── SKILL.md
        └── scripts/
            ├── comprehend_image.py
            └── comprehend_image.sh
```

## Agent Skills Specification

This skill follows the [Agent Skills spec](https://agentskills.io/specification.md).

### Required Frontmatter

```yaml
---
name: image-comprehension-ollama
description: "..."
license: MIT
compatibility: Requires Ollama and Python 3
metadata:
  author: aosama
  version: "1.0.0"
---
```

### Name Field Rules

- Lowercase letters, numbers, and hyphens only
- Must match the parent directory name exactly (`image-comprehension-ollama`)
- The skill directory lives under `skills/image-comprehension-ollama/`

### Optional Skill Directories

```
skills/image-comprehension-ollama/
├── SKILL.md        # Required — main instructions
└── scripts/        # Executable scripts
```

## Build / Test Commands

**Python syntax check:**
```bash
python3 -m py_compile skills/image-comprehension-ollama/scripts/comprehend_image.py
```

**Shell script check (if shellcheck is available):**
```bash
shellcheck skills/image-comprehension-ollama/scripts/comprehend_image.sh
```

**Smoke test (requires Ollama running with a vision model):**
```bash
./skills/image-comprehension-ollama/scripts/comprehend_image.sh --test
```

## Validation

Validate the skill against the Agent Skills spec:

```bash
npx skills-ref validate ./skills/image-comprehension-ollama
```

Checks that `SKILL.md` frontmatter is valid and naming conventions are followed.

## Git Workflow

### Branch Naming

- Features: `feature/description`
- Fixes: `fix/description`
- Documentation: `docs/description`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add new feature`
- `fix: resolve issue`
- `docs: update documentation`

### Pull Request Checklist

- [ ] `name` field matches directory name exactly
- [ ] `name` follows naming rules (lowercase, hyphens, no `--`)
- [ ] `description` is 1-1024 chars with trigger phrases
- [ ] `SKILL.md` is under 500 lines
- [ ] No sensitive data or credentials
- [ ] Python syntax check passes