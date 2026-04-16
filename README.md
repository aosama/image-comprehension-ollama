# image-comprehension-ollama

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ollama](https://img.shields.io/badge/Ollama-required-blue.svg)](https://ollama.com)

Give your coding agent eyes. This skill lets AI agents that can't natively see images understand them by running a local Ollama vision model.

When an agent encounters a screenshot, chart, diagram, photo, or any image file, it calls this skill to get a detailed text description of the image contents. Everything runs locally — no API keys, no cloud services, no data leaving your machine.

## Features

- 🔒 **Fully local** — uses Ollama, no API keys or cloud services needed
- 🖼️ **Multi-format** — supports PNG, JPEG, GIF, WebP, BMP
- ⚡ **On-demand loading** — model loads when needed, unloads after to free memory
- 🔧 **Configurable model** — use any Ollama vision model, defaults to `gemma4:e2b`
- 📝 **Custom prompts** — ask specific questions about images, not just "describe it"
- 🔁 **Auto-start Ollama** — automatically starts a local Ollama server if one isn't running (macOS app bundle and Linux PATH supported)

## Repository structure

```
image-comprehension-ollama/
├── .gitignore
├── AGENTS.md                          # Guidelines for AI agents
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── VERSIONS.md                        # Version tracking
└── skills/
    └── image-comprehension-ollama/    # Skill directory (matches frontmatter name)
        ├── SKILL.md                  # Skill instructions and metadata
        └── scripts/
            ├── comprehend_image.py    # Core Python script
            └── comprehend_image.sh   # Shell wrapper with timeout
```

This follows the [Agent Skills specification](https://agentskills.io/specification.md).

## Prerequisites

1. **[Ollama](https://ollama.com)** — Install it:

   **macOS** — [Download Ollama.dmg](https://ollama.com/download) (requires macOS 14 Sonoma or later), then drag to Applications and launch.

   **Linux** — Run the install script:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

   **Windows** — [Download the installer](https://ollama.com/download) from the website.

   Once installed, make sure Ollama is running:
   ```bash
   ollama serve
   ```

2. **python3** — Available on your PATH. No virtual environment required.

3. **A vision model** — Pull the default model (or whichever you prefer):
   ```bash
   ollama pull gemma4:e2b
   ```

## Installation

### Option 1: `npx skills add` (recommended)

```bash
npx skills add aosama/image-comprehension-ollama
```

This installs the skill to `.agents/skills/` following the [Agent Skills spec](https://agentskills.io).

### Option 2: Clone + symlink

```bash
# Clone the repo
git clone https://github.com/aosama/image-comprehension-ollama.git

# Symlink to the standard skill location
mkdir -p "$HOME/.agents/skills"
ln -s "$(pwd)/image-comprehension-ollama/skills/image-comprehension-ollama" "$HOME/.agents/skills/image-comprehension-ollama"
```

### Option 3: Manual path

If you prefer not to use the symlink, just clone the repo and call the script by its full path:

```bash
git clone https://github.com/aosama/image-comprehension-ollama.git
cd image-comprehension-ollama
./skills/image-comprehension-ollama/scripts/comprehend_image.sh --image /path/to/image.png
```

## Usage

```bash
# Basic usage — describe an image
./skills/image-comprehension-ollama/scripts/comprehend_image.sh --image screenshot.png

# Ask a specific question about an image
./skills/image-comprehension-ollama/scripts/comprehend_image.sh --image chart.png --prompt "What are the key trends in this chart?"

# Extract text from an image
./skills/image-comprehension-ollama/scripts/comprehend_image.sh --image receipt.jpg --prompt "Extract and transcribe all visible text."

# Use a different model
./skills/image-comprehension-ollama/scripts/comprehend_image.sh --image photo.png --model llava:7b

# Or set model via environment variable
OLLAMA_VISION_MODEL=llava:7b ./skills/image-comprehension-ollama/scripts/comprehend_image.sh --image photo.png

# Run the built-in smoke test
./skills/image-comprehension-ollama/scripts/comprehend_image.sh --test

# Show help
./skills/image-comprehension-ollama/scripts/comprehend_image.sh --help
```

## Configuration

| Setting | CLI flag | Environment variable | Default |
|---------|----------|---------------------|---------|
| Vision model | `--model` | `OLLAMA_VISION_MODEL` | `gemma4:e2b` |
| Timeout | — | `COMPREHEND_IMAGE_TIMEOUT_SECONDS` | `180` |

### Using a different model

Any Ollama vision model works. Popular options:

```bash
# Pull an alternative model
ollama pull llava:7b

# Use it
./skills/image-comprehension-ollama/scripts/comprehend_image.sh --image photo.png --model llava:7b
```

The `--model` flag takes precedence over `OLLAMA_VISION_MODEL`. If neither is set, `gemma4:e2b` is used.

## Output

- **stdout** — The image description (capture this for programmatic use)
- **stderr** — Progress logs and error messages

```bash
# Capture only the description
description=$(./skills/image-comprehension-ollama/scripts/comprehend_image.sh --image photo.png 2>/dev/null)
```

## How it works

1. `comprehend_image.sh` wraps `comprehend_image.py` with a configurable timeout
2. The Python script validates the image exists and is a supported format
3. If Ollama isn't already running, it attempts to auto-start it (macOS app bundle or Linux `ollama` from PATH)
4. It checks the requested model is installed
5. It base64-encodes the image and sends it to Ollama's HTTP API
6. The model describes the image and the description is printed to stdout
7. The model unloads immediately (`keep_alive: 0`) to free resources

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Ollama is not responding` | Run `ollama serve` in a separate terminal |
| `Model 'xxx' not found` | Run `ollama pull xxx` to download it |
| `python3 is required but was not found` | Install Python 3 and ensure it's on your PATH |
| `Image file not found` | Check the path is correct and the file exists |

## License

This project is licensed under the [MIT License](LICENSE).