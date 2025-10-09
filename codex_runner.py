```python
#!/usr/bin/env python3
"""
CodexDaemon Runner
------------------
Local version of the Codex AI automation runner.

This script connects to OpenAI via your .env configuration to perform code edits,
generate functions, and push changes directly to your CodexDaemon repository.

Usage Examples:
    python3 codex_runner.py "add a function to fetch weather from OpenWeather API"
    python3 codex_runner.py "improve error handling in codex_runner.py" --commit
    python3 codex_runner.py --health
    python3 codex_runner.py --time
"""

import os, sys, argparse
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown
from git import Repo, Actor
from dotenv import load_dotenv
from openai import OpenAI

console = Console()

# === Load local .env ===
env_path = Path(__file__).resolve().parent / ".env"
if not env_path.exists():
    console.print(f"[red]ERROR: .env file not found at {env_path}[/red]")
    sys.exit(1)
load_dotenv(dotenv_path=env_path)

# === Environment variables ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_DIR = Path(os.getenv("PROJECT_DIR", Path(__file__).resolve().parent)).resolve()
MODEL = os.getenv("CODEX_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    console.print("[red]ERROR: OPENAI_API_KEY not set in .env[/red]")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# === Repo utilities ===
def get_repo():
    try:
        return Repo(PROJECT_DIR)
    except Exception:
        console.print(f"[red]Not a valid Git repo: {PROJECT_DIR}[/red]")
        sys.exit(1)

# === Health check ===
def health_check():
    console.rule("[green]🧠 CodexDaemon Health Check")
    console.print(f"[bold]Project Dir:[/bold] {PROJECT_DIR}")
    console.print(f"[bold]Model:[/bold] {MODEL}")
    console.print(f"[bold].env Path:[/bold] {env_path}")
    console.print(f"[bold]OpenAI Key Loaded:[/bold] {'✅' if OPENAI_API_KEY else '❌'}")
    try:
        repo = get_repo()
        console.print(f"[bold]Git Repo OK:[/bold] {repo.active_branch}")
    except Exception as e:
        console.print(f"[red]Git error:[/red] {e}")
    console.print("[green]✅ Environment healthy.\n")

# === Print current UTC time ===
def print_current_time():
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"[blue]Current UTC Time:[/blue] {current_time}")

# === Ask OpenAI ===
def ask_model(prompt, context):
    system = (
        "You are a senior Python engineer. "
        "Implement the requested change directly and return the full updated file content. "
        "Do not return a diff or patch."
    )
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Task: {prompt}\n\n---- FILE CONTENT ----\n{context}\n---- END ----"},
            ],
            temperature=0.2,
            max_tokens=4000,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        console.print(f"[red]OpenAI error:[/red] {e}")
        sys.exit(1)

# === File editing ===
def update_file(target_file, new_content):
    Path(target_file).write_text(new_content, encoding="utf-8")
    console.print(f"[green]✅ File updated:[/green] {target_file}")

# === Commit and push ===
def commit_push(repo, message, push=True):
    repo.git.add(all=True)
    if not repo.index.diff("HEAD"):
        console.print("[yellow]No changes to commit[/yellow]")
        return
    author_name = os.getenv("GIT_AUTHOR_NAME", "CodexDaemon Bot")
    author_email = os.getenv("GIT_AUTHOR_EMAIL", "codexdaemon@example.com")
    author = Actor(author_name, author_email)
    repo.index.commit(f"🤖 CodexDaemon: {message}", author=author)
    if push:
        try:
            repo.remotes.origin.push()
            console.print("[green]Pushed to origin[/green]")
        except Exception as e:
            console.print(f"[yellow]Committed locally, push failed:[/yellow] {e}")

# === Main ===
def main():
    ap = argparse.ArgumentParser(description="CodexDaemon Runner")
    ap.add_argument("instruction", nargs="?", type=str, help="Instruction to execute")
    ap.add_argument("--commit", action="store_true", help="Commit and push changes")
    ap.add_argument("--health", action="store_true", help="Run environment health check")
    ap.add_argument("--time", action="store_true", help="Print current UTC time")
    args = ap.parse_args()

    if args.health:
        health_check()
        sys.exit(0)

    if args.time:
        print_current_time()
        sys.exit(0)

    if not args.instruction:
        console.print("[red]No instruction provided[/red]")
        sys.exit(1)

    repo = get_repo()
    target_hint = args.instruction.split()[-1]
    target_path = (PROJECT_DIR / target_hint).resolve() if target_hint.endswith(".py") else None

    if not target_path or not target_path.exists():
        console.print(f"[red]Target file not found: {target_hint}[/red]")
        sys.exit(1)

    context = target_path.read_text(encoding="utf-8", errors="ignore")
    console.print(f"[cyan]Editing:[/cyan] {target_path.relative_to(PROJECT_DIR)}")

    new_content = ask_model(args.instruction, context)
    update_file(target_path, new_content)

    if args.commit:
        commit_push(repo, args.instruction, push=True)

if __name__ == "__main__":
    main()
```