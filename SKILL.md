---
name: image-comprehension-ollama
description: "You cannot see images — this skill gives you vision. When you encounter an image file (screenshot, photo, diagram, chart, scan), use this skill to understand what is in it. A local vision model (default: gemma4:e2b via Ollama) describes the image back to you in text, so you can act on visual information you otherwise could not perceive. Supports PNG, JPEG, GIF, WebP, BMP."
---

# Image Comprehension with Ollama

**You are not a vision model. You cannot see images.** This skill bridges that gap.

When you encounter an image file — whether from a screenshot the user shared, a photo on disk, a rendered webpage capture, a chart, a diagram, or any other visual artifact — this skill lets you understand its contents. It runs a local vision model that analyzes the image and returns a text description to stdout. The model loads on demand, describes the image, and unloads immediately to free memory.

Use this skill proactively whenever visual information is relevant to your task and you cannot directly perceive it.

## When to use this skill

- A user shares a screenshot and asks you to debug, review, or explain it
- You take a browser screenshot for QA and need to understand what rendered on screen (Playwright snapshots show structure; this skill shows you what it actually looks like)
- You encounter image files in the repo (diagrams, charts, photos, scans)
- You need to extract text from an image (OCR-like use case)
- You need to verify visual output (e.g., does the UI look correct?)
- Any situation where a human would look at an image and you need the same information

## Prerequisites

- [Ollama](https://ollama.com) installed and running on your machine.
- `python3` available on your PATH. No virtual environment is required.
- A vision model pulled locally. By default the skill uses `gemma4:e2b`. Run once manually:
  ```bash
  ollama pull gemma4:e2b
  ```
  To use a different model, set the `OLLAMA_VISION_MODEL` environment variable or pass `--model`.

## Resolve the skill path first

Always call the script by absolute path. On this machine, and as a default convention, use:

```bash
$HOME/.agents/skills/image-comprehension-ollama/scripts/comprehend_image.sh
```

## Agent workflow

1. Obtain or confirm the image path from the user, or from a screenshot you took.
2. Decide what question to ask about the image:
   - For general descriptions: use the default prompt.
   - For specific information: provide a focused question via `--prompt`.
   - For text extraction: ask about text content explicitly.
3. Run the comprehension command.
4. The description is printed to stdout (progress logs go to stderr).
5. Use the returned description to complete your task — debug, verify, analyze, answer the user's question.

## Default prompt

If you do not provide `--prompt`, the skill uses:

```
Describe this image in detail
```

Override with `--prompt` for specific questions about the image. Better prompts produce better descriptions — be specific about what you need to know.

## Quick start

```bash
# Basic usage with default prompt and model
"$HOME/.agents/skills/image-comprehension-ollama/scripts/comprehend_image.sh" --image /path/to/image.png

# Custom question about the image
"$HOME/.agents/skills/image-comprehension-ollama/scripts/comprehend_image.sh" --image /path/to/screenshot.png --prompt "What text is visible in this screenshot?"

# Use a different model
"$HOME/.agents/skills/image-comprehension-ollama/scripts/comprehend_image.sh" --image /path/to/image.png --model llava:7b

# Use a different model via environment variable
OLLAMA_VISION_MODEL=llava:7b "$HOME/.agents/skills/image-comprehension-ollama/scripts/comprehend_image.sh" --image /path/to/image.png

# Analyze a chart or diagram
"$HOME/.agents/skills/image-comprehension-ollama/scripts/comprehend_image.sh" --image /path/to/diagram.png --prompt "Explain the flow and relationships in this diagram."

# Run the built-in smoke test
"$HOME/.agents/skills/image-comprehension-ollama/scripts/comprehend_image.sh" --test

# Show help
"$HOME/.agents/skills/image-comprehension-ollama/scripts/comprehend_image.sh" --help
```

## Supported image formats

- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)
- GIF (`.gif`)
- WebP (`.webp`)
- BMP (`.bmp`)

## Configuration

| Setting | CLI flag | Environment variable | Default |
|---------|----------|---------------------|---------|
| Vision model | `--model` | `OLLAMA_VISION_MODEL` | `gemma4:e2b` |
| Timeout | — | `COMPREHEND_IMAGE_TIMEOUT_SECONDS` | `180` |

- **Model**: Pass `--model <name>` on the command line, or set `OLLAMA_VISION_MODEL` in your environment. The CLI flag takes precedence. If neither is set, `gemma4:e2b` is used.
- **Timeout**: Set `COMPREHEND_IMAGE_TIMEOUT_SECONDS` to change the shell wrapper timeout (default 180 seconds). The inner Python script also enforces this as its maximum wait time for API calls.

## Timing

Image comprehension typically takes 5 to 60 seconds depending on:
- Image complexity and resolution
- Question complexity
- Hardware capabilities (CPU/GPU)

Progress logs are printed to stderr during comprehension so coding agents can see that work is still progressing.

## Options

- `--image <path>` — Path to the image file to analyze (required, unless using `--test`).
- `--prompt <text>` — Custom prompt/question for the image (default: "Describe this image in detail").
- `--model <name>` — Ollama model to use (default: `gemma4:e2b`, override with `OLLAMA_VISION_MODEL` env var).
- `--test` — Run the built-in smoke test.
- `--help` — Show the help text.

## Output

The image description is printed to **stdout**. Progress logs and error messages go to **stderr**.

To capture only the description:

```bash
description=$("$HOME/.agents/skills/image-comprehension-ollama/scripts/comprehend_image.sh" --image /path/to/image.png 2>/dev/null)
```

## Concurrency guidance

**Do not parallelize image comprehension requests.** Each comprehension may monopolize GPU/CPU resources. Run comprehension one at a time and wait for each to complete before starting the next.

## How it works

1. `comprehend_image.sh` forwards all arguments to `comprehend_image.py` using your existing `python3`.
2. The Python script validates the image path exists.
3. It checks that Ollama is running and the model is installed.
4. It encodes the image as base64 and sends a POST request to `http://localhost:11434/api/generate` with `keep_alive: "0"`.
5. The description is printed to stdout.
6. The `keep_alive: "0"` parameter unloads the model immediately after processing, freeing GPU/CPU memory.

If Ollama is not running or the model is not installed, the script prints a clear error to stderr and exits with a non-zero code. The agent should report the error to the user and suggest running `ollama serve` or `ollama pull <model>`.

## Example prompts

| Use case | Prompt example |
|----------|----------------|
| General description | `"Describe this image in detail"` (default) |
| Object detection | `"What objects are present in this image?"` |
| Text extraction | `"Extract and transcribe all visible text in this image."` |
| Chart analysis | `"What does this chart show? Describe the trends and key data points."` |
| UI/UX review | `"Describe the user interface elements and their layout."` |
| Document reading | `"What is the content of this document? Summarize the key points."` |
| Error diagnosis | `"What error or issue is shown in this screenshot?"` |
| Browser QA | `"Does this webpage render correctly? Describe the layout, any visual errors, and whether the content matches what you'd expect."` |
| Dark/light theme | `"Is this page in dark mode or light mode? Describe the color scheme and any theme-related issues."` |

## How to test the skill

```bash
# Run the built-in smoke test (creates a minimal test image)
"$HOME/.agents/skills/image-comprehension-ollama/scripts/comprehend_image.sh" --test

# Test with a real image
"$HOME/.agents/skills/image-comprehension-ollama/scripts/comprehend_image.sh" --image ~/Downloads/some-image.png
```

## Caveats

- The vision model can hallucinate details, misread text, or miss elements. Treat descriptions as strong evidence, not ground truth. When precision matters (e.g., reading error messages, checking exact UI text), cross-reference with accessibility snapshots, page source, or other tools.
- Small text, thin fonts, and low-contrast regions are the most common sources of misreadings. For OCR-critical tasks, ask the user to confirm key values.
- The description is only as good as your prompt. A vague prompt like "what is this" will produce a vague answer. A specific prompt like "read the error message in the red banner at the top of this screenshot" will produce a targeted answer.
- The model unloads after each call. If you need to analyze multiple images, expect a short load time on each call.

## Notes

- No API key is required — everything runs locally via Ollama's HTTP API.
- The Python code uses only the standard library.
- Progress logs go to stderr, description goes to stdout — easy to capture programmatically.
- On macOS, the script can automatically start a managed Ollama server if Ollama is installed via the Mac app but no server is running.