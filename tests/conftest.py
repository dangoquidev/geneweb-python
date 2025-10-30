"""Configuration pytest et fixtures partagées pour les tests."""

import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH pour les imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
