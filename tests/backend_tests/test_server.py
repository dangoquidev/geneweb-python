#!/usr/bin/env python3
"""
Test du serveur GenEWeb Python
Simple script pour tester la connexion HTTP
"""


import requests


def test_server(url="http://localhost:8080"):
    """Test la connexion au serveur GenEWeb"""
    print(f"Test de connexion à {url}...")

    try:
        response = requests.get(url, timeout=10)
        print(f"✅ Statut: {response.status_code}")
        print(f"✅ Content-Type: {response.headers.get('Content-Type', 'Non spécifié')}")
        print(f"✅ Taille réponse: {len(response.content)} bytes")

        if response.status_code == 200:
            print("\n📄 Début du contenu HTML:")
            content = response.text[:500]  # Premiers 500 caractères
            print(content)
            if len(response.text) > 500:
                print("... (tronqué)")

            # Vérifier si c'est du HTML valide
            if "<html" in response.text.lower() or "<body" in response.text.lower():
                print("✅ HTML valide détecté")
            else:
                print("⚠️  Pas de HTML valide détecté")

        return True

    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au serveur")
        print("   Le serveur est-il démarré sur le port 2317 ?")
        return False

    except requests.exceptions.Timeout:
        print("❌ Erreur: Timeout de connexion")
        return False

    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False


def test_database_pages():
    """Test les pages spécifiques aux bases de données"""
    print("\nTest des pages de bases de données...")

    bases = ["sample_family", "ma_famille"]

    for base in bases:
        url = f"http://localhost:8080/{base}"
        print(f"\nTest de {url}...")

        try:
            response = requests.get(url, timeout=5)
            print(f"  Statut: {response.status_code}")

            if response.status_code == 200:
                print("  ✅ Page accessible")
            elif response.status_code == 404:
                print("  ⚠️  Page non trouvée")
            else:
                print(f"  ⚠️  Statut inattendu: {response.status_code}")

        except Exception as e:
            print(f"  ❌ Erreur: {e}")


if __name__ == "__main__":
    print("🧪 Test du serveur GenEWeb Python")
    print("=" * 40)

    # Test de la page principale
    success = test_server()

    if success:
        # Test des pages de bases de données
        test_database_pages()

        print("\n🎉 Serveur fonctionne correctement !")
        print("Vous pouvez ouvrir http://localhost:8080 dans votre navigateur.")
    else:
        print("\n❌ Le serveur ne répond pas correctement.")
        print("Vérifiez que le serveur est démarré avec:")
        print("python -m geneweb.cli server --port 8080 --database-dir .")

    print("\n" + "=" * 40)
