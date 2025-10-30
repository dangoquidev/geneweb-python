"""
Package de gestion de base de données pour GenEWeb.

Ce package fournit une abstraction pour gérer les bases de données généalogiques
avec support de multiples formats (Pickle, JSON, etc.).
"""

from .base import DatabaseDriver
from .pickle_driver import PickleDriver
from .repository import Repository

__all__ = ["DatabaseDriver", "PickleDriver", "Repository"]
