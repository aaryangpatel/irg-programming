---
title: Python Quick Reference
---


# Python quick reference 

You likely already have python installed on your computer. If not, here is how to install it.

````markdown
##  Installing Python 

Use system Python + pip (no virtual environment).

**macOS**
- Install Python 3.12: `brew install python@3.12` (or download from python.org)
- Verify pip: `python3 -m pip --version`

**Linux (Debian/Ubuntu)**
- Install: `sudo apt-get install -y python3 python3-pip`
- Verify pip: `python3 -m pip --version`

**Windows**
- Install Python 3.12 from python.org (check “Add python.exe to PATH”) or via Microsoft Store.
- Verify pip: `py -3 -m pip --version`

**Upgrade pip (once)**
```bash
python3 -m pip install --user -U pip        # Windows: py -3 -m pip install --user -U pip
````

**Install project requirements (no sudo)**

```bash
python3 -m pip install --user -r requirements.txt    # Windows: py -3 -m pip install --user -r requirements.txt
```

> If command-line scripts aren’t found, add the user-site Scripts directory to your PATH:

* **macOS/Linux (bash/zsh)**

  ```bash
  export PATH="$(python3 -m site --user-base)/bin:$PATH"
  ```

  (Add the line to `~/.bashrc` or `~/.zshrc` to make it permanent.)

* **Windows (PowerShell)**

  ```powershell
  $scripts = (py -3 -m site --user-site).Replace('site-packages','Scripts')
  $env:Path += ';' + $scripts
  ```

  (Persist via “Environment Variables” → edit `Path`.)

**Run checks / scripts**

```bash
python3 setupcheck.py                 # Windows: py -3 setupcheck.py
```



## Optional: Installing UV

Use **uv** — a fast Python/venv/pip manager that also installs Python for you.

* macOS / Linux:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
* Windows (PowerShell):

  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

If you prefer package managers: `brew install uv` (macOS) or `winget install --id=astral-sh.uv -e` (Windows). ([Astral Docs][1])

> Why uv? It gives you a guaranteed clean, per-project Python without touching system Python, and can pin the Python version you need. ([Astral Docs][2])

---

## 1) Per-project setup (5 commands)

**Goal**: project folder, pinned Python, isolated env, required libs.

```bash
# Pick Python 3.12 or 3.11
mkdir hw1 && cd hw1
uv venv --python 3.12
source .venv/bin/activate      # Windows: .\.venv\Scripts\activate
uv pip install -U pip
```

> Need a specific Python at any time? `uv venv --python 3.11.9` (uv downloads it if missing). ([Astral Docs][3])

---

## Install the libraries you’ll actually use

```bash
# Core Libraries
uv pip install pydantic httpx python-dotenv

# For Later: Web services
uv pip install openai google-search-results    # SerpAPI’s Python client

# For Later: Retrieval (Pyserini wraps Anserini/Lucene)
uv pip install pyserini
```

**Note:** Pyserini **expects Java 21** on PATH (`java -version`) because it bundles Anserini. Install any JDK 21+ (Temurin/Zulu/etc.). ([GitHub][4])  Pyserini might also work better on Python 3.11.

---

## Running Python Code

```bash
python -V           # show version in the venv
python              # REPL
python script.py    # run a script
python -m pkg.tool  # run a module as a script
deactivate          # leave the venv
```

---

## Install Visual Studio Code (VSCode) as Programming Environment


1. Install VSCode and the **Python** extension (ms-python.python).
2. Open the repo folder (**File → Open Folder…**).
3. Select interpreter: **Ctrl/Cmd+Shift+P** → *Python: Select Interpreter* → pick the one `python -V` shows on the command line.
4. Open `setupcheck.py` (or a other python code).
5. Run current file: click ▶ Run (or **Ctrl/Cmd+F5**).
6. Use **View → Terminal** for a shell aligned with VSCode’s interpreter.
7. Pass args/env: create `.vscode/launch.json` and set `args`, `env`, `cwd`.
8. Advanced: Lint/format: `pip install ruff black` → enable *Format on Save* in Settings.



[1]: https://docs.astral.sh/uv/getting-started/installation/?utm_source=chatgpt.com "Installation | uv - Astral Docs"
[2]: https://docs.astral.sh/uv/concepts/python-versions/?utm_source=chatgpt.com "Python versions | uv - Astral Docs"
[3]: https://docs.astral.sh/uv/pip/environments/?utm_source=chatgpt.com "Using Python environments - uv - Astral Docs"
