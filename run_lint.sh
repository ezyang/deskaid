#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run Ruff linting
echo "Running Ruff linter..."

UNSAFE_CODES="F401,F841,I"

"${SCRIPT_DIR}/.venv/bin/python" -m ruff check --ignore "$UNSAFE_CODES" --fix codemcp/ test/

# Less safe autofixes
"${SCRIPT_DIR}/.venv/bin/python" -m ruff check --select "$UNSAFE_CODES" --unsafe-fixes --fix codemcp/ test/

echo "Lint completed successfully!"
