# Cont## Quick Start (5 minutes)

```bash
# Clone and setup
git clone <repository>
cd python-geneweb-modernization
make setup

# Start developing
make run           # Start main GenEWeb server (port 8080)
# OR
make run-simple    # Start simple test server (port 2317)

# Make changes, then test
make all           # Format + check + test everything
```b Python

Welcome to the GenEWeb Python project! This guide will help you get started with contributing to the project while maintaining our code quality standards.

## 🚀 Quick Start (5 Minutes)

### 1. Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd python-geneweb-modernization

# One-command setup
make setup
```

### 2. Check Everything Works

```bash
# Run the complete development workflow
make all
```

### 3. Make Your First Change

```bash
# Edit files...

# Before committing, run:
make all        # Format, check quality, run tests
```

**That's it!** The Makefile handles all the complexity for you.

## 🛠️ Development Commands

### Main Commands

```bash
make              # Show help (default)
make setup        # Setup development environment
make format       # Format code with black and isort
make check        # Run quality checks (flake8, mypy)
make test         # Run all tests
make all          # Complete workflow: format → check → test
make clean        # Clean generated files
make status       # Show project status
```

### Project Status

```bash
make status       # Shows:
# 📁 Python files: X
# � Lines of code: Y
# 🛠️ Available commands and docs
```

## 📋 Code Standards

### Required Reading
- [Coding Conventions](docs/CODING_CONVENTIONS.md) - **Must read for all contributors**
- [Documentation Standards](docs/DOCUMENTATION_STANDARDS.md) - **Required for API changes**

### Key Standards
- **PEP 8 compliant** with 120 character line limit
- **Google-style docstrings** for all public APIs
- **Type hints** for all function parameters and returns
- **Custom exceptions** for error handling

## 🔧 Development Workflow

### The Simple Way (Recommended)

```bash
# Edit your files...

# Before committing:
make all        # One command does everything:
                # → Formats code (black + isort)
                # → Checks quality (flake8 + mypy)
                # → Runs tests (all test suites)
```

### Manual Commands (If Needed)

```bash
make format     # Just format code
make check      # Just run quality checks
make test       # Just run tests
```

### Pre-commit Hooks

Pre-commit hooks automatically run basic checks when you commit.
If they fail, fix with: `make format`

## 📝 Writing Code

### Function Documentation Template

```python
def example_function(param1: str, param2: Optional[int] = None) -> bool:
    """
    Brief description of what the function does.

    Longer description if needed. Explain complex logic,
    algorithms, or important behavior.

    Args:
        param1: Description of the first parameter
        param2: Description of optional parameter with default

    Returns:
        Description of return value and its meaning

    Raises:
        ValueError: When parameter validation fails
        DatabaseError: When database operation fails

    Example:
        >>> result = example_function("hello", 42)
        >>> print(result)
        True
    """
    # Implementation here
    pass
```

### Class Documentation Template

```python
class ExampleClass:
    """
    Brief description of the class purpose.

    Longer description explaining the class responsibilities,
    main usage patterns, and any important behavior.

    Attributes:
        attribute1: Description of public attribute
        attribute2: Description of another attribute
        _private_attr: Description of private attribute (internal use)

    Example:
        >>> obj = ExampleClass("param")
        >>> result = obj.main_method()
        >>> print(result)
        'expected output'
    """

    def __init__(self, param: str) -> None:
        """
        Initialize the class with given parameters.

        Args:
            param: Description of initialization parameter
        """
        pass
```

### Error Handling

Use our custom exceptions from `geneweb.core.exceptions`:

```python
from geneweb.core.exceptions import DatabaseError, TemplateError, GenEWebError

def example_with_errors():
    """Example showing proper error handling."""
    try:
        # Risky operation
        result = risky_database_operation()
    except ConnectionError as e:
        raise DatabaseError(f"Database connection failed: {e}") from e
    except ValueError as e:
        raise GenEWebError(f"Invalid input provided: {e}") from e
```

## 🧪 Testing

### Writing Tests

Follow the pattern in `test_compliance.py`:

```python
class TestYourFeature(unittest.TestCase):
    """Tests for your new feature."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.test_data = create_test_data()

    def test_specific_behavior(self) -> None:
        """
        Test a specific behavior of your feature.

        This docstring explains what exactly is being tested
        ## 📝 Writing Code

### Function Documentation Template

```python
def example_function(param1: str, param2: Optional[int] = None) -> bool:
    """
    Brief description of what the function does.

    Args:
        param1: Description of the first parameter
        param2: Description of optional parameter with default

    Returns:
        Description of return value and its meaning

    Raises:
        ValueError: When parameter validation fails
        DatabaseError: When database operation fails
    """
    # Implementation here
    pass
```

### Error Handling

Use our custom exceptions from `geneweb.core.exceptions`:

```python
from geneweb.core.exceptions import DatabaseError, TemplateError

try:
    # risky operation
    result = risky_database_operation()
except ConnectionError as e:
    raise DatabaseError(f"Database connection failed: {e}") from e
```

## 🧪 Testing

Add tests following the pattern in `test_compliance.py`:

```python
def test_your_feature(self) -> None:
    """Test description."""
    # Arrange, Act, Assert
    result = your_function("input")
    self.assertEqual(result, "expected")
```

## � Current Quality Status

- ✅ **0 errors** - All code is syntactically correct
- ⚠️ **~430 warnings** - Opportunities for improvement (run `./dev.py` for current count)
- ✅ **13/13 compliance tests passing**

**Goal:** Maintain 0 errors, reduce warnings when possible.

## 🔄 Pull Request Process

1. **Run the full check:** `make all`
2. **Add tests** for new functionality
3. **Update documentation** if you've changed APIs

## 🆘 Getting Help

**Common Issues:**

- **"My code doesn't pass checks"** → `make format` then `make check`
- **"Tests are failing"** → `make test` for details
- **"Pre-commit hooks failing"** → `make format` fixes most issues
- **"Missing development tools"** → `make setup` installs everything

**References:**
- **Standards**: [docs/CODING_CONVENTIONS.md](docs/CODING_CONVENTIONS.md)
- **Documentation**: [docs/DOCUMENTATION_STANDARDS.md](docs/DOCUMENTATION_STANDARDS.md)
- **Examples**: Look at existing code in `gwd_simple.py` and `template_engine.py`

---

**Thank you for contributing to GenEWeb Python!** 🙏

Your contributions help make genealogical research more accessible and maintainable for everyone.
