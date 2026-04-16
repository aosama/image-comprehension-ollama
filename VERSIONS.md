# image-comprehension-ollama Versions

Current versions of the skill. Agents can compare against local versions to check for updates.

| Skill | Version | Last Updated |
|-------|---------|--------------|
| image-comprehension-ollama | 1.0.0 | 2026-04-16 |

## Recent Changes

### 2026-04-16
- Initial open-source release
- Configurable vision model via `--model` flag and `OLLAMA_VISION_MODEL` env var (default: `gemma4:e2b`)
- Cross-platform Ollama auto-start (macOS app bundle + Linux PATH)
- Progress logs to stderr, description to stdout
- Model unloads after each call to free resources
- Built-in smoke test (`--test`)