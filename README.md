# VSCode Project Template

A minimal and clean template for Python projects in Visual Studio Code.  
It includes a preconfigured `.vscode` folder for environment auto-activation and Copilot instruction files.

---

## Setup

### 1. Create and activate a virtual environment

Open a **new integrated terminal** in VS Code (``Ctrl+` `` or from the menu *Terminal → New Terminal*)  
and run the following commands:

```bash
# Create a new virtual environment (Python 3.12 recommended)
python -m venv .venv

# Activate it (macOS / Linux)
source .venv/bin/activate

# On Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

When activated, your terminal prompt should show `(.venv)`.

---

### 2. Verify that everything works

Run this command in the **same terminal** to confirm that Python is using the correct virtual environment:

```bash
python -c "import sys, os; print('Python:', sys.executable); print('VIRTUAL_ENV:', os.environ.get('VIRTUAL_ENV'))"
```

Expected output:

```
Python: /path/to/your/project/.venv/bin/python
VIRTUAL_ENV: /path/to/your/project/.venv
```

If both paths match your project folder, your environment is set up correctly ✅

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

(Leave `requirements.txt` empty or list your default dependencies.)

---

### 4. Run your scripts

```bash
python your_script.py
```

VS Code will automatically detect and activate the `.venv` environment.

---

## 📁 Structure

```
.github/               # Copilot and instructions files
.vscode/               # VSCode settings and extensions
.gitignore             # Excludes .venv and other temporary files
.AGENTS.md             # 
LICENSE
README.md              # This file
requirements.txt       # Project dependencies
```

---

## ⚖️ License

MIT © Antonio L. Martínez Trapote
