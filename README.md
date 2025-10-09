# 🧠 CodexDaemon

**CodexDaemon** is a headless AI engineer that automatically edits, commits, and patches your code — locally or via GitHub Actions — using OpenAI’s Codex-like reasoning and your `.env` configuration.

---

## ⚙️ How It Works
1. Reads local `.env` for your API key and repo path.  
2. Accepts natural language commands (e.g. *“add a weather API function to update_readme.py”*).  
3. Uses GPT-4o-mini to generate a diff patch.  
4. Applies it, commits, and pushes to your repo automatically.  

---

## 🚀 Quick Start

```bash
git clone https://github.com/roninazure/CodexDaemon.git
cd CodexDaemon
cp .env.example .env
pip install -r requirements.txt
