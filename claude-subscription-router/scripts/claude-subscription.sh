#!/bin/bash
# Simple bash wrapper for claude-subscription.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/claude-subscription.py" "$@"