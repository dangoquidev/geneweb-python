#!/usr/bin/env python3
"""
Créer une base de données de démonstration simple pour GenEWeb.

Ce script crée un fichier pickle avec des données minimales mais valides
pour que l'application puisse démarrer sans erreur.
"""

import os
import pickle
from datetime import datetime


def create_demo_database():
    """Créer une base de données de démonstration avec quelques personnes."""

    # Structure de base GenEWeb (simplifiée)
    demo_data = {
        # Base metadata
        "metadata": {
            "name": "showcase",
            "created": datetime.now().isoformat(),
            "version": "1.0.0",
            "description": "Base de démonstration GenEWeb",
        },
        # Personnes (dictionnaire avec id comme clé)
        "persons": {
            "p001": {
                "id": "p001",
                "first_name": "Jean",
                "surname": "DUPONT",
                "sex": "M",
                "birth_date": "1950-01-15",
                "birth_place": "Paris, France",
                "occupation": "Ingénieur",
                "notes": "Fondateur de la famille Dupont dans cette base",
            },
            "p002": {
                "id": "p002",
                "first_name": "Marie",
                "surname": "MARTIN",
                "sex": "F",
                "birth_date": "1952-03-22",
                "birth_place": "Lyon, France",
                "occupation": "Professeure",
                "notes": "Épouse de Jean Dupont",
            },
            "p003": {
                "id": "p003",
                "first_name": "Pierre",
                "surname": "DUPONT",
                "sex": "M",
                "birth_date": "1975-07-10",
                "birth_place": "Marseille, France",
                "occupation": "Médecin",
                "notes": "Fils de Jean et Marie",
            },
            "p004": {
                "id": "p004",
                "first_name": "Sophie",
                "surname": "BERNARD",
                "sex": "F",
                "birth_date": "1978-11-03",
                "birth_place": "Nice, France",
                "occupation": "Architecte",
                "notes": "Épouse de Pierre Dupont",
            },
            "p005": {
                "id": "p005",
                "first_name": "Lucas",
                "surname": "DUPONT",
                "sex": "M",
                "birth_date": "2005-04-18",
                "birth_place": "Toulouse, France",
                "notes": "Fils de Pierre et Sophie",
            },
        },
        # Familles (dictionnaire avec id comme clé)
        "families": {
            "f001": {
                "id": "f001",
                "husband_id": "p001",
                "wife_id": "p002",
                "marriage_date": "1974-06-15",
                "marriage_place": "Mairie de Paris 15ème",
                "children_ids": ["p003"],
                "notes": "Premier mariage de la base",
            },
            "f002": {
                "id": "f002",
                "husband_id": "p003",
                "wife_id": "p004",
                "marriage_date": "2002-09-21",
                "marriage_place": "Mairie de Marseille 8ème",
                "children_ids": ["p005"],
                "notes": "Deuxième génération",
            },
        },
        # Statistiques
        "stats": {"persons_count": 5, "families_count": 2, "marriages_count": 2, "births_count": 5},
    }

    return demo_data


def main():
    """Fonction principale."""
    print("🏗️  Création de la base de données de démonstration...")

    # Créer le répertoire data s'il n'existe pas
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"📁 Répertoire {data_dir} créé")

    # Créer les données de démonstration
    demo_data = create_demo_database()

    # Sauvegarder dans le fichier pickle
    pickle_file = os.path.join(data_dir, "showcase.pickle")

    try:
        with open(pickle_file, "wb") as f:
            pickle.dump(demo_data, f)

        print(f"✅ Base de données créée: {pickle_file}")
        print("📊 Contenu:")
        print(f"   • {demo_data['stats']['persons_count']} personnes")
        print(f"   • {demo_data['stats']['families_count']} familles")
        print(f"   • {demo_data['stats']['marriages_count']} mariages")

        # Tester le fichier
        with open(pickle_file, "rb") as f:
            pickle.load(f)
            print("✅ Fichier testé et chargé avec succès")

    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
