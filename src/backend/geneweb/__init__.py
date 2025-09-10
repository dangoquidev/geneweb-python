"""
GenEWeb Python Modernization
============================

A modern Python implementation of the GenEWeb genealogical software,
carefully translated from OCaml while preserving all core functionality
and historical significance.
"""

__version__ = "1.0.0"
__author__ = "GenEWeb Python Modernization Project"
__license__ = "GPL-2.0-only"

# Core modules
from . import core, db, security, util, web
from .core.config import Config
from .db.driver import DatabaseDriver

# Main entry points
from .web.server import start_server
