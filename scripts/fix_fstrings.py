#!/usr/bin/env python3
"""
Script pour corriger automatiquement les f-strings sans placeholders
"""

import os
import re


def fix_fstrings_in_file(filepath):
    """Corriger les f-strings sans placeholders dans un fichier"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Regex pour détecter les f-strings sans placeholders
        # Éviter les templates HTML qui contiennent des {{ }}
        pattern = r'f"([^"]*)"'

        def replace_fstring(match):
            string_content = match.group(1)
            # Si la chaîne contient des {}, la garder en f-string
            if "{" in string_content and "}" in string_content:
                return match.group(0)  # Garder tel quel
            # Sinon, convertir en string normale
            return f'"{string_content}"'

        content = re.sub(pattern, replace_fstring, content)

        # Faire la même chose pour les f-strings avec apostrophes
        pattern = r"f'([^']*)'"

        def replace_fstring_single(match):
            string_content = match.group(1)
            if "{" in string_content and "}" in string_content:
                return match.group(0)
            return f"'{string_content}'"

        content = re.sub(pattern, replace_fstring_single, content)

        # Écrire seulement si modifié
        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✅ Corrigé: {filepath}")
            return True
        return False

    except Exception as e:
        print(f"  ❌ Erreur avec {filepath}: {e}")
        return False


def main():
    """Corriger tous les fichiers Python du projet"""
    print("🔧 Correction des f-strings sans placeholders...")

    fixed_count = 0

    # Parcourir tous les fichiers Python
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                if fix_fstrings_in_file(filepath):
                    fixed_count += 1

    print(f"✅ {fixed_count} fichiers corrigés")


if __name__ == "__main__":
    main()
