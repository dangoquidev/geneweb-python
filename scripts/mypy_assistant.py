#!/usr/bin/env python3
"""
Assistant pour les erreurs MyPy - Aide à identifier et proposer des corrections
"""

import os
import subprocess
import sys
from typing import Dict, List


class MyPyAssistant:
    """Assistant pour analyser et proposer des corrections mypy"""

    def __init__(self):
        self.safe_fixes = {
            # Corrections sûres et automatisables
            "Need type annotation for": self._suggest_type_annotation,
            "imported but unused": self._suggest_remove_import,
            "Returning Any from function": self._suggest_return_type,
            "has no attribute": self._suggest_attribute_fix,
        }

    def run_mypy(self) -> List[str]:
        """Exécuter mypy et récupérer les erreurs"""
        try:
            result = subprocess.run(
                ["mypy", "--ignore-missing-imports", "src/"],
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src", **os.environ},
            )
            return result.stdout.split("\n") if result.stdout else []
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution de mypy: {e}")
            return []

    def analyze_errors(self) -> Dict[str, List[str]]:
        """Analyser les erreurs et les catégoriser"""
        errors = self.run_mypy()
        categorized = {
            "safe_to_fix": [],  # Corrections automatisables
            "needs_review": [],  # Nécessite révision manuelle
            "type_issues": [],  # Problèmes de types
            "import_issues": [],  # Problèmes d'imports
            "logic_issues": [],  # Problèmes de logique
        }

        for error in errors:
            if not error.strip() or "Found" in error and "error" in error:
                continue

            if "Need type annotation" in error:
                categorized["safe_to_fix"].append(error)
            elif "imported but unused" in error:
                categorized["import_issues"].append(error)
            elif "Returning Any" in error:
                categorized["type_issues"].append(error)
            elif any(keyword in error for keyword in ["has no attribute", "Incompatible"]):
                categorized["logic_issues"].append(error)
            else:
                categorized["needs_review"].append(error)

        return categorized

    def _suggest_type_annotation(self, error: str) -> str:
        """Suggérer une annotation de type"""
        if "list[" in error:
            return "💡 Suggestion: Ajouter `= []` ou spécifier le type avec `list[str] = []`"
        elif "dict[" in error:
            return "💡 Suggestion: Ajouter `= {}` ou spécifier le type avec `dict[str, str] = {}`"
        return "💡 Suggestion: Ajouter une annotation de type appropriée"

    def _suggest_remove_import(self, error: str) -> str:
        """Suggérer la suppression d'un import"""
        return "💡 Suggestion: Supprimer cet import inutilisé avec `make autofix`"

    def _suggest_return_type(self, error: str) -> str:
        """Suggérer un type de retour"""
        return "💡 Suggestion: Spécifier le type de retour de la fonction ou convertir Any"

    def _suggest_attribute_fix(self, error: str) -> str:
        """Suggérer une correction d'attribut"""
        return "💡 Suggestion: Vérifier l'existence de l'attribut ou ajouter une vérification"

    def generate_report(self):
        """Générer un rapport détaillé"""
        print("🔍 Analyse des erreurs MyPy...")
        print("=" * 50)

        errors = self.analyze_errors()

        if not any(errors.values()):
            print("🎉 Aucune erreur MyPy détectée !")
            return

        # Erreurs automatisables
        if errors["safe_to_fix"]:
            print("\\n✅ CORRECTIONS AUTOMATISABLES:")
            print("-" * 30)
            for error in errors["safe_to_fix"]:
                print(f"📝 {error}")
                for pattern, suggestion_func in self.safe_fixes.items():
                    if pattern in error:
                        print(f"   {suggestion_func(error)}")
                        break

        # Problèmes d'imports
        if errors["import_issues"]:
            print("\\n📦 PROBLÈMES D'IMPORTS:")
            print("-" * 30)
            for error in errors["import_issues"]:
                print(f"📝 {error}")
                print("   💡 Suggestion: Exécuter `make autofix` pour nettoyer")

        # Problèmes de types
        if errors["type_issues"]:
            print("\\n🏷️  PROBLÈMES DE TYPES:")
            print("-" * 30)
            for error in errors["type_issues"]:
                print(f"📝 {error}")
                print("   💡 Suggestion: Révision manuelle nécessaire")

        # Problèmes de logique
        if errors["logic_issues"]:
            print("\\n⚠️  PROBLÈMES DE LOGIQUE (CRITIQUES):")
            print("-" * 30)
            for error in errors["logic_issues"]:
                print(f"📝 {error}")
                print("   🚨 Suggestion: Correction manuelle OBLIGATOIRE")

        # Autres erreurs
        if errors["needs_review"]:
            print("\\n🔍 NÉCESSITE RÉVISION:")
            print("-" * 30)
            for error in errors["needs_review"]:
                print(f"📝 {error}")

        # Statistiques
        total_errors = sum(len(error_list) for error_list in errors.values())
        safe_count = len(errors["safe_to_fix"])
        critical_count = len(errors["logic_issues"])

        print("\\n" + "=" * 50)
        print("📊 STATISTIQUES:")
        print(f"   Total d'erreurs: {total_errors}")
        print(f"   Automatisables: {safe_count}")
        print(f"   Critiques: {critical_count}")
        print(f"   Nécessitent révision: {total_errors - safe_count}")

        # Recommandations
        print("\\n🎯 RECOMMANDATIONS:")
        if safe_count > 0:
            print("   1. Corrections automatiques disponibles")
        if critical_count > 0:
            print("   2. ⚠️  Corriger les erreurs critiques en priorité")
        print("   3. Réviser manuellement les erreurs de types")
        print("   4. Utiliser `make check` régulièrement")

    def suggest_quick_fixes(self):
        """Suggérer des corrections rapides sûres"""
        print("\\n🚀 CORRECTIONS RAPIDES SUGGÉRÉES:")
        print("make autofix     # Nettoyer imports + style")
        print("make format      # Formatage complet")
        print("make check       # Vérifier l'état")


def main():
    """Point d'entrée principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("📚 Assistant MyPy - Aide aux corrections")
        print("Usage:")
        print("  python3 scripts/mypy_assistant.py         # Rapport complet")
        print("  python3 scripts/mypy_assistant.py --quick # Suggestions rapides")
        return

    assistant = MyPyAssistant()

    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        assistant.suggest_quick_fixes()
    else:
        assistant.generate_report()


if __name__ == "__main__":
    main()
