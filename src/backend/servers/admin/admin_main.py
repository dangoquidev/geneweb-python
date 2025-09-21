#!/usr/bin/env python3
"""
Point d'entrée principal pour le serveur d'administration GenEWeb

Ce script peut être utilisé de plusieurs façons :
1. python admin_main.py [options]
2. python -m geneweb.admin [options]
3. gwsetup [options] (après installation du package)
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.backend.servers.admin.admin_server import main

if __name__ == "__main__":
    main()