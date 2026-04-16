# Contributing to image-comprehension-ollama

Thank you for your interest in contributing! This project aims to stay simple and focused, so here are some guidelines.

## Development setup

1. **Fork and clone** the repository
2. Ensure [Ollama](https://ollama.com) is installed and `ollama serve` is running
3. Pull the default model: `ollama pull moondream:1.8b`
4. Ensure `python3` is on your PATH (the scripts use only the standard library)

## Making changes

1. Create a branch for your change: `git checkout -b my-feature`
2. Make your changes
3. Test them (see below)
4. Commit with a clear message
5. Push and open a pull request

## Testing

The skill includes a built-in smoke test:

```bash
./scripts/comprehend_image.sh --test
```

For manual testing, use any image:

```bash
./scripts/comprehend_image.sh --image /path/to/image.png
./scripts/comprehend_image.sh --image /path/to/image.png --model llava:7b
./scripts/comprehend_image.sh --image /path/to/image.png --prompt "What text is visible?"
```

### What to test

- Default model works (`--image` only)
- Custom model via `--model` flag
- Custom model via `OLLAMA_VISION_MODEL` env var
- `--prompt` customization
- `--test` smoke test
- `--help` output
- Error cases (missing file, unsupported format, Ollama not running)

## Code style

- **Shell** (`comprehend_image.sh`): Keep it minimal — it's a thin wrapper. Use `set -euo pipefail`.
- **Python** (`comprehend_image.py`): Standard library only. No external dependencies. Keep it as a single file.
- **Markdown**: Keep documentation concise and practical.

## Reporting issues

Open an issue on GitHub with:

- What you expected
- What actually happened
- Steps to reproduce
- Your OS, Python version, Ollama version, and model name