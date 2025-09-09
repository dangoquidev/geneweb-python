# Python GenEWeb Modernization

This is a careful modernization of the GenEWeb genealogical software, translated from OCaml to Python while preserving all core functionality and historical significance.

## Original GenEWeb

GenEWeb is an open source genealogy software originally written in OCaml. It comes with a Web interface and can be used off-line or as a Web service. This Python modernization maintains compatibility with existing databases and preserves all the original functionality.

## Architecture

The system is structured in modules that mirror the original OCaml implementation:

- `core/` - Core data structures and definitions
- `db/` - Database management and storage
- `web/` - Web server and HTTP handling
- `import_export/` - Data import/export functionality
- `display/` - Web interface and templating
- `util/` - Utility functions and helpers
- `security/` - Authentication and authorization
- `plugins/` - Plugin system
- `bin/` - Command-line utilities

## Installation

```bash
pip install -r requirements.txt
python setup.py install
```

## Usage

Start the web server:
```bash
python -m geneweb.server --port 2317 --base-dir /path/to/databases
```

## Compatibility

This Python version maintains compatibility with:
- Original GenEWeb database formats
- GEDCOM import/export
- Web interface templates
- Authentication systems
- Plugin architecture

## Development

The code has been carefully translated to preserve the original structure and behavior while using modern Python patterns and libraries.
