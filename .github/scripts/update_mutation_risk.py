#!/usr/bin/env python3
import os
import re
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = REPO_ROOT / "README.md"

# Risky code patterns and weights
PATTERNS = {
    r"\beval\(": 10,
    r"\bexec\(": 10,
    r"\bopen\(": 5,
    r"\bsubprocess\.(run|Popen)": 10,
    r"\bos\.system": 10,
    r"\b__import__\(": 8,
    r"@codex": 7,
    r"#\s*(evolve|mutate|hallucinate)": 4,
    r"openai\.api_key": 5,
}

def score_file(filepath):
    try:
        score = 0
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                for pattern, weight in PATTERNS.items():
                    if re.search(pattern, line):
                        score += weight
        return score
    except Exception:
        return 0

def collect_scores():
    scores = []
    for path in REPO_ROOT.rglob("*.py"):
        if any(p in str(path) for p in [".venv", "__pycache__", "site-packages"]):
            continue
        score = score_file(path)
        if score > 0:
            rel_path = str(path.relative_to(REPO_ROOT))
            scores.append((rel_path, score))
    return sorted(scores, key=lambda x: x[1], reverse=True)

def inject_into_readme(scores):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!-- CODEX_MUTATION_SCORE_START -->"
    end_marker = "<!-- CODEX_MUTATION_SCORE_END -->"

    if start_marker not in content or end_marker not in content:
        print("❌ Mutation risk block not found in README.md")
        return

    timestamp = datetime.utcnow().isoformat() + "Z"

    rows = "\n".join(
        f"<tr><td>{path}</td><td align='right'>{score}</td></tr>"
        for path, score in scores[:10]
    )

    new_block = f"""{start_marker}
<div align="center" style="margin-top:30px; padding:20px; border-radius:16px;
    border:1px solid #f97316; box-shadow:0 0 10px #f97316, inset 0 0 10px #f97316;
    background:#111; color:#e0e0e0; font-family:monospace;">

<h3 style="color:#f97316;">🧬 CodexDaemon Mutation Risk Score</h3>

<table style="width:70%; border-collapse:collapse; color:#f8f8f8; font-family:monospace;">
<tr style="color:#f97316;">
<th align="left">File</th>
<th align="right">Risk Score</th>
</tr>
{rows}
</table>

<pre style="text-align:left; color:#f0cfcf; background:#111; padding:15px;
    border-radius:10px; border:1px solid #f97316; box-shadow:inset 0 0 6px #f97316;">
CodexDaemon performed a self-inspection on potential mutation vectors.
Risk is ranked by suspicious operations and volatile patterns.
Scan timestamp: {timestamp}
</pre>

</div>
{end_marker}"""

    pattern = re.compile(f"{start_marker}.*?{end_marker}", re.DOTALL)
    updated = pattern.sub(new_block, content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    print("✅ Mutation Risk Score updated in README.md")

if __name__ == "__main__":
    inject_into_readme(collect_scores())
