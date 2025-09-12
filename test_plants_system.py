#!/usr/bin/env python3
"""
Script de test rapide du système de plantes
"""

import json
from plants_database import plants_db
from plants_data_collector import PlantDataCollector

def test_database():
    """Test de la base de données"""
    print("=== TEST BASE DE DONNÉES ===")

    # Test de sauvegarde
    test_plant = {
        'scientific_name': 'Test Plant',
        'common_names': ['Plante Test'],
        'family': 'Testaceae',
        'description': 'Une plante de test',
        'categories': [{'category': 'test', 'subcategory': 'unit'}],
        'care_instructions': {'watering': 'weekly'},
        'weather_data': {'temperature_min': 10, 'temperature_max': 30}
    }

    try:
        plant_id = plants_db.save_plant(test_plant)
        print(f"✅ Sauvegarde réussie - ID: {plant_id}")

        # Test de récupération
        retrieved = plants_db.get_plant('Test Plant')
        if retrieved:
            print(f"✅ Récupération réussie: {retrieved['scientific_name']}")
        else:
            print("❌ Échec de récupération")

        # Test de recherche
        results = plants_db.search_plants('test')
        print(f"✅ Recherche trouvée: {len(results)} résultats")

        # Statistiques
        stats = plants_db.get_stats()
        print(f"✅ Statistiques: {stats['total_plants']} plantes")

    except Exception as e:
        print(f"❌ Erreur base de données: {e}")

def test_collector():
    """Test du collecteur de données"""
    print("\n=== TEST COLLECTEUR ===")

    collector = PlantDataCollector()

    test_plants = ["Rosa rugosa", "Quercus robur"]

    for plant in test_plants:
        try:
            print(f"\n🌱 Test de {plant}:")
            data = collector.collect_comprehensive_plant_data(plant)

            if data:
                print(f"✅ Données collectées: {len(data.get('sources', {}))} sources")
                print(f"   - Nom scientifique: {data.get('scientific_name')}")
                print(f"   - Noms communs: {data.get('common_names', [])}")
                print(f"   - Famille: {data.get('family', 'N/A')}")
                print(f"   - Catégories: {len(data.get('categories', []))}")

                # Sauvegarde en base
                plant_id = plants_db.save_plant(data)
                print(f"✅ Sauvegardé en base - ID: {plant_id}")
            else:
                print("❌ Aucune donnée collectée")

        except Exception as e:
            print(f"❌ Erreur pour {plant}: {e}")

def test_integration():
    """Test de l'intégration complète"""
    print("\n=== TEST INTÉGRATION ===")

    from plants_integration import PlantsIntegrationSystem

    integration = PlantsIntegrationSystem()

    # Test avec une petite liste
    test_plants = ["Tulipa gesneriana", "Mentha piperita"]

    try:
        stats = integration.process_plant_list(test_plants, batch_size=2)

        print("✅ Intégration réussie:")
        print(f"   - Traité: {stats['total_processed']}")
        print(f"   - Réussi: {stats['successful_collects']}")
        print(f"   - Sauvegardé: {stats['saved_to_db']}")

        # Vérification en base
        final_stats = plants_db.get_stats()
        print(f"✅ Base finale: {final_stats['total_plants']} plantes")

    except Exception as e:
        print(f"❌ Erreur intégration: {e}")

def show_sample_data():
    """Affiche un échantillon des données"""
    print("\n=== ÉCHANTILLON DE DONNÉES ===")

    try:
        # Recherche par catégorie
        categories = ['fleurs', 'arbres', 'legumes']

        for category in categories:
            plants = plants_db.get_plants_by_category(category, limit=1)
            if plants:
                plant = plants[0]
                print(f"\n📋 {category.upper()}:")
                print(f"   Nom: {plant.get('scientific_name')}")
                print(f"   Commun: {plant.get('common_names', ['N/A'])[0]}")
                print(f"   Description: {plant.get('description', 'N/A')[:100]}...")

    except Exception as e:
        print(f"❌ Erreur échantillon: {e}")

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS DU SYSTÈME DE PLANTES")
    print("=" * 50)

    try:
        # Test de la base de données
        test_database()

        # Test du collecteur
        test_collector()

        # Test d'intégration
        test_integration()

        # Affichage d'échantillon
        show_sample_data()

        print("\n" + "=" * 50)
        print("✅ TESTS TERMINÉS")

        # Statistiques finales
        final_stats = plants_db.get_stats()
        print("\n📊 STATISTIQUES FINALES:")
        for key, value in final_stats.items():
            if isinstance(value, int) and value > 0:
                print(f"   {key}: {value}")

    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
