#!/bin/bash
# Claude Subscription Router — Bash wrapper
# Usage: ./route.sh "task description" [--agent developer] [--model opus] [...]
#
# Shorthand: first positional arg is the task, rest are flags.
# Example:
#   ./route.sh "Build landing page for clinic" --agent developer --model opus
#   ./route.sh "Fix auth bug" --project website-abd --agent developer

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# If first arg doesn't start with --, treat it as --task
if [[ $# -gt 0 && "${1:0:2}" != "--" ]]; then
    TASK="$1"
    shift
    python3 "$SCRIPT_DIR/router.py" --task "$TASK" "$@"
else
    python3 "$SCRIPT_DIR/router.py" "$@"
fi
