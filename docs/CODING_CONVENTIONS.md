# Coding Conventions

This document outlines the coding standards and conventions for the Python GenWeb Modernization project. These conventions are based on PEP 8 and industry best practices.

## Table of Contents

1. [General Principles](#general-principles)
2. [Code Layout](#code-layout)
3. [Naming Conventions](#naming-conventions)
4. [Comments and Documentation](#comments-and-documentation)
5. [Imports](#imports)
6. [Error Handling](#error-handling)
7. [Type Hints](#type-hints)
8. [Tools and Enforcement](#tools-and-enforcement)

## General Principles

- **Readability counts**: Code should be written for humans to read, not just machines to execute
- **Consistency is key**: Follow established patterns within the codebase
- **Simplicity over complexity**: Prefer simple, clear solutions over complex ones
- **Don't repeat yourself (DRY)**: Avoid code duplication

## Code Layout

### Indentation
- Use **4 spaces** per indentation level
- Never mix tabs and spaces
- Continuation lines should align wrapped elements

```python
# Correct
def long_function_name(
    var_one, var_two, var_three,
    var_four):
    print(var_one)

# Correct
result = some_function_that_takes_arguments(
    'a', 'b', 'c',
    'd', 'e', 'f',
)
```

### Blank Lines
- Two blank lines around top-level function and class definitions
- One blank line around method definitions inside a class
- Use blank lines sparingly within functions to separate logical sections

```python
import os
import sys


class MyClass:
    """A simple example class."""

    def __init__(self):
        self.value = 0

    def method_one(self):
        """First method."""
        pass

    def method_two(self):
        """Second method."""
        pass


def standalone_function():
    """A standalone function."""
    pass
```

### Whitespace
- Avoid extraneous whitespace in expressions and statements
- Surround binary operators with a single space on either side
- Don't use spaces around the `=` sign in keyword arguments

```python
# Correct
spam(ham[1], {eggs: 2})
x = 1
y = 2
long_variable = 3

# Wrong
spam( ham[ 1 ], { eggs : 2 } )
x             = 1
y             = 2
long_variable = 3
```

## Naming Conventions

### Variables and Functions
- Use **snake_case** for variable and function names
- Use descriptive names that clearly indicate purpose

```python
# Correct
user_count = 0
def calculate_total_price():
    pass

# Wrong
n = 0
def calc():
    pass
```

### Constants
- Use **UPPER_CASE** with underscores separating words
- Define at module level

```python
MAX_CONNECTIONS = 100
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"
```

### Classes
- Use **PascalCase** (CapWords) for class names
- Use descriptive names that represent the entity

```python
class UserAccount:
    pass

class DatabaseConnection:
    pass
```

### Private Members
- Use leading underscore for internal use
- Use double leading underscore for name mangling (rare cases)

```python
class MyClass:
    def __init__(self):
        self.public = "accessible"
        self._internal = "internal use"
        self.__private = "name mangled"
```

### File and Package Names
- Use lowercase with underscores if needed
- Keep names short but descriptive

```
user_management.py
database_models.py
```

## Comments and Documentation

### Inline Comments
- Use sparingly and only when necessary
- Write complete sentences
- Keep comments up to date with code changes

```python
x = x + 1  # Increment x by one
```

### Block Comments
- Use for complex logic explanation
- Each line starts with `# ` and a single space

```python
# This is a complex algorithm that processes user data
# in multiple steps to ensure data integrity and
# performance optimization
def process_user_data(data):
    pass
```

### Docstrings
- Use for all public modules, functions, classes, and methods
- Use triple double quotes `"""`
- First line should be a brief summary
- Follow Google or NumPy docstring format

```python
def calculate_area(length: float, width: float) -> float:
    """Calculate the area of a rectangle.

    Args:
        length: The length of the rectangle in meters.
        width: The width of the rectangle in meters.

    Returns:
        The area of the rectangle in square meters.

    Raises:
        ValueError: If length or width is negative.
    """
    if length < 0 or width < 0:
        raise ValueError("Length and width must be non-negative")
    return length * width
```

## Imports

### Order
1. Standard library imports
2. Related third-party imports
3. Local application/library specific imports

### Format
- Use absolute imports when possible
- One import per line for `from` imports
- Group imports and separate groups with blank lines

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import requests
from flask import Flask, request

# Local
from geneweb.core import config
from geneweb.db import driver
```

## Error Handling

### Exception Handling
- Use specific exception types
- Avoid bare `except` clauses
- Include meaningful error messages

```python
# Correct
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Invalid value provided: {e}")
    raise
except ConnectionError:
    logger.warning("Connection failed, retrying...")
    retry_connection()

# Wrong
try:
    result = risky_operation()
except:
    pass
```

### Custom Exceptions
- Create custom exceptions for domain-specific errors
- Inherit from appropriate base exception classes

```python
class GeneWebError(Exception):
    """Base exception for GenWeb operations."""
    pass

class DatabaseConnectionError(GeneWebError):
    """Raised when database connection fails."""
    pass
```

## Type Hints

### Usage
- Use type hints for all public functions and methods
- Use for complex data structures and return types
- Import types from `typing` module when needed

```python
from typing import List, Dict, Optional, Union

def process_users(users: List[Dict[str, str]]) -> Optional[str]:
    """Process a list of user dictionaries."""
    if not users:
        return None
    return f"Processed {len(users)} users"

def get_user_by_id(user_id: int) -> Union[Dict[str, str], None]:
    """Retrieve user by ID."""
    # Implementation here
    pass
```

## Tools and Enforcement

### Code Formatting
- **black**: Automatic code formatting
- **isort**: Import sorting

### Code Quality
- **flake8**: Style guide enforcement
- **pylint**: Comprehensive code analysis
- **mypy**: Static type checking

### Pre-commit Hooks
Set up pre-commit hooks to automatically enforce these standards:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
```

### Configuration Files

#### pyproject.toml
```toml
[tool.black]
line-length = 120
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 120

[tool.pylint.messages_control]
max-line-length = 120
```

## Conclusion

Following these conventions ensures code consistency, readability, and maintainability across the project. All team members should familiarize themselves with these standards and use the recommended tools to enforce them automatically.

For questions or suggestions regarding these conventions, please open an issue or discussion in the project repository.

## See also

- `CONTRIBUTING.md` — guide de contribution et workflow de développement
- `docs/DOCUMENTATION_STANDARDS.md` — règles pour la documentation et templates

These documents are the canonical references for coding and documentation standards in this project.
