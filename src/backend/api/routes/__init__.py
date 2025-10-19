"""
API routes for GenEWeb.

Modular route handlers for different resource types.
"""

from backend.api.routes import families, health, persons, search

__all__ = ["health", "persons", "families", "search"]
