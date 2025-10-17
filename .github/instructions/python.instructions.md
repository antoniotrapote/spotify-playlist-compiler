---
applyTo: "**/*.py"
description: "Coding standards for all Python source files"
---

# Project coding standards for Python

- **Style**
  - Follow the PEP 8 style guide.
  - Use `snake_case` for variables and functions.
  - Use `PascalCase` for class names.
  - Keep line length reasonable (around 100 characters).

- **Readability**
  - Always prioritize clarity and simplicity over cleverness.
  - Write self-explanatory code and avoid unnecessary complexity.

- **Documentation**
  - Add docstrings (triple quotes) to modules, classes, and functions.
  - Write comments only for non-obvious parts of the code.

- **Functions**
  - Use descriptive names.
  - Always include type hints for parameters and return values.
  - Keep functions small and focused on a single task.

- **Testing**
  - When writing new functions, add simple unit tests with `pytest`.
  - Tests should cover typical cases and edge cases.