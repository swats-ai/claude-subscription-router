#!/usr/bin/env python3
"""
Claude Subscription Router
Routes heavy tasks to Claude CLI (subscription) while preserving OpenClaw context
"""

import os
import sys
import json
import sqlite3
import subprocess
from pathlib import Path

def get_memory_context(query_terms="", limit=5):
    """Get relevant memory context from SQLite DB"""
    try:
        db_path = os.path.expanduser("~/.openclaw/workspace/memory.db")
        conn = sqlite3.connect(db_path)
        
        if query_terms:
            # Use FTS search if terms provided
            cursor = conn.execute(
                "SELECT key, value FROM memories_fts WHERE memories_fts MATCH ? LIMIT ?",
                (query_terms, limit)
            )
        else:
            # Get recent daily log entries
            cursor = conn.execute(
                "SELECT key, content FROM daily_log WHERE date >= date('now', '-7 days') ORDER BY rowid DESC LIMIT ?",
                (limit,)
            )
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            return "\n".join([f"- {key}: {value}" for key, value in results])
        else:
            return "No relevant memory found."
            
    except Exception as e:
        return f"Memory access error: {e}"

def get_soul_content():
    """Read SOUL.md content"""
    try:
        soul_path = os.path.expanduser("~/.openclaw/workspace/SOUL.md")
        with open(soul_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"SOUL.md access error: {e}"

def get_identity_content():
    """Read IDENTITY.md content"""
    try:
        identity_path = os.path.expanduser("~/.openclaw/workspace/IDENTITY.md")
        with open(identity_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"IDENTITY.md access error: {e}"

def get_user_content():
    """Read USER.md content"""
    try:
        user_path = os.path.expanduser("~/.openclaw/workspace/USER.md")
        with open(user_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"USER.md access error: {e}"

def build_context_prompt(task, memory_query="", agent_profile=""):
    """Build complete context prompt for Claude CLI"""
    
    soul = get_soul_content()
    identity = get_identity_content()
    user = get_user_content()
    memory = get_memory_context(memory_query)
    
    context_prompt = f"""
# CONTEXT FOR CLAUDE CLI EXECUTION

## IDENTITY
{identity}

## SOUL (Personality & Rules)
{soul}

## USER INFO
{user}

## RELEVANT MEMORY
{memory}

## AGENT PROFILE
{agent_profile}

## TASK
{task}

---
Execute this task following all the rules in SOUL.md. You are operating in subscription mode via Claude CLI, so you don't have access to OpenClaw tools. Focus on the core task and provide detailed, actionable output.
"""
    
    return context_prompt

def call_claude_cli(context_prompt, model="opus"):
    """Execute Claude CLI with context"""
    try:
        # Change to workspace directory
        workspace = os.path.expanduser("~/.openclaw/workspace")
        
        cmd = [
            "claude",
            "--print",
            "--dangerously-skip-permissions",
            "--model", model,
            context_prompt
        ]
        
        result = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "output": result.stdout,
                "error": None
            }
        else:
            return {
                "success": False,
                "output": None,
                "error": result.stderr or f"Command failed with code {result.returncode}"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": None,
            "error": "Claude CLI execution timed out (2 minutes) - try breaking task into smaller parts"
        }
    except Exception as e:
        return {
            "success": False,
            "output": None,
            "error": f"Execution error: {e}"
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 claude-subscription.py <task> [memory_query] [agent_profile] [model]")
        print("Example: python3 claude-subscription.py 'Create a landing page for medical clinic' 'medical healthcare' 'developer' 'opus'")
        sys.exit(1)
    
    task = sys.argv[1]
    memory_query = sys.argv[2] if len(sys.argv) > 2 else ""
    agent_profile = sys.argv[3] if len(sys.argv) > 3 else ""
    model = sys.argv[4] if len(sys.argv) > 4 else "opus"
    
    print(f"🤖 Routing to Claude CLI (subscription)...")
    print(f"📋 Task: {task}")
    print(f"🧠 Memory query: {memory_query}")
    print(f"👤 Agent profile: {agent_profile}")
    print(f"🎯 Model: {model}")
    print("-" * 60)
    
    context_prompt = build_context_prompt(task, memory_query, agent_profile)
    result = call_claude_cli(context_prompt, model)
    
    if result["success"]:
        print(result["output"])
    else:
        print(f"❌ Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()