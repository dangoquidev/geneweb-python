#!/usr/bin/env python3
"""
Script pour corriger automatiquement les erreurs MyPy SÛRES
ATTENTION: Ne corrige que les annotations de types manquantes simples
"""

import os
import re
import sys


class SafeMyPyFixer:
    """Correcteur sûr pour certaines erreurs mypy"""

    def __init__(self):
        self.fixes_applied = 0
        self.files_modified = []

    def fix_type_annotations(self, file_path: str) -> bool:
        """Corriger les annotations de types manquantes simples"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Pattern pour __all__: list[str] = [...]
            all_pattern = r"^(\s*)(__all__)\s*=\s*(\[.*?\])$"
            content = re.sub(all_pattern, r"\1\2: list[str] = \3", content, flags=re.MULTILINE)

            # Pattern pour variables avec listes vides
            # Cherche: variable = []
            # Remplace par: variable: list[str] = []
            list_pattern = r"^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\[\s*\]$"
            content = re.sub(list_pattern, r"\1\2: list[str] = []", content, flags=re.MULTILINE)

            # Pattern pour variables avec dictionnaires vides
            # Cherche: variable = {}
            # Remplace par: variable: dict[str, str] = {}
            dict_pattern = r"^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{\s*\}$"
            content = re.sub(dict_pattern, r"\1\2: dict[str, str] = {}", content, flags=re.MULTILINE)

            # Seulement écrire si des changements ont été faits
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return True

            return False

        except Exception as e:
            print(f"❌ Erreur lors de la correction de {file_path}: {e}")
            return False

    def process_files(self) -> None:
        """Traiter tous les fichiers Python"""
        python_files = []

        # Trouver tous les fichiers Python
        for root, dirs, files in os.walk("src"):
            # Ignorer les répertoires cachés et __pycache__
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        print(f"🔍 Analyse de {len(python_files)} fichiers Python...")

        for file_path in python_files:
            if self.fix_type_annotations(file_path):
                self.files_modified.append(file_path)
                self.fixes_applied += 1
                print(f"✅ {file_path}")

        print("\n📊 Résumé:")
        print(f"   Fichiers modifiés: {len(self.files_modified)}")
        print(f"   Total corrections: {self.fixes_applied}")

        if self.files_modified:
            print("\n📝 Fichiers modifiés:")
            for file_path in self.files_modified:
                print(f"   - {file_path}")
            print("\n💡 Conseil: Exécutez 'make check' pour vérifier les corrections")
        else:
            print("\n🎉 Aucune correction automatique nécessaire!")


def main():
    """Point d'entrée principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("🔧 Correcteur MyPy sûr")
        print("Ne corrige que les annotations de types manquantes SIMPLES:")
        print("- __all__: list[str] = [...]")
        print("- variable: list[str] = []")
        print("- variable: dict[str, str] = {}")
        print("\\nATTENTION: NE PAS utiliser pour les erreurs complexes!")
        return

    print("🔧 Correction automatique des annotations MyPy sûres...")
    print("⚠️  Ne corrige que les cas simples et sûrs")
    print("=" * 50)

    fixer = SafeMyPyFixer()
    fixer.process_files()


if __name__ == "__main__":
    main()
