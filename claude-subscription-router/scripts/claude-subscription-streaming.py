#!/usr/bin/env python3
"""
Claude Subscription Router - Streaming Version
Routes heavy tasks to Claude CLI with real-time output streaming
"""

import os
import sys
import sqlite3
import subprocess
from pathlib import Path

def get_memory_context(query_terms="", limit=3):
    """Get relevant memory context from SQLite DB (reduced limit for speed)"""
    try:
        db_path = os.path.expanduser("~/.openclaw/workspace/memory.db")
        conn = sqlite3.connect(db_path)
        
        if query_terms:
            cursor = conn.execute(
                "SELECT key, value FROM memories_fts WHERE memories_fts MATCH ? LIMIT ?",
                (query_terms, limit)
            )
        else:
            cursor = conn.execute(
                "SELECT key, content FROM daily_log WHERE date >= date('now', '-3 days') ORDER BY rowid DESC LIMIT ?",
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

def build_context_prompt(task, memory_query="", agent_profile=""):
    """Build lightweight context prompt for Claude CLI"""
    
    # Read core files with error handling
    try:
        soul_path = os.path.expanduser("~/.openclaw/workspace/SOUL.md")
        with open(soul_path, 'r') as f:
            soul = f.read()[:2000]  # Limit SOUL to 2k chars
    except:
        soul = "SOUL.md not available"
    
    try:
        identity_path = os.path.expanduser("~/.openclaw/workspace/IDENTITY.md")
        with open(identity_path, 'r') as f:
            identity = f.read()[:1000]  # Limit identity
    except:
        identity = "IDENTITY.md not available"
    
    memory = get_memory_context(memory_query)
    
    # Lightweight context
    context_prompt = f"""# CONTEXT

## IDENTITY
{identity}

## KEY RULES (from SOUL)
{soul[:1000]}

## MEMORY
{memory}

## AGENT ROLE
{agent_profile}

## TASK
{task}

---
Execute efficiently. Focus on core deliverable. You're in Claude CLI subscription mode."""
    
    return context_prompt

def call_claude_cli_streaming(context_prompt, model="opus"):
    """Execute Claude CLI with streaming output"""
    try:
        workspace = os.path.expanduser("~/.openclaw/workspace")
        
        cmd = [
            "claude",
            "--model", model,
            context_prompt
        ]
        
        print(f"🤖 Starting Claude CLI ({model})...")
        print("-" * 60)
        
        # Stream output in real-time
        process = subprocess.Popen(
            cmd,
            cwd=workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        output_lines = []
        
        # Read output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                print(line, end='')
                output_lines.append(line)
        
        # Wait for process to complete
        process.wait()
        
        if process.returncode == 0:
            return {
                "success": True,
                "output": "".join(output_lines),
                "error": None
            }
        else:
            stderr_output = process.stderr.read()
            return {
                "success": False,
                "output": None,
                "error": stderr_output or f"Command failed with code {process.returncode}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "output": None,
            "error": f"Execution error: {e}"
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 claude-subscription-streaming.py <task> [memory_query] [agent_profile] [model]")
        sys.exit(1)
    
    task = sys.argv[1]
    memory_query = sys.argv[2] if len(sys.argv) > 2 else ""
    agent_profile = sys.argv[3] if len(sys.argv) > 3 else ""
    model = sys.argv[4] if len(sys.argv) > 4 else "opus"
    
    context_prompt = build_context_prompt(task, memory_query, agent_profile)
    result = call_claude_cli_streaming(context_prompt, model)
    
    if not result["success"]:
        print(f"\n❌ Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()