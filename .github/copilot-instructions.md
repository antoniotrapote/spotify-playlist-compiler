# Copilot Global Instructions

These are general guidelines for generating code in this repository:

- **Code style**
  - Follow PEP8 style for Python code.
  - Use clear and descriptive variable and function names.
  - Add type hints for function arguments and return values.

- **Documentation**
  - Include docstrings for all public functions and classes.
  - Write comments only when code is not self-explanatory.

- **Testing**
  - Provide simple unit tests with `pytest` when creating new functions.
  - Keep tests small and focused on one behavior.

- **Dependencies**
  - Prefer Python standard library over external packages, unless otherwise required.
  - If an external package is suggested, explain why.

- **Code quality**
  - Avoid global variables and side effects.
  - Write small, reusable, and pure functions whenever possible.
  - Ensure code is efficient and avoids unnecessary computations.

- **Security**
  - Avoid hardcoding sensitive information like API keys or passwords.
  - Follow best practices for handling user input to prevent security vulnerabilities.