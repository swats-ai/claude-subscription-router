---
name: claude-subscription-router
description: Cost optimization system for OpenClaw that routes heavy computational tasks (development, analysis, content creation) to Claude CLI subscription mode while preserving full OpenClaw context. Use when Anthropic pricing changes from unlimited to on-demand billing, or when needing to minimize token costs for resource-intensive work. Automatically detects coding tasks, long-form analysis, content writing, and design work to route through subscription instead of on-demand billing.
---

# Claude Subscription Router

Routes heavy computational tasks to Claude CLI subscription mode to minimize on-demand billing costs while preserving full OpenClaw context and capabilities.

## Problem Solved

When Anthropic switches from unlimited subscription billing to on-demand billing through OpenClaw, costs can increase 4x or more. This skill provides automatic cost optimization by routing heavy tasks to Claude CLI (which maintains subscription pricing) while keeping lightweight orchestration in OpenClaw.

## How It Works

```
Heavy Task Request → OpenClaw (minimal orchestration) → Claude CLI (subscription) → Result
```

**Cost comparison:**
- **Before:** All tokens on-demand ($200/week)
- **After:** Orchestration on-demand + heavy work subscription (~$40-50/week)

## Installation

### Step 1: Copy Scripts
```bash
# Copy to your OpenClaw workspace
cp scripts/claude-subscription.py ~/.openclaw/workspace/scripts/
cp scripts/claude-subscription-streaming.py ~/.openclaw/workspace/scripts/
cp scripts/claude-subscription.sh ~/.openclaw/workspace/scripts/
chmod +x ~/.openclaw/workspace/scripts/claude-subscription.*
```

### Step 2: Test Installation
```bash
cd ~/.openclaw/workspace/scripts
./claude-subscription.py "Test system functionality" "" "" "sonnet"
```

### Step 3: Configure Agent Models (Optional)
If you want additional savings, configure agents to use Sonnet instead of Opus:

**Gateway config changes:**
```json
"model": {
  "primary": "anthropic/claude-sonnet-4-20250514",
  "fallback": ["anthropic/claude-sonnet-4-20250514"]
}
```

**Keep Opus for PM agents only:**
```json
"agents": {
  "pm-client1": { "model": "anthropic/claude-opus-4-6" },
  "pm-client2": { "model": "anthropic/claude-opus-4-6" }
}
```

## Usage

### Automatic Detection (Recommended)
Once installed, the main OpenClaw agent automatically detects and routes heavy tasks:

**Triggers automatic routing:**
- "Create/build/develop/code"
- "Write/blog/content/copy" 
- "Analyze/research/strategy"
- "Design/mockup/wireframe"

### Manual Routing

**Standard (with timeout protection):**
```bash
exec: python3 ~/.openclaw/workspace/scripts/claude-subscription.py "task description" "memory keywords" "agent profile" "model"
```

**Streaming (no timeout, real-time output):**
```bash
exec background:true: python3 ~/.openclaw/workspace/scripts/claude-subscription-streaming.py "task description" "memory keywords" "agent profile" "model"
```

**Parameters:**
1. **task** (required) - Full task description
2. **memory_query** (optional) - Keywords for memory search
3. **agent_profile** (optional) - developer, seo, writer, designer, etc.
4. **model** (optional) - opus, sonnet, haiku (default: opus)

### Examples

**Development (streaming for long tasks):**
```bash
exec background:true: python3 ~/.openclaw/workspace/scripts/claude-subscription-streaming.py "Build React authentication component with JWT" "react auth login" "developer" "opus"
```

**Content Writing:**
```bash
./claude-subscription.py "Write comprehensive guide for small business SEO" "SEO business marketing" "writer" "sonnet"
```

**Analysis:**
```bash
./claude-subscription.py "Analyze competitive landscape for fintech startups" "fintech competition analysis" "analyst" "opus"
```

## Context Preservation

The scripts automatically include:
- **SOUL.md** - Personality and behavioral rules
- **IDENTITY.md** - Agent identity and role
- **USER.md** - User information and preferences
- **Memory Search** - Relevant historical context
- **Agent Profile** - Role-specific instructions

## Cost Optimization Guidelines

### Tier 1: Maximum Savings
- Default model: Sonnet for all non-PM agents
- Heavy tasks: Routed to Claude CLI subscription
- **Savings: ~75-80%**

### Tier 2: Moderate Savings
- Default model: Keep Opus for critical agents
- Heavy tasks: Routed to Claude CLI subscription
- **Savings: ~40-50%**

### Tier 3: Minimal Impact
- All agents: Keep current Opus configuration
- Heavy tasks only: Routed to Claude CLI subscription
- **Savings: ~30-40%**

## Deployment Across Environments

### Multi-Mac Mini Setup
1. Package this skill: `scripts/package_skill.py claude-subscription-router`
2. Install on target machines: Load the .skill file in OpenClaw
3. Ensure Claude CLI is installed: `curl -sSL https://claude.ai/cli/install | bash`
4. Test on each machine: Run test command above

### Required Dependencies
- Python 3.6+
- Claude CLI installed and authenticated
- SQLite3 (standard with Python)
- OpenClaw workspace structure

### Configuration Variables
The scripts read from standard OpenClaw workspace files:
- `~/.openclaw/workspace/SOUL.md`
- `~/.openclaw/workspace/IDENTITY.md` 
- `~/.openclaw/workspace/USER.md`
- `~/.openclaw/workspace/memory.db`

No additional configuration required.

## Monitoring and Debugging

### Check Script Status
```bash
python3 ~/.openclaw/workspace/scripts/claude-subscription.py --version
```

### Monitor Usage Patterns
```sql
-- Check recent routing decisions
SELECT date, content FROM daily_log 
WHERE key LIKE '%subscription%' 
ORDER BY date DESC LIMIT 10;
```

### Common Issues

**Claude CLI not authenticated:**
```bash
claude auth login
```

**Permission errors:**
```bash
chmod +x ~/.openclaw/workspace/scripts/claude-subscription.*
```

**Timeout issues:**
- Use streaming version: `claude-subscription-streaming.py` 
- Run with `exec background:true` for long tasks
- Break large tasks into smaller parts
- Standard timeout: 2 minutes

### Script Versions

**claude-subscription.py** - Standard version with 2-minute timeout
- Good for: Quick tasks, testing, debugging
- Returns complete output when done
- Safe timeout protection

**claude-subscription-streaming.py** - Streaming version with no timeout
- Good for: Long tasks, development, content creation
- Real-time output display
- No timeout limits
- Use with `exec background:true`

## Integration with Existing Workflows

This skill integrates seamlessly with:
- **PM Pipeline:** Heavy development tasks routed automatically
- **Content Creation:** Long-form writing uses subscription
- **Code Review:** Analysis tasks optimized for cost
- **Research Tasks:** Deep analysis leverages unlimited tokens

The routing is transparent - users don't need to change their request patterns.

## Security Considerations

- Scripts operate in OpenClaw workspace directory
- No external network calls except to Claude CLI
- Memory access is read-only
- Standard file permissions apply

Audit the scripts before deployment in sensitive environments.