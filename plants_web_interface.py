#!/usr/bin/env python3
"""
Interface web pour la base de données de plantes
Génère les données JSON pour l'intégration avec blank.html
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any
from plants_database import plants_db

class PlantsWebInterface:
    """Interface web pour exposer les données de plantes"""

    def __init__(self):
        self.db_path = 'plants_comprehensive.db'

    def generate_plants_json(self) -> str:
        """Génère un fichier JSON avec toutes les plantes pour le web"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Récupère toutes les plantes avec leurs catégories
                cursor.execute('''
                    SELECT
                        p.id, p.scientific_name, p.common_names, p.family,
                        p.genus, p.species, p.description, p.care_instructions,
                        p.climate_data, p.sources, p.image_urls,
                        GROUP_CONCAT(pc.category || ':' || COALESCE(pc.subcategory, '')) as categories,
                        pwd.temperature_min, pwd.temperature_max,
                        pwd.humidity_min, pwd.humidity_max,
                        pwd.sunlight_hours_min, pwd.sunlight_hours_max
                    FROM plants p
                    LEFT JOIN plant_categories pc ON p.id = pc.plant_id
                    LEFT JOIN plant_weather_data pwd ON p.id = pwd.plant_id
                    WHERE p.scientific_name != 'Test Plant'  -- Exclure les données de test
                    GROUP BY p.id
                    ORDER BY p.scientific_name
                ''')

                plants_data = []
                for row in cursor.fetchall():
                    plant = {
                        'id': row[0],
                        'scientific_name': row[1],
                        'common_names': json.loads(row[2] or '[]'),
                        'family': row[3],
                        'genus': row[4],
                        'species': row[5],
                        'description': row[6],
                        'care_instructions': json.loads(row[7] or '{}'),
                        'climate_data': json.loads(row[8] or '{}'),
                        'sources': json.loads(row[9] or '{}'),
                        'image_urls': json.loads(row[10] or '[]'),
                        'categories': row[11].split(',') if row[11] else [],
                        'weather_data': {
                            'temperature_min': row[12],
                            'temperature_max': row[13],
                            'humidity_min': row[14],
                            'humidity_max': row[15],
                            'sunlight_hours_min': row[16],
                            'sunlight_hours_max': row[17]
                        } if row[12] is not None else {}
                    }
                    plants_data.append(plant)

                # Structure pour le web
                web_data = {
                    'metadata': {
                        'total_plants': len(plants_data),
                        'generated_at': datetime.now().isoformat(),
                        'version': '1.0'
                    },
                    'categories': self._get_categories_summary(),
                    'plants': plants_data
                }

                # Sauvegarde en JSON
                with open('plants_data.json', 'w', encoding='utf-8') as f:
                    json.dump(web_data, f, indent=2, ensure_ascii=False)

                print(f"✅ Fichier plants_data.json généré avec {len(plants_data)} plantes")
                return 'plants_data.json'

        except Exception as e:
            print(f"❌ Erreur génération JSON: {e}")
            return None

    def _get_categories_summary(self) -> Dict[str, Any]:
        """Génère un résumé des catégories pour la navigation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Compte par catégorie principale
                cursor.execute('''
                    SELECT
                        CASE
                            WHEN pc.category LIKE '%fleur%' THEN 'fleurs'
                            WHEN pc.category LIKE '%arbre%' THEN 'arbres'
                            WHEN pc.category LIKE '%legume%' THEN 'legumes'
                            WHEN pc.category LIKE '%fruit%' THEN 'fruits'
                            WHEN pc.category LIKE '%aromate%' THEN 'aromates'
                            ELSE pc.category
                        END as main_category,
                        COUNT(DISTINCT p.id) as count
                    FROM plants p
                    JOIN plant_categories pc ON p.id = pc.plant_id
                    WHERE p.scientific_name != 'Test Plant'
                    GROUP BY main_category
                    ORDER BY count DESC
                ''')

                categories = {}
                for row in cursor.fetchall():
                    categories[row[0]] = row[1]

                return categories

        except Exception as e:
            print(f"❌ Erreur résumé catégories: {e}")
            return {}

    def generate_category_data(self) -> Dict[str, List[Dict]]:
        """Génère les données organisées par catégories pour l'interface"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                categories_data = {
                    'fleurs': [],
                    'arbres': [],
                    'legumes': [],
                    'fruits': [],
                    'aromates': []
                }

                # Récupère les plantes par catégorie
                for category in categories_data.keys():
                    cursor.execute('''
                        SELECT
                            p.id, p.scientific_name,
                            json_extract(p.common_names, '$[0]') as common_name,
                            p.family, p.description,
                            p.care_instructions, p.image_urls
                        FROM plants p
                        JOIN plant_categories pc ON p.id = pc.plant_id
                        WHERE pc.category LIKE ?
                        AND p.scientific_name != 'Test Plant'
                        ORDER BY p.scientific_name
                        LIMIT 50  -- Limite pour performance
                    ''', (f'%{category}%',))

                    for row in cursor.fetchall():
                        plant = {
                            'id': row[0],
                            'scientific_name': row[1],
                            'common_name': row[2] or row[1].split()[0],
                            'family': row[3],
                            'description': row[4][:200] + '...' if row[4] and len(row[4]) > 200 else row[4],
                            'care_instructions': json.loads(row[5] or '{}'),
                            'image_urls': json.loads(row[6] or '[]')
                        }
                        categories_data[category].append(plant)

                # Sauvegarde par catégories
                with open('plants_by_category.json', 'w', encoding='utf-8') as f:
                    json.dump(categories_data, f, indent=2, ensure_ascii=False)

                print("✅ Fichier plants_by_category.json généré")
                return categories_data

        except Exception as e:
            print(f"❌ Erreur génération catégories: {e}")
            return {}

    def generate_search_index(self) -> Dict[str, List[int]]:
        """Génère un index de recherche pour performance"""
        try:
            search_index = {
                'scientific_names': {},
                'common_names': {},
                'families': {},
                'categories': {}
            }

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Index noms scientifiques
                cursor.execute('''
                    SELECT id, scientific_name FROM plants
                    WHERE scientific_name != 'Test Plant'
                ''')
                for row in cursor.fetchall():
                    name = row[1].lower()
                    if name not in search_index['scientific_names']:
                        search_index['scientific_names'][name] = []
                    search_index['scientific_names'][name].append(row[0])

                # Index noms communs
                cursor.execute('''
                    SELECT p.id, json_extract(p.common_names, '$[' || json_each.key || ']') as common_name
                    FROM plants p, json_each(p.common_names)
                    WHERE p.scientific_name != 'Test Plant'
                ''')
                for row in cursor.fetchall():
                    if row[1]:
                        name = row[1].lower()
                        if name not in search_index['common_names']:
                            search_index['common_names'][name] = []
                        search_index['common_names'][name].append(row[0])

                # Index familles
                cursor.execute('''
                    SELECT id, family FROM plants
                    WHERE family IS NOT NULL AND scientific_name != 'Test Plant'
                ''')
                for row in cursor.fetchall():
                    family = row[1].lower()
                    if family not in search_index['families']:
                        search_index['families'][family] = []
                    search_index['families'][family].append(row[0])

                # Index catégories
                cursor.execute('''
                    SELECT p.id, pc.category FROM plants p
                    JOIN plant_categories pc ON p.id = pc.plant_id
                    WHERE p.scientific_name != 'Test Plant'
                ''')
                for row in cursor.fetchall():
                    category = row[1].lower()
                    if category not in search_index['categories']:
                        search_index['categories'][category] = []
                    search_index['categories'][category].append(row[0])

                # Sauvegarde l'index
                with open('plants_search_index.json', 'w', encoding='utf-8') as f:
                    json.dump(search_index, f, indent=2, ensure_ascii=False)

                print("✅ Index de recherche généré")
                return search_index

        except Exception as e:
            print(f"❌ Erreur génération index: {e}")
            return {}

def main():
    """Fonction principale"""
    print("🚀 Génération des données web pour les plantes...")

    interface = PlantsWebInterface()

    # Génère les fichiers de données
    try:
        print("\n1. Génération du fichier principal...")
        interface.generate_plants_json()

        print("\n2. Génération des données par catégories...")
        interface.generate_category_data()

        print("\n3. Génération de l'index de recherche...")
        interface.generate_search_index()

        print("\n✅ Tous les fichiers générés avec succès!")
        print("📁 Fichiers créés:")
        print("   - plants_data.json (données complètes)")
        print("   - plants_by_category.json (données par catégories)")
        print("   - plants_search_index.json (index de recherche)")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
