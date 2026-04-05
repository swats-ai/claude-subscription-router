#!/bin/bash
# Installation script for Claude Subscription Router skill

set -e

WORKSPACE_DIR="$HOME/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE_DIR/scripts"

echo "🤖 Installing Claude Subscription Router..."

# Create scripts directory if it doesn't exist
mkdir -p "$SCRIPTS_DIR"

# Copy scripts
echo "📁 Copying scripts to workspace..."
cp "$(dirname "$0")/claude-subscription.py" "$SCRIPTS_DIR/"
cp "$(dirname "$0")/claude-subscription-streaming.py" "$SCRIPTS_DIR/"
cp "$(dirname "$0")/claude-subscription.sh" "$SCRIPTS_DIR/"

# Make executable
chmod +x "$SCRIPTS_DIR/claude-subscription.py"
chmod +x "$SCRIPTS_DIR/claude-subscription-streaming.py"
chmod +x "$SCRIPTS_DIR/claude-subscription.sh"

echo "✅ Scripts installed successfully"

# Test installation
echo "🧪 Testing installation..."
if python3 "$SCRIPTS_DIR/claude-subscription.py" "Test installation" "" "" "sonnet" >/dev/null 2>&1; then
    echo "✅ Installation test passed"
else
    echo "⚠️  Installation test failed - check Claude CLI authentication"
    echo "   Run: claude auth login"
fi

echo ""
echo "🎯 Claude Subscription Router installed!"
echo "   Scripts location: $SCRIPTS_DIR"
echo "   Usage: python3 $SCRIPTS_DIR/claude-subscription.py '<task>' '[memory_query]' '[agent_profile]' '[model]'"
echo ""
echo "💡 Scripts available:"
echo "   Standard: claude-subscription.py (2min timeout)"
echo "   Streaming: claude-subscription-streaming.py (no timeout, real-time)"
echo "💡 For long tasks, use streaming version with 'exec background:true'"