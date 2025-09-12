import sqlite3
import json
import requests
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Any

class PlantsDatabase:
    """Base de données SQLite pour stocker les données de plantes depuis plusieurs APIs gratuites"""

    def __init__(self, db_path: str = 'plants_comprehensive.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialise la structure de la base de données"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Table principale des plantes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scientific_name TEXT UNIQUE NOT NULL,
                    common_names TEXT, -- JSON array
                    family TEXT,
                    genus TEXT,
                    species TEXT,
                    description TEXT,
                    care_instructions TEXT, -- JSON
                    climate_data TEXT, -- JSON
                    sources TEXT, -- JSON tracking des sources
                    image_urls TEXT, -- JSON array
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Table des catégories
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plant_categories (
                    plant_id INTEGER,
                    category TEXT, -- fleurs, arbres, legumes, fruits, aromates, etc.
                    subcategory TEXT, -- sous-catégorie
                    FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE,
                    UNIQUE(plant_id, category, subcategory)
                )
            ''')

            # Table des données météo associées
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plant_weather_data (
                    plant_id INTEGER,
                    temperature_min REAL,
                    temperature_max REAL,
                    humidity_min REAL,
                    humidity_max REAL,
                    sunlight_hours_min INTEGER,
                    sunlight_hours_max INTEGER,
                    rainfall_min REAL,
                    rainfall_max REAL,
                    hardiness_zone_min TEXT,
                    hardiness_zone_max TEXT,
                    FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
                )
            ''')

            # Table de cache pour les APIs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_cache (
                    cache_key TEXT PRIMARY KEY,
                    data TEXT,
                    source TEXT,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Index pour les performances
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scientific_name ON plants(scientific_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_common_names ON plants(common_names)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_family ON plants(family)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON plant_categories(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_key ON api_cache(cache_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires ON api_cache(expires_at)')

            conn.commit()

    def save_plant(self, plant_data: Dict[str, Any]) -> int:
        """Sauvegarde une plante dans la base de données"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insertion/MAJ de la plante
            cursor.execute('''
                INSERT OR REPLACE INTO plants
                (scientific_name, common_names, family, genus, species,
                 description, care_instructions, climate_data, sources, image_urls, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plant_data.get('scientific_name'),
                json.dumps(plant_data.get('common_names', [])),
                plant_data.get('family'),
                plant_data.get('genus'),
                plant_data.get('species'),
                plant_data.get('description'),
                json.dumps(plant_data.get('care_instructions', {})),
                json.dumps(plant_data.get('climate_data', {})),
                json.dumps(plant_data.get('sources', {})),
                json.dumps(plant_data.get('image_urls', [])),
                datetime.now().isoformat()
            ))

            plant_id = cursor.lastrowid

            # Sauvegarde des catégories
            if 'categories' in plant_data:
                for category_data in plant_data['categories']:
                    cursor.execute('''
                        INSERT OR IGNORE INTO plant_categories
                        (plant_id, category, subcategory)
                        VALUES (?, ?, ?)
                    ''', (
                        plant_id,
                        category_data.get('category'),
                        category_data.get('subcategory')
                    ))

            # Sauvegarde des données météo
            if 'weather_data' in plant_data:
                weather = plant_data['weather_data']
                cursor.execute('''
                    INSERT OR REPLACE INTO plant_weather_data
                    (plant_id, temperature_min, temperature_max, humidity_min, humidity_max,
                     sunlight_hours_min, sunlight_hours_max, rainfall_min, rainfall_max,
                     hardiness_zone_min, hardiness_zone_max)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    plant_id,
                    weather.get('temperature_min'),
                    weather.get('temperature_max'),
                    weather.get('humidity_min'),
                    weather.get('humidity_max'),
                    weather.get('sunlight_hours_min'),
                    weather.get('sunlight_hours_max'),
                    weather.get('rainfall_min'),
                    weather.get('rainfall_max'),
                    weather.get('hardiness_zone_min'),
                    weather.get('hardiness_zone_max')
                ))

            conn.commit()
            return plant_id

    def get_plant(self, scientific_name: str) -> Optional[Dict[str, Any]]:
        """Récupère une plante par son nom scientifique"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT p.*, GROUP_CONCAT(pc.category || ':' || COALESCE(pc.subcategory, '')) as categories,
                       pwd.*
                FROM plants p
                LEFT JOIN plant_categories pc ON p.id = pc.plant_id
                LEFT JOIN plant_weather_data pwd ON p.id = pwd.plant_id
                WHERE p.scientific_name = ?
                GROUP BY p.id
            ''', (scientific_name,))

            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None

    def search_plants(self, query: str, category: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Recherche des plantes par nom ou catégorie"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            sql = '''
                SELECT p.*, GROUP_CONCAT(pc.category || ':' || COALESCE(pc.subcategory, '')) as categories
                FROM plants p
                LEFT JOIN plant_categories pc ON p.id = pc.plant_id
                WHERE (p.scientific_name LIKE ? OR
                       p.common_names LIKE ? OR
                       p.description LIKE ?)
            '''
            params = [f'%{query}%', f'%{query}%', f'%{query}%']

            if category:
                sql += ' AND pc.category = ?'
                params.append(category)

            sql += ' GROUP BY p.id LIMIT ?'
            params.append(limit)

            cursor.execute(sql, params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_plants_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les plantes d'une catégorie spécifique"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT p.*, GROUP_CONCAT(pc.category || ':' || COALESCE(pc.subcategory, '')) as categories
                FROM plants p
                JOIN plant_categories pc ON p.id = pc.plant_id
                WHERE pc.category = ?
                GROUP BY p.id
                LIMIT ?
            ''', (category, limit))

            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convertit une ligne de base de données en dictionnaire"""
        return {
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
            'last_updated': row[11],
            'created_at': row[12],
            'categories': row[13].split(',') if row[13] else []
        }

    def get_stats(self) -> Dict[str, int]:
        """Retourne les statistiques de la base de données"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            stats = {}

            # Nombre total de plantes
            cursor.execute('SELECT COUNT(*) FROM plants')
            stats['total_plants'] = cursor.fetchone()[0]

            # Nombre par catégorie
            cursor.execute('''
                SELECT category, COUNT(DISTINCT plant_id)
                FROM plant_categories
                GROUP BY category
            ''')

            for row in cursor.fetchall():
                stats[f'category_{row[0]}'] = row[1]

            # Nombre de plantes avec données météo
            cursor.execute('SELECT COUNT(*) FROM plant_weather_data')
            stats['plants_with_weather_data'] = cursor.fetchone()[0]

            return stats

    def cleanup_old_cache(self):
        """Nettoie le cache expiré"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM api_cache WHERE expires_at < ?', (datetime.now().isoformat(),))
            conn.commit()

# Instance globale de la base de données
plants_db = PlantsDatabase()
