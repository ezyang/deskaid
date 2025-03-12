#!/bin/bash
set -e

echo "Running Pyright type checker with strict settings..."
python -m pyright codemcp

echo "Type checking completed successfully!"