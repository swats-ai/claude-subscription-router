#!/usr/bin/env python3
"""
Claude Subscription Router
Routes heavy tasks to Claude CLI (Max subscription) while preserving OpenClaw context.

Usage:
    python3 router.py --task "Build a landing page" --model opus
    python3 router.py --task "Fix auth bug" --agent developer --project website-abd
    python3 router.py --task "Create SEO report" --dry-run --verbose
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", os.path.expanduser("~/.openclaw/workspace")))
DB_PATH = WORKSPACE / "memory.db"
VALID_MODELS = ("opus", "sonnet", "haiku")
MAX_TIMEOUT = 600
DEFAULT_TIMEOUT = 300
DEFAULT_MEMORY_LIMIT = 5


def read_file(path: Path) -> str:
    """Read a text file, return content or error string."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"[File not found: {path.name}]"
    except Exception as e:
        return f"[Error reading {path.name}: {e}]"


def sanitize_fts_query(query: str) -> str:
    """Sanitize FTS5 query terms to avoid syntax errors.

    Wraps each word in double quotes so special characters
    (*, OR, AND, NOT, parentheses) are treated as literals.
    """
    words = query.split()
    sanitized = []
    for word in words:
        # Strip existing quotes, wrap in double quotes
        clean = word.strip('"\'')
        if clean:
            # Escape internal double quotes
            clean = clean.replace('"', '""')
            sanitized.append(f'"{clean}"')
    return " ".join(sanitized)


def get_memory_context(query_terms: str = "", limit: int = DEFAULT_MEMORY_LIMIT) -> str:
    """Get relevant memory context from SQLite DB via FTS search."""
    if not DB_PATH.exists():
        return "No memory database found."
    try:
        results = []
        with sqlite3.connect(str(DB_PATH)) as conn:
            if query_terms:
                safe_query = sanitize_fts_query(query_terms)
                cursor = conn.execute(
                    "SELECT key, value, category FROM memories WHERE id IN "
                    "(SELECT rowid FROM memories_fts WHERE memories_fts MATCH ?) LIMIT ?",
                    (safe_query, limit)
                )
                results = cursor.fetchall()

            if not results:
                cursor = conn.execute(
                    "SELECT key, content, category FROM daily_log "
                    "WHERE date >= date('now', '-7 days') ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
                results = cursor.fetchall()

        if results:
            lines = []
            for key, value, category in results:
                label = f"[{category}]" if category else ""
                k = key or "entry"
                lines.append(f"- {label} {k}: {value}")
            return "\n".join(lines)
        return "No relevant memory found."
    except sqlite3.OperationalError as e:
        return f"Memory search error (bad query?): {e}"
    except Exception as e:
        return f"Memory access error: {e}"


def get_project_context(project_id: str) -> str:
    """Get project metadata from memory.db projects table."""
    if not project_id or not DB_PATH.exists():
        return ""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.execute(
                "SELECT name, url, git, technology, client_name, notes FROM projects WHERE id = ?",
                (project_id,)
            )
            row = cursor.fetchone()
        if row:
            name, url, git, tech, client, notes = row
            parts = [f"**Project:** {name}"]
            if url:
                parts.append(f"**URL:** {url}")
            if git:
                parts.append(f"**Repo:** {git}")
            if tech:
                parts.append(f"**Tech:** {tech}")
            if client:
                parts.append(f"**Client:** {client}")
            if notes:
                parts.append(f"**Notes:** {notes}")
            return "\n".join(parts)
        return f"[Project '{project_id}' not found in database]"
    except Exception as e:
        return f"Project lookup error: {e}"


def get_agent_profile(agent_id: str) -> str:
    """Load agent-specific PROFILE.md if it exists."""
    if not agent_id:
        return ""

    # Check common profile locations
    candidates = [
        WORKSPACE / "agents" / agent_id / "PROFILE.md",
        WORKSPACE / "agents" / f"{agent_id}-agent" / "PROFILE.md",
        WORKSPACE / f"workspace-{agent_id}" / "SOUL.md",
    ]
    for path in candidates:
        if path.exists():
            content = read_file(path)
            if not content.startswith("["):
                return content

    # Fallback: check agents table in DB
    if DB_PATH.exists():
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                cursor = conn.execute(
                    "SELECT name, role, notes FROM agents WHERE id = ?",
                    (agent_id,)
                )
                row = cursor.fetchone()
            if row:
                name, role, notes = row
                parts = [f"**Agent:** {name} ({role})"]
                if notes:
                    parts.append(f"**Notes:** {notes}")
                return "\n".join(parts)
        except Exception as e:
            return f"[Agent DB lookup error: {e}]"

    return agent_id


def build_context_prompt(
    task: str,
    memory_query: str = "",
    agent_profile: str = "",
    project_id: str = "",
) -> str:
    """Build the complete context prompt for Claude CLI."""

    identity = read_file(WORKSPACE / "IDENTITY.md")
    soul = read_file(WORKSPACE / "SOUL.md")
    user = read_file(WORKSPACE / "USER.md")
    memory = get_memory_context(memory_query)
    profile = get_agent_profile(agent_profile)
    project = get_project_context(project_id)

    sections = [
        "# CONTEXT FOR CLAUDE CLI EXECUTION",
        "",
        "## IDENTITY",
        identity,
        "",
        "## SOUL (Personality & Rules)",
        soul,
        "",
        "## USER INFO",
        user,
        "",
        "## RELEVANT MEMORY",
        memory,
    ]

    if profile:
        sections.extend(["", "## AGENT PROFILE", profile])

    if project:
        sections.extend(["", "## PROJECT CONTEXT", project])

    sections.extend([
        "",
        "## TASK",
        task,
        "",
        "---",
        "Execute this task following all the rules in SOUL.md. "
        "You are operating in subscription mode via Claude CLI, "
        "so you don't have access to OpenClaw tools. "
        "Focus on the core task and provide detailed, actionable output.",
    ])

    return "\n".join(sections)


def call_claude_cli(
    context_prompt: str,
    model: str = "opus",
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Execute Claude CLI with the context prompt via stdin."""

    cmd = [
        "claude",
        "--print",
        "--permission-mode", "bypassPermissions",
        "--model", model,
    ]

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            input=context_prompt,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = round(time.time() - start, 1)

        if result.returncode == 0:
            return {
                "success": True,
                "output": result.stdout,
                "error": None,
                "model": model,
                "elapsed_seconds": elapsed,
            }
        else:
            return {
                "success": False,
                "output": result.stdout or None,
                "error": result.stderr or f"Exit code {result.returncode}",
                "model": model,
                "elapsed_seconds": elapsed,
            }
    except subprocess.TimeoutExpired:
        elapsed = round(time.time() - start, 1)
        return {
            "success": False,
            "output": None,
            "error": f"Timed out after {timeout}s",
            "model": model,
            "elapsed_seconds": elapsed,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": None,
            "error": "claude CLI not found. Install it first.",
            "model": model,
            "elapsed_seconds": 0,
        }
    except Exception as e:
        elapsed = round(time.time() - start, 1)
        return {
            "success": False,
            "output": None,
            "error": str(e),
            "model": model,
            "elapsed_seconds": elapsed,
        }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Route tasks to Claude CLI with OpenClaw context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --task "Build landing page" --model opus
  %(prog)s --task "Fix auth bug" --agent developer --project website-abd
  %(prog)s --task "Write blog post" --agent writer --dry-run
  %(prog)s --task "Quick lookup" --model haiku --timeout 30
        """,
    )
    parser.add_argument("--task", required=True, help="Task description")
    parser.add_argument("--memory-query", default="", help="FTS search terms for memory.db")
    parser.add_argument("--agent", default="", help="Agent profile ID (developer, seo, writer, pm-abd, etc.)")
    parser.add_argument("--project", default="", help="Project ID for project-specific context")
    parser.add_argument("--model", default="opus", choices=list(VALID_MODELS),
                        help="Claude model (default: opus)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"Max execution time in seconds (default: {DEFAULT_TIMEOUT}, max: {MAX_TIMEOUT})")
    parser.add_argument("--verbose", action="store_true", help="Show full context before execution")
    parser.add_argument("--dry-run", action="store_true", help="Print context without calling Claude CLI")
    parser.add_argument("--json", action="store_true", help="Output structured JSON")
    return parser.parse_args()


def main():
    args = parse_args()

    # Clamp timeout
    timeout = min(args.timeout, MAX_TIMEOUT)

    # Build context
    context_prompt = build_context_prompt(
        task=args.task,
        memory_query=args.memory_query,
        agent_profile=args.agent,
        project_id=args.project,
    )

    # Verbose: show context
    if args.verbose or args.dry_run:
        print("=" * 60, file=sys.stderr)
        print("CONTEXT PROMPT", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(context_prompt, file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"Model: {args.model} | Timeout: {timeout}s | Agent: {args.agent or 'none'} | Project: {args.project or 'none'}",
              file=sys.stderr)
        print("=" * 60, file=sys.stderr)

    if args.dry_run:
        if args.json:
            print(json.dumps({"dry_run": True, "context_length": len(context_prompt), "model": args.model}, indent=2))
        else:
            print(f"\n[DRY RUN] Context: {len(context_prompt)} chars | Model: {args.model} | Would execute with timeout: {timeout}s")
        sys.exit(0)

    # Execute
    if not args.json:
        print(f"Routing to Claude CLI ({args.model})...", file=sys.stderr)
        print(f"Task: {args.task[:80]}{'...' if len(args.task) > 80 else ''}", file=sys.stderr)
        print("-" * 60, file=sys.stderr)

    result = call_claude_cli(context_prompt, model=args.model, timeout=timeout)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(result["output"])
            print(f"\n[Completed in {result['elapsed_seconds']}s using {result['model']}]", file=sys.stderr)
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            if result.get("output"):
                print(f"Partial output:\n{result['output']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
