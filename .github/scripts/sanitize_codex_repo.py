import os
import ast
import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
README_PATH = os.path.join(REPO_ROOT, "README.md")

SANITIZE_START = "<!-- SANITIZE_LOG_START -->"
SANITIZE_END = "<!-- SANITIZE_LOG_END -->"

def scan_python_files():
    python_files = []
    for root, _, files in os.walk(REPO_ROOT):
        if '.venv' in root or '__pycache__' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                python_files.append(os.path.join(root, f))
    return python_files

def sanitize_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='surrogatepass') as f:
        original_code = f.read()

    try:
        tree = ast.parse(original_code)
    except SyntaxError:
        return False, False  # failed to parse

    cleaned_code = original_code.strip() + "\n"
    was_modified = (cleaned_code != original_code)

    if was_modified:
        with open(filepath, 'w', encoding='utf-8', errors='surrogatepass') as f:
            f.write(cleaned_code)

    return True, was_modified

def generate_sanitize_block(num_files, num_cleaned, syntax_errors):
    timestamp = datetime.datetime.utcnow().isoformat(timespec='seconds') + "Z"
    return f"""{SANITIZE_START}
<div align="center" style="margin-top:30px; padding:20px; border-radius:16px;
    border:1px solid #22c55e; box-shadow:0 0 10px #22c55e, inset 0 0 10px #22c55e;
    background:#111; color:#e0e0e0; font-family:monospace;">

<h3 style="color:#22c55e;">🧹 CodexDaemon Sanitize Log — {timestamp}</h3>

<ul style="list-style:none; padding:0; font-size:14px;">
  <li>✅ <strong>{num_files}</strong> Python files scanned</li>
  <li>✅ <strong>{num_cleaned}</strong> files auto-cleaned</li>
  <li>✅ <strong>{'No' if syntax_errors == 0 else syntax_errors}</strong> syntax errors</li>
</ul>

</div>
{SANITIZE_END}"""

def update_readme(log_block):
    with open(README_PATH, 'r', encoding='utf-8', errors='surrogatepass') as f:
        readme = f.read()

    if SANITIZE_START in readme and SANITIZE_END in readme:
        before = readme.split(SANITIZE_START)[0]
        after = readme.split(SANITIZE_END)[1]
        updated = before + log_block + after
    else:
        # Append at bottom if tags not found
        updated = readme.rstrip() + "\n\n" + log_block

    with open(README_PATH, 'w', encoding='utf-8', errors='surrogatepass') as f:
        f.write(updated)

def main():
    files = scan_python_files()
    cleaned = 0
    syntax_errors = 0

    for file in files:
        parsed, modified = sanitize_file(file)
        if not parsed:
            syntax_errors += 1
        elif modified:
            cleaned += 1

    block = generate_sanitize_block(len(files), cleaned, syntax_errors)
    update_readme(block)

    print("[OK] README updated with sanitize log.\n")
    print("[SUMMARY]")
    print(f"Scanned  : {len(files)} .py files")
    print(f"Cleaned  : {cleaned} modified")
    print(f"Errors   : {syntax_errors} syntax issues")

if __name__ == "__main__":
    main()
