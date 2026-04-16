#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly COMPREHEND_IMAGE_TIMEOUT_SECONDS="${COMPREHEND_IMAGE_TIMEOUT_SECONDS:-180}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found on PATH" >&2
  exit 1
fi

export COMPREHEND_IMAGE_TIMEOUT_SECONDS

exec python3 -c '
import os
import subprocess
import sys

timeout_seconds = int(os.environ["COMPREHEND_IMAGE_TIMEOUT_SECONDS"])

try:
    completed = subprocess.run(sys.argv[1:], timeout=timeout_seconds)
except subprocess.TimeoutExpired:
    print(
        f"[comprehend_image] ERROR: Command timed out after {timeout_seconds} seconds in comprehend_image.sh. "
        "This timeout is configurable via the COMPREHEND_IMAGE_TIMEOUT_SECONDS env var.",
        file=sys.stderr,
    )
    raise SystemExit(1)

raise SystemExit(completed.returncode)
' python3 "$SCRIPT_DIR/comprehend_image.py" "$@"