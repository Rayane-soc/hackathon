#!/usr/bin/env python3
"""
Script de test pour vérifier l'accès aux fichiers JSON via le serveur local
"""

import requests
import json

def test_server_access():
    """Test l'accès aux fichiers JSON via le serveur local"""
    base_url = "http://localhost:8000"

    print("🧪 Test d'accès au serveur local...")
    print(f"📡 URL de base: {base_url}")

    # Test accès aux fichiers JSON
    files_to_test = [
        "/plants_data.json",
        "/plants_by_category.json",
        "/blank.html"
    ]

    for file_path in files_to_test:
        try:
            url = base_url + file_path
            print(f"\n🔍 Test de {file_path}...")

            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                print(f"✅ {file_path} : OK ({len(response.text)} caractères)")

                # Pour les fichiers JSON, vérifier qu'ils sont valides
                if file_path.endswith('.json'):
                    try:
                        data = response.json()
                        if file_path == "/plants_data.json":
                            total_plants = data.get('metadata', {}).get('total_plants', 0)
                            print(f"   📊 {total_plants} plantes dans la base de données")
                        elif file_path == "/plants_by_category.json":
                            categories = list(data.keys())
                            print(f"   📂 Catégories: {', '.join(categories)}")
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON invalide: {e}")
            else:
                print(f"❌ {file_path} : Erreur {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"❌ {file_path} : Erreur de connexion - {e}")
        except Exception as e:
            print(f"❌ {file_path} : Erreur inattendue - {e}")

    print("\n" + "="*50)
    print("🎯 Test terminé!")

if __name__ == "__main__":
    test_server_access()
