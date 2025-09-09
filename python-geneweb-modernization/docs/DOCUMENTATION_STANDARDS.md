# Documentation Standards

This document defines the documentation standards for the Python GenWeb Modernization project. Comprehensive and well-structured documentation is essential for project maintainability, onboarding new contributors, and ensuring long-term success.

## Table of Contents

1. [Documentation Philosophy](#documentation-philosophy)
2. [Types of Documentation](#types-of-documentation)
3. [Code Documentation](#code-documentation)
4. [API Documentation](#api-documentation)
5. [User Documentation](#user-documentation)
6. [Project Documentation](#project-documentation)
7. [Documentation Tools](#documentation-tools)
8. [Review Process](#review-process)

## Documentation Philosophy

### Core Principles

- **Clarity over Cleverness**: Write clear, straightforward documentation that can be understood by developers of varying experience levels
- **Keep It Current**: Documentation must be updated alongside code changes
- **User-Focused**: Consider the reader's perspective and needs
- **Comprehensive but Concise**: Provide complete information without unnecessary verbosity
- **Examples Drive Understanding**: Include practical examples wherever possible

### Target Audiences

1. **New Contributors**: Developers joining the project
2. **Maintainers**: Current team members working on the codebase
3. **End Users**: People using the GenWeb application
4. **API Consumers**: Developers integrating with our APIs

## Types of Documentation

### 1. Code Documentation
- Inline comments
- Docstrings
- Type annotations

### 2. API Documentation
- Endpoint descriptions
- Request/response schemas
- Authentication details
- Usage examples

### 3. User Documentation
- Installation guides
- User manuals
- Tutorials
- FAQ sections

### 4. Project Documentation
- Architecture overviews
- Development setup
- Contribution guidelines
- Release notes

## Code Documentation

### Docstring Standards

#### Format
Use **Google-style docstrings** for consistency and readability.

#### Module Docstrings
```python
"""GenWeb Core Configuration Module.

This module provides configuration management for the GenWeb application,
including database settings, security parameters, and application defaults.

Example:
    Basic usage of the configuration module:

    >>> from geneweb.core import config
    >>> db_url = config.get_database_url()
    >>> print(db_url)
    'sqlite:///geneweb.db'

Attributes:
    DEFAULT_DB_PATH (str): Default path for SQLite database
    MAX_SEARCH_RESULTS (int): Maximum number of search results to return
"""
```

#### Class Docstrings
```python
class DatabaseManager:
    """Manages database connections and operations.

    The DatabaseManager class provides a high-level interface for database
    operations, including connection pooling, transaction management, and
    query execution with proper error handling.

    Attributes:
        connection_url (str): Database connection URL
        pool_size (int): Maximum number of connections in the pool
        is_connected (bool): Current connection status

    Example:
        >>> db = DatabaseManager("sqlite:///test.db")
        >>> db.connect()
        >>> users = db.get_all_users()
        >>> db.close()
    """
```

#### Function/Method Docstrings
```python
def search_person(name: str, birth_year: Optional[int] = None) -> List[Person]:
    """Search for persons by name and optional birth year.

    Performs a case-insensitive search for persons matching the given name.
    Optionally filters results by birth year if provided. Results are sorted
    by relevance score.

    Args:
        name: Full or partial name to search for. Minimum 2 characters.
        birth_year: Optional birth year to filter results. Must be between
            1800 and current year.

    Returns:
        List of Person objects matching the search criteria. Empty list if
        no matches found. Limited to 100 results maximum.

    Raises:
        ValueError: If name is less than 2 characters or birth_year is invalid.
        DatabaseError: If database connection fails during search.

    Example:
        >>> results = search_person("Smith", 1950)
        >>> for person in results:
        ...     print(f"{person.name} - {person.birth_year}")
        John Smith - 1950
        Jane Smith - 1952
    """
```

#### Property Docstrings
```python
class Person:
    @property
    def age(self) -> Optional[int]:
        """Current age of the person in years.

        Calculates age based on birth date and current date. Returns None
        if birth date is unknown or person is deceased.

        Returns:
            Age in years, or None if birth date unavailable.
        """
```

### Inline Comments

#### When to Use
- Complex algorithms or business logic
- Non-obvious code behavior
- Temporary workarounds or TODOs
- Performance-critical sections

#### Style Guidelines
```python
# Correct: Explain the "why", not the "what"
user_score = calculate_base_score() * 1.2  # Apply 20% bonus for premium users

# Wrong: Stating the obvious
user_score = user_score + 10  # Add 10 to user score

# Complex logic explanation
# The following algorithm implements a modified Levenshtein distance
# to handle genealogical name variations (nicknames, spelling changes)
# while maintaining O(n*m) time complexity
similarity_score = calculate_name_similarity(name1, name2)
```

#### TODO Comments
```python
# TODO: Implement caching for frequently accessed genealogy data
# TODO(username): Add validation for international date formats
# FIXME: Handle edge case when person has multiple birth records
# HACK: Temporary workaround for legacy database schema
```

## API Documentation

### REST API Documentation

Use **OpenAPI/Swagger** specification for REST APIs:

```yaml
openapi: 3.0.0
info:
  title: GenWeb API
  version: 1.0.0
  description: API for genealogical data management
paths:
  /api/persons/{id}:
    get:
      summary: Get person by ID
      description: Retrieve detailed information about a specific person
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
          description: Unique identifier for the person
      responses:
        '200':
          description: Person details retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Person'
        '404':
          description: Person not found
```

### Endpoint Documentation Template

```python
@app.route('/api/persons/<int:person_id>', methods=['GET'])
def get_person(person_id: int):
    """Get person details by ID.

    Retrieves comprehensive information about a person including:
    - Basic demographics (name, birth/death dates)
    - Family relationships (parents, spouse, children)
    - Associated events and sources

    Path Parameters:
        person_id (int): Unique identifier for the person

    Returns:
        200: Person details in JSON format
        404: Person not found
        500: Internal server error

    Example Request:
        GET /api/persons/123

    Example Response:
        {
            "id": 123,
            "name": "John Doe",
            "birth_date": "1950-01-15",
            "birth_place": "New York, NY",
            "parents": [456, 789],
            "children": [101, 102]
        }
    """
```

## User Documentation

### Installation Guide Structure
```markdown
# Installation Guide

## Prerequisites
- System requirements
- Dependencies

## Installation Steps
1. Step-by-step instructions
2. With code examples
3. Expected outputs

## Verification
- How to test the installation
- Common troubleshooting

## Next Steps
- Links to tutorials
- Configuration options
```

### Tutorial Standards
- **Step-by-step format** with clear numbered instructions
- **Screenshot or code examples** for each major step
- **Expected outcomes** clearly stated
- **Troubleshooting sections** for common issues
- **Progressive complexity** from basic to advanced topics

### FAQ Format
```markdown
## Frequently Asked Questions

### How do I import data from GEDCOM files?

**Answer:** GenWeb supports GEDCOM import through the web interface:

1. Navigate to Data → Import
2. Select your GEDCOM file
3. Choose import options
4. Click "Import Data"

See the [GEDCOM Import Guide](gedcom-import.md) for detailed instructions.
```

## Project Documentation

### README Structure
```markdown
# Project Name

Brief description of what the project does.

## Features
- Key feature 1
- Key feature 2
- Key feature 3

## Installation
Quick installation instructions with link to detailed guide.

## Quick Start
Basic usage example to get users started immediately.

## Documentation
- [User Guide](docs/user-guide.md)
- [API Reference](docs/api-reference.md)
- [Development Setup](docs/development.md)

## Contributing
Link to contribution guidelines.

## License
License information.
```

### Architecture Documentation
- **System overview diagrams**
- **Component relationships**
- **Data flow descriptions**
- **Technology stack explanations**
- **Design decision rationales**

## Documentation Tools

### Recommended Tools

1. **Sphinx**: Python documentation generator
   - Supports reStructuredText and Markdown
   - Auto-generates API docs from docstrings
   - Multiple output formats (HTML, PDF, EPUB)

2. **MkDocs**: Markdown-based documentation
   - Simple configuration
   - Live preview during development
   - Beautiful themes available

3. **Swagger/OpenAPI**: API documentation
   - Interactive API explorer
   - Code generation capabilities
   - Standards-compliant

### Configuration Examples

#### Sphinx Configuration (conf.py)
```python
# Sphinx configuration
project = 'GenWeb'
copyright = '2025, GenWeb Team'
author = 'GenWeb Team'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',  # Google-style docstrings
    'sphinx.ext.intersphinx',
]

html_theme = 'sphinx_rtd_theme'
autodoc_typehints = 'description'
```

#### MkDocs Configuration (mkdocs.yml)
```yaml
site_name: GenWeb Documentation
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections

nav:
  - Home: index.md
  - User Guide:
    - Installation: user-guide/installation.md
    - Quick Start: user-guide/quickstart.md
  - API Reference: api-reference.md
  - Development: development.md

markdown_extensions:
  - codehilite
  - toc:
      permalink: true
```

## Review Process

### Documentation Review Checklist

#### Content Review
- [ ] **Accuracy**: Information is correct and up-to-date
- [ ] **Completeness**: All necessary information is included
- [ ] **Clarity**: Content is easy to understand
- [ ] **Examples**: Practical examples are provided where helpful
- [ ] **Links**: All internal and external links work correctly

#### Technical Review
- [ ] **Code Examples**: All code examples are tested and working
- [ ] **API Changes**: Documentation reflects current API structure
- [ ] **Dependencies**: Version requirements are accurate
- [ ] **Compatibility**: Platform and version compatibility noted

#### Style Review
- [ ] **Grammar**: Proper grammar and spelling
- [ ] **Formatting**: Consistent with style guide
- [ ] **Structure**: Logical organization and flow
- [ ] **Tone**: Appropriate for target audience

### Review Process Steps

1. **Author Review**: Self-review before submission
2. **Peer Review**: Technical review by team member
3. **User Testing**: Test documentation with target audience
4. **Final Approval**: Sign-off by documentation lead

### Documentation Maintenance

#### Regular Reviews
- **Monthly**: Check for broken links and outdated information
- **Release Cycles**: Update documentation for new features
- **Quarterly**: Comprehensive review of all documentation

#### Version Control
- Track documentation changes alongside code changes
- Use semantic versioning for major documentation updates
- Maintain changelog for documentation modifications

## Conclusion

Quality documentation is as important as quality code. Following these standards ensures that our documentation serves its intended purpose: making the GenWeb project accessible, maintainable, and successful.

Remember: **Good documentation is written for the reader, not the writer.**
