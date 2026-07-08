# Information Retrieval and Generation Systems

Aaryan Patel

---



# Installation

## 1. Install Python and create a virtual environment

Choose one of the following options:

### Option A: Using pyenv (recommended if available)

```bash
pyenv install 3.12.3
pyenv virtualenv 3.12.3 irg-env
pyenv activate irg-env
````

### Option B: Using built-in Python `venv` (no pyenv required)


```bash
python3 -m venv irg-env
source irg-env/bin/activate 
```

On Windows:
```bash
python3 -m venv irg-env
irg-env\Scripts\activate
  ```

---

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

Alternatively, if you have [`uv`](https://github.com/astral-sh/uv) installed: `
uv pip install -r requirements.txt`

---

## 3. Check the installation

To verify that your environment is set up correctly, run:

```bash
python setupcheck.py
```

---

## Managing Dependencies

If you want to add more Python packages, simply add them to `requirements.txt`, then call `pip install -r requirements.txt` again.

If you're comfortable with modern Python packaging, you can optionally switch to using a `pyproject.toml` instead.


# Activation

You only need to perform the installation once. However, **every time you sit down to work on the project**, you need to activate your Python environment.

Use the appropriate command depending on how you created your environment:

* **Option A (pyenv):**

  ```bash
  pyenv activate irg-env
  ```

* **Option B (venv):**

  ```bash
  source irg-env/bin/activate      # On Windows: irg-env\Scripts\activate
  ```

  On Windows:
  ```bash
  irg-env\Scripts\activate
  ```

After activation, you can run any Python script or module as usual.

You can verify that the correct environment is active by running:

```bash
python setupcheck.py
```

---



# Homework

Please see the `README.md` file in the respective homework folders.

* `./prog1`: Simple Retrieval System


# Recommended Repository Layout

```
irg-course/
├─ irg-env/ or .venv/           # python env
├─ requirements.txt
├─ setupcheck.py 
├─ .gitignore                   # File patterns to not commit
├─ .env                         # API keys (not committed): OPENAI_API_KEY=...
├─ src/
│  └─ mylib/                    # build up a library you reuse across assignments
│     ├─ __init__.py
│     ├─ request.py             # JSON helpers for request objects
│     └─ document.py            # JSON helpers for document objects
├─ data/                        # datasets the homeworks need
└─ prog1/                       # homework launchers (bash/python)
   ├─ README.md                 # Homework instruction
   ├─ run.py                    # Python main class 
   └─ run.sh                    # Bash script to launch the main class
```