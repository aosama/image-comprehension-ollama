#!/usr/bin/env python3
"""Comprehend an image with Ollama vision model and output the description to stdout."""

from __future__ import annotations

import atexit
import argparse
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Never

DEFAULT_MODEL_NAME = "moondream:1.8b"
DEFAULT_PROMPT = "Describe this image in detail"
DEFAULT_OLLAMA_HOST = "127.0.0.1:11434"
OLLAMA_COMMAND_TIMEOUT_SECONDS = 180
OLLAMA_READY_RETRY_COUNT = 15
OLLAMA_READY_RETRY_DELAY_SECONDS = 1
PROGRESS_LOG_INTERVAL_SECONDS = 5
SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
MAC_APP_OLLAMA_RESOURCES_DIR = Path("/Applications/Ollama.app/Contents/Resources")

_OLLAMA_ENV: dict[str, str] | None = None
_MANAGED_OLLAMA_SERVER: subprocess.Popen[str] | None = None
_MANAGED_OLLAMA_SERVER_CMD: list[str] | None = None
_MAC_RESOURCES_DIR: Path | None = None


def resolve_model_name() -> str:
    """Resolve the model name from env var or default."""
    return os.environ.get("OLLAMA_VISION_MODEL", DEFAULT_MODEL_NAME)


def log(message: str) -> None:
    print(f"[comprehend_image] {message}", file=sys.stderr)


def fail(message: str) -> Never:
    raise SystemExit(f"[comprehend_image] ERROR: {message}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="comprehend_image.sh",
        description="Analyze an image with Ollama vision model and output description to stdout.",
    )
    parser.add_argument(
        "--image",
        required=False,
        help="path to the image file to analyze",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help=f"text prompt for image analysis (default: '{DEFAULT_PROMPT}')",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"Ollama model to use (default: '{DEFAULT_MODEL_NAME}', override with OLLAMA_VISION_MODEL env var)",
    )
    parser.add_argument("--test", action="store_true", help="run a smoke test")
    return parser.parse_args(argv)


def resolve_ollama_env() -> dict[str, str]:
    global _OLLAMA_ENV

    if _OLLAMA_ENV is not None:
        return _OLLAMA_ENV

    env = os.environ.copy()

    # Check if Ollama is already reachable — if so, use it as-is.
    if is_ollama_reachable(env):
        log("Ollama is already running, using existing server.")
        _OLLAMA_ENV = env
        return _OLLAMA_ENV

    # Try to start a managed server. On macOS, this may use the app bundle;
    # on Linux and other platforms, this uses ollama from PATH.
    server_cmd = find_ollama_server_command()

    if server_cmd is not None and "OLLAMA_HOST" not in env:
        env["OLLAMA_HOST"] = f"127.0.0.1:{find_available_local_port()}"
        start_managed_ollama_server(server_cmd, env)

    _OLLAMA_ENV = env
    return _OLLAMA_ENV


def is_ollama_reachable(env: dict[str, str]) -> bool:
    """Check whether Ollama is already reachable at the configured host."""
    host = env.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    url = f"http://{host}" if not host.startswith("http") else host
    try:
        request = urllib.request.Request(f"{url}/api/tags", method="GET")
        with urllib.request.urlopen(request, timeout=3):
            return True
    except Exception:
        return False


def find_ollama_server_command() -> list[str] | None:
    """Find the ollama server command for the current platform.

    On macOS, prefer the app bundle binary (which needs OLLAMA_LIBRARY_PATH).
    On Linux and other platforms, use ollama from PATH.
    Returns None if ollama cannot be found.
    """
    if sys.platform == "darwin":
        resources_dir = find_ollama_app_resources_dir()
        if resources_dir is not None:
            # Store resources_dir for OLLAMA_LIBRARY_PATH injection
            global _MAC_RESOURCES_DIR
            _MAC_RESOURCES_DIR = resources_dir
            return [str(resources_dir / "ollama"), "serve"]

    # On Linux and other platforms, or macOS without the app bundle
    ollama_path = shutil.which("ollama")
    if ollama_path is not None:
        return [ollama_path, "serve"]

    return None


def find_ollama_app_resources_dir() -> Path | None:
    """Find the Ollama app bundle Resources directory on macOS."""
    if sys.platform != "darwin":
        return None

    candidates: list[Path] = []
    ollama_path = shutil.which("ollama")
    if ollama_path:
        resolved_ollama_path = Path(ollama_path).resolve()
        candidates.append(resolved_ollama_path.parent)
    candidates.append(MAC_APP_OLLAMA_RESOURCES_DIR)

    for candidate in candidates:
        if (candidate / "ollama").is_file() and any(candidate.glob("mlx_metal_v*")):
            return candidate

    return None


def find_available_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def start_managed_ollama_server(command: list[str], env: dict[str, str]) -> None:
    global _MANAGED_OLLAMA_SERVER, _MANAGED_OLLAMA_SERVER_CMD, _MAC_RESOURCES_DIR

    if _MANAGED_OLLAMA_SERVER is not None:
        return

    # macOS app bundle needs OLLAMA_LIBRARY_PATH set
    if _MAC_RESOURCES_DIR is not None and "OLLAMA_LIBRARY_PATH" not in env:
        env["OLLAMA_LIBRARY_PATH"] = str(_MAC_RESOURCES_DIR)
        log(f"Using Ollama app Resources for OLLAMA_LIBRARY_PATH: {_MAC_RESOURCES_DIR}")

    _MANAGED_OLLAMA_SERVER_CMD = command
    command_text = format_command(command)
    log(f"Starting a managed Ollama server on {env['OLLAMA_HOST']}: {command_text}")
    _MANAGED_OLLAMA_SERVER = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        env=env,
    )
    atexit.register(stop_managed_ollama_server)


def stop_managed_ollama_server() -> None:
    global _MANAGED_OLLAMA_SERVER

    if _MANAGED_OLLAMA_SERVER is None:
        return

    if _MANAGED_OLLAMA_SERVER.poll() is None:
        _MANAGED_OLLAMA_SERVER.terminate()
        try:
            _MANAGED_OLLAMA_SERVER.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _MANAGED_OLLAMA_SERVER.kill()
            _MANAGED_OLLAMA_SERVER.wait(timeout=5)

    _MANAGED_OLLAMA_SERVER = None


def ollama_api_url() -> str:
    host = resolve_ollama_env().get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    return f"http://{host}"


def normalize_image_path(raw_path: str) -> Path:
    """Normalize a raw image path string into a resolved Path.

    Handles Unicode normalization (e.g. macOS uses narrow no-break space
    U+202F instead of regular space in filenames like screenshots) and
    tilde expansion.
    """
    import unicodedata

    expanded = unicodedata.normalize("NFC", os.path.expanduser(raw_path))
    # Try the normalized path as-is first
    candidate = Path(expanded).resolve()
    if candidate.is_file():
        return candidate

    # If the exact path doesn't exist, try replacing common Unicode
    # space look-alikes with a regular space and searching the parent dir
    parent = candidate.parent
    if parent.is_dir():
        target_name = candidate.name
        # Replace narrow no-break space (U+202F) and other Unicode spaces
        normalized_name = unicodedata.normalize("NFKC", target_name)
        if normalized_name != target_name:
            alt_path = parent / normalized_name
            if alt_path.is_file():
                return alt_path.resolve()

        # Fuzzy: try matching against actual directory entries by NFC-normalized name
        normalized_compare = unicodedata.normalize("NFKC", target_name).casefold()
        for entry in parent.iterdir():
            if unicodedata.normalize("NFKC", entry.name).casefold() == normalized_compare:
                return entry.resolve()

    return candidate


def validate_image_path(image_path: Path) -> None:
    if not image_path.is_file():
        # Provide helpful message with parent directory listing if available
        parent = image_path.parent
        extra = ""
        if parent.is_dir():
            matches = list(parent.glob(f"{image_path.stem}*"))
            if matches:
                names = ", ".join(m.name for m in matches[:5])
                extra = f" Similar files in {parent}: {names}"
        fail(f"Image file not found: {image_path}.{extra}")
    if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        fail(
            f"Unsupported image format: {image_path.suffix}. "
            f"Supported: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
        )


def create_test_image() -> Path:
    """Create a valid minimal test image for smoke tests."""
    test_dir = Path(tempfile.mkdtemp(prefix="comprehend-image-test-"))
    test_image = test_dir / "test_image.png"

    minimal_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAEklEQVR42mP4n2KEBzGMSmNDACBmnjUIeg0MAAAAAElFTkSuQmCC"
    )
    test_image.write_bytes(minimal_png)
    return test_image


def format_command(command: list[str]) -> str:
    import shlex

    return " ".join(shlex.quote(part) for part in command)


def run_ollama_command(
    command: list[str],
    *,
    operation_name: str,
    show_heartbeat: bool = False,
    capture_stdout: bool = True,
) -> subprocess.CompletedProcess[str]:
    command_text = format_command(command)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        env=resolve_ollama_env(),
    )
    start_time = time.monotonic()
    next_progress_log_seconds = PROGRESS_LOG_INTERVAL_SECONDS

    log(f"Starting {operation_name}: {command_text}")

    while True:
        return_code = process.poll()
        elapsed_seconds = int(time.monotonic() - start_time)

        if return_code is not None:
            stdout_text, stderr_text = process.communicate()
            stdout_text = stdout_text or ""
            stderr_text = stderr_text or ""
            log(
                f"Finished {operation_name} in {elapsed_seconds}s with exit code {return_code}."
            )
            return subprocess.CompletedProcess(
                command, return_code, stdout_text, stderr_text
            )

        if elapsed_seconds >= OLLAMA_COMMAND_TIMEOUT_SECONDS:
            process.kill()
            stdout_text, stderr_text = process.communicate()
            stdout_text = stdout_text or ""
            stderr_text = stderr_text or ""
            details = stderr_text.strip() or stdout_text.strip()
            message = (
                "Command timed out after "
                f"{OLLAMA_COMMAND_TIMEOUT_SECONDS} seconds during {operation_name}: {command_text}. "
                "This timeout is fixed in the skill."
            )
            if details:
                message = f"{message} Details: {details}"
            fail(message)

        if show_heartbeat and elapsed_seconds >= next_progress_log_seconds:
            remaining_seconds = OLLAMA_COMMAND_TIMEOUT_SECONDS - elapsed_seconds
            log(
                f"Still waiting for {operation_name}... {elapsed_seconds}s elapsed, "
                f"{remaining_seconds}s until timeout."
            )
            next_progress_log_seconds += PROGRESS_LOG_INTERVAL_SECONDS

        time.sleep(1)


def ensure_ollama_ready() -> None:
    log("Checking whether Ollama is reachable...")
    for attempt in range(OLLAMA_READY_RETRY_COUNT):
        result = run_ollama_command(
            ["ollama", "list"],
            operation_name="Ollama availability check",
            capture_stdout=True,
        )
        if result.returncode == 0:
            log("Ollama is reachable.")
            return
        if attempt < OLLAMA_READY_RETRY_COUNT - 1:
            time.sleep(OLLAMA_READY_RETRY_DELAY_SECONDS)
    fail("Ollama is not responding. Is 'ollama serve' running?")


def ensure_model_present(model_name: str) -> None:
    log(f"Checking whether model '{model_name}' is installed...")
    result = run_ollama_command(
        ["ollama", "list"],
        operation_name="model availability check",
        capture_stdout=True,
    )
    if result.returncode != 0:
        fail(
            result.stderr.strip()
            or result.stdout.strip()
            or "Failed to query Ollama models."
        )

    if model_name not in result.stdout:
        fail(f"Model '{model_name}' not found. Run: ollama pull {model_name}")

    log(f"Model '{model_name}' is installed.")


def encode_image_to_base64(image_path: Path) -> str:
    """Read an image file and return its base64-encoded content."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def comprehend_image_via_api(image_path: Path, prompt: str, model_name: str) -> str:
    """
    Send image to Ollama vision model via HTTP API and return the description.

    Uses the /api/generate endpoint with base64-encoded image.
    """
    validate_image_path(image_path)
    log(f"Analyzing image: {image_path}")
    log(f"Prompt: {prompt}")
    log(f"Model: {model_name}")

    image_base64 = encode_image_to_base64(image_path)

    payload = {
        "model": model_name,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
        "keep_alive": "0",
    }

    url = f"{ollama_api_url()}/api/generate"
    request_data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=request_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    log(f"Starting image comprehension via API: POST {url}")
    start_time = time.monotonic()
    next_progress_log_seconds = PROGRESS_LOG_INTERVAL_SECONDS

    try:
        with urllib.request.urlopen(
            request, timeout=OLLAMA_COMMAND_TIMEOUT_SECONDS
        ) as response:
            while True:
                elapsed_seconds = int(time.monotonic() - start_time)

                if elapsed_seconds >= next_progress_log_seconds:
                    remaining_seconds = OLLAMA_COMMAND_TIMEOUT_SECONDS - elapsed_seconds
                    log(
                        f"Still waiting for image comprehension... {elapsed_seconds}s elapsed, "
                        f"{remaining_seconds}s until timeout."
                    )
                    next_progress_log_seconds += PROGRESS_LOG_INTERVAL_SECONDS

                try:
                    response_data = response.read()
                    break
                except urllib.error.URLError:
                    time.sleep(1)

            elapsed_seconds = int(time.monotonic() - start_time)
            log(f"Finished image comprehension via API in {elapsed_seconds}s.")

            result = json.loads(response_data.decode("utf-8"))

            if "error" in result:
                fail(f"API error: {result['error']}")

            if "response" not in result:
                fail(f"Unexpected API response: {result}")

            description = result["response"].strip()
            if not description:
                fail("Image comprehension returned no output.")

            return description

    except urllib.error.URLError as e:
        fail(f"Failed to connect to Ollama API: {e}")
    except json.JSONDecodeError as e:
        fail(f"Failed to parse API response: {e}")


def run_smoke_test(model_name: str | None = None) -> None:
    model = model_name or resolve_model_name()
    log("Running smoke test...")
    ensure_ollama_ready()
    ensure_model_present(model)

    test_image = create_test_image()
    try:
        description = comprehend_image_via_api(
            test_image, "What do you see in this image?", model
        )
        log(
            f"Smoke test succeeded. Description ({len(description)} chars): {description[:100]}..."
        )
    finally:
        shutil.rmtree(test_image.parent, ignore_errors=True)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    model_name = args.model or resolve_model_name()

    if args.test:
        run_smoke_test(args.model)
        return 0

    if not args.image:
        fail("No image path given. Use --image /path/to/image or --help.")

    image_path = normalize_image_path(args.image)
    prompt = args.prompt if args.prompt else DEFAULT_PROMPT

    ensure_ollama_ready()
    ensure_model_present(model_name)
    description = comprehend_image_via_api(image_path, prompt, model_name)
    print(description)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))