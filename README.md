# Claude Subscription Router

**OpenClaw Skill for Cost Optimization**

Routes heavy computational tasks to Claude CLI subscription mode to reduce OpenClaw on-demand billing costs by **75-80%**.

## Problem

When Anthropic switches from unlimited subscription to on-demand billing through OpenClaw:
- Costs can increase **4x** (from $200/month to $800/month)
- Heavy tasks (development, analysis, content) become expensive
- Need cost optimization without losing OpenClaw functionality

## Solution

Smart routing system:
```
Heavy Task → OpenClaw (orchestration) → Claude CLI (subscription) → Result
```

**Result:** $200/week → $40-50/week savings

## Quick Start

### Installation
```bash
# Download the skill
wget https://github.com/swats-ai/claude-subscription-router/releases/latest/download/claude-subscription-router.skill

# Install in OpenClaw
openclaw skills install claude-subscription-router.skill

# Or extract manually
unzip claude-subscription-router.skill
cd claude-subscription-router && ./scripts/install.sh
```

### Usage

**Automatic Detection** (recommended):
Once installed, your main OpenClaw agent will automatically route heavy tasks.

**Manual routing:**
```bash
# Standard version (2min timeout)
python3 ~/.openclaw/workspace/scripts/claude-subscription.py "Build React app" "react" "developer" "opus"

# Streaming version (no timeout, real-time output)
python3 ~/.openclaw/workspace/scripts/claude-subscription-streaming.py "Analyze 100-page document" "analysis" "analyst" "opus"
```

## Features

✅ **Cost Optimization**: 75-80% reduction in on-demand costs  
✅ **Context Preservation**: Full SOUL, IDENTITY, USER, memory context  
✅ **Two Versions**: Standard (quick) and streaming (long tasks)  
✅ **Auto-Detection**: Automatic routing of heavy tasks  
✅ **Multi-Environment**: Easy deployment across Mac minis  
✅ **No Configuration**: Works with standard OpenClaw setup  

## What Gets Routed

- **Development**: "create", "build", "develop", "code"
- **Content**: "write", "blog", "content", "copy"  
- **Analysis**: "analyze", "research", "strategy"
- **Design**: "design", "mockup", "wireframe"

## Requirements

- Python 3.6+
- [Claude CLI](https://claude.ai/cli) installed and authenticated
- OpenClaw workspace structure
- SQLite3 (included with Python)

## Cost Comparison

| Scenario | Before | After | Savings |
|----------|--------|-------|---------|
| **Heavy tasks only** | $200/week | $120/week | 40% |
| **+ Sonnet for agents** | $200/week | $80/week | 60% |
| **Full optimization** | $200/week | $40/week | 80% |

## Files

- `claude-subscription-router.skill` - Packaged skill (10KB)
- `claude-subscription-router/` - Source code and documentation
- `scripts/install.sh` - Automatic installation script

## Support

- 🐛 **Issues**: Open a GitHub issue
- 💬 **Discord**: [OpenClaw Community](https://discord.com/invite/clawd)
- 📖 **Docs**: See [SKILL.md](claude-subscription-router/SKILL.md) for detailed documentation

---

**Part of the [SWATS.ai](https://swats.ai) OpenClaw ecosystem**