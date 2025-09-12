import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from urllib.parse import quote
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlantDataCollector:
    """Collecteur de données depuis plusieurs APIs gratuites"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PlantDataCollector/1.0 (Educational Project)'
        })

        # Cache pour éviter les requêtes répétées
        self.cache = {}
        self.cache_duration = timedelta(hours=24)

    def collect_comprehensive_plant_data(self, plant_name: str) -> Dict[str, Any]:
        """
        Collecte des données complètes sur une plante depuis toutes les sources disponibles
        """
        logger.info(f"Collecting data for: {plant_name}")

        combined_data = {
            'scientific_name': plant_name,
            'common_names': [],
            'sources': {},
            'categories': [],
            'care_instructions': {},
            'climate_data': {},
            'description': '',
            'image_urls': [],
            'weather_data': {}
        }

        # 1. Collecte depuis Trefle API (USDA)
        try:
            trefle_data = self._get_trefle_data(plant_name)
            if trefle_data:
                combined_data = self._merge_trefle_data(combined_data, trefle_data)
                logger.info(f"Trefle data collected for {plant_name}")
        except Exception as e:
            logger.warning(f"Trefle API error for {plant_name}: {e}")

        # 2. Collecte depuis Wikipedia
        try:
            wiki_data = self._get_wikipedia_data(plant_name)
            if wiki_data:
                combined_data = self._merge_wikipedia_data(combined_data, wiki_data)
                logger.info(f"Wikipedia data collected for {plant_name}")
        except Exception as e:
            logger.warning(f"Wikipedia API error for {plant_name}: {e}")

        # 3. Collecte depuis PlantNet
        try:
            plantnet_data = self._get_plantnet_data(plant_name)
            if plantnet_data:
                combined_data = self._merge_plantnet_data(combined_data, plantnet_data)
                logger.info(f"PlantNet data collected for {plant_name}")
        except Exception as e:
            logger.warning(f"PlantNet API error for {plant_name}: {e}")

        # 4. Collecte depuis OpenPlantBook
        try:
            opb_data = self._get_openplantbook_data(plant_name)
            if opb_data:
                combined_data = self._merge_openplantbook_data(combined_data, opb_data)
                logger.info(f"OpenPlantBook data collected for {plant_name}")
        except Exception as e:
            logger.warning(f"OpenPlantBook API error for {plant_name}: {e}")

        # Nettoyage et validation des données
        combined_data = self._clean_and_validate_data(combined_data)

        return combined_data

    def _get_trefle_data(self, plant_name: str) -> Optional[Dict[str, Any]]:
        """Collecte depuis Trefle API (USDA) - GRATUIT"""
        # Note: Trefle API nécessite une clé gratuite
        # Pour cet exemple, on simule avec des données de test
        # En production, il faudrait s'inscrire sur https://trefle.io/

        # Simulation de données Trefle
        mock_trefle_data = {
            'scientific_name': plant_name,
            'common_name': self._generate_common_name(plant_name),
            'family': self._extract_family_from_name(plant_name),
            'genus': plant_name.split()[0] if len(plant_name.split()) > 1 else plant_name,
            'year': 2024,
            'bibliography': 'USDA Plants Database',
            'author': 'USDA',
            'status': 'accepted',
            'rank': 'species'
        }

        return mock_trefle_data

    def _get_wikipedia_data(self, plant_name: str) -> Optional[Dict[str, Any]]:
        """Collecte depuis Wikipedia API - GRATUIT"""
        try:
            # Recherche du nom scientifique sur Wikipedia
            search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(plant_name.replace(' ', '_'))}"

            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'extract' in data and len(data['extract']) > 50:
                return {
                    'title': data.get('title', ''),
                    'description': data.get('extract', ''),
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    'thumbnail': data.get('thumbnail', {}).get('source', ''),
                    'coordinates': data.get('coordinates', {})
                }

        except requests.exceptions.RequestException as e:
            logger.warning(f"Wikipedia request failed: {e}")

        return None

    def _get_plantnet_data(self, plant_name: str) -> Optional[Dict[str, Any]]:
        """Collecte depuis PlantNet API - GRATUIT"""
        try:
            # PlantNet API pour identification et données
            # Simulation avec données de test
            mock_plantnet_data = {
                'species': plant_name,
                'family': self._extract_family_from_name(plant_name),
                'common_names': [self._generate_common_name(plant_name)],
                'images': [],
                'description': f"Plante {plant_name} - Données PlantNet",
                'distribution': 'Europe, Amérique du Nord',
                'habitat': 'Jardins, parcs, milieux naturels'
            }

            return mock_plantnet_data

        except Exception as e:
            logger.warning(f"PlantNet data collection failed: {e}")
            return None

    def _get_openplantbook_data(self, plant_name: str) -> Optional[Dict[str, Any]]:
        """Collecte depuis OpenPlantBook API - GRATUIT"""
        try:
            # OpenPlantBook fournit des données techniques d'entretien
            # Simulation avec données de test
            mock_opb_data = {
                'pid': plant_name.lower().replace(' ', '_'),
                'display_pid': plant_name,
                'alias': self._generate_common_name(plant_name),
                'temperature_min': 10,
                'temperature_max': 30,
                'humidity_min': 40,
                'humidity_max': 70,
                'light_min': 300,
                'light_max': 1000,
                'ph_min': 6.0,
                'ph_max': 7.5,
                'difficulty': 'medium',
                'watering_frequency': 'weekly'
            }

            return mock_opb_data

        except Exception as e:
            logger.warning(f"OpenPlantBook data collection failed: {e}")
            return None

    def _merge_trefle_data(self, combined_data: Dict, trefle_data: Dict) -> Dict:
        """Fusionne les données de Trefle"""
        combined_data['scientific_name'] = trefle_data.get('scientific_name', combined_data['scientific_name'])
        combined_data['family'] = trefle_data.get('family', combined_data.get('family', ''))
        combined_data['genus'] = trefle_data.get('genus', combined_data.get('genus', ''))

        if trefle_data.get('common_name'):
            if trefle_data['common_name'] not in combined_data['common_names']:
                combined_data['common_names'].append(trefle_data['common_name'])

        combined_data['sources']['trefle'] = {
            'bibliography': trefle_data.get('bibliography', ''),
            'author': trefle_data.get('author', ''),
            'collected_at': datetime.now().isoformat()
        }

        return combined_data

    def _merge_wikipedia_data(self, combined_data: Dict, wiki_data: Dict) -> Dict:
        """Fusionne les données de Wikipedia"""
        if not combined_data['description'] and wiki_data.get('description'):
            combined_data['description'] = wiki_data['description']

        if wiki_data.get('thumbnail'):
            combined_data['image_urls'].append(wiki_data['thumbnail'])

        combined_data['sources']['wikipedia'] = {
            'title': wiki_data.get('title', ''),
            'url': wiki_data.get('url', ''),
            'collected_at': datetime.now().isoformat()
        }

        return combined_data

    def _merge_plantnet_data(self, combined_data: Dict, plantnet_data: Dict) -> Dict:
        """Fusionne les données de PlantNet"""
        for name in plantnet_data.get('common_names', []):
            if name not in combined_data['common_names']:
                combined_data['common_names'].append(name)

        if not combined_data['description'] and plantnet_data.get('description'):
            combined_data['description'] = plantnet_data['description']

        combined_data['sources']['plantnet'] = {
            'family': plantnet_data.get('family', ''),
            'distribution': plantnet_data.get('distribution', ''),
            'habitat': plantnet_data.get('habitat', ''),
            'collected_at': datetime.now().isoformat()
        }

        return combined_data

    def _merge_openplantbook_data(self, combined_data: Dict, opb_data: Dict) -> Dict:
        """Fusionne les données d'OpenPlantBook"""
        combined_data['care_instructions'] = {
            'watering_frequency': opb_data.get('watering_frequency', ''),
            'difficulty': opb_data.get('difficulty', ''),
            'ph_range': f"{opb_data.get('ph_min', '')}-{opb_data.get('ph_max', '')}"
        }

        combined_data['weather_data'] = {
            'temperature_min': opb_data.get('temperature_min'),
            'temperature_max': opb_data.get('temperature_max'),
            'humidity_min': opb_data.get('humidity_min'),
            'humidity_max': opb_data.get('humidity_max'),
            'sunlight_hours_min': opb_data.get('light_min'),
            'sunlight_hours_max': opb_data.get('light_max')
        }

        combined_data['sources']['openplantbook'] = {
            'pid': opb_data.get('pid', ''),
            'collected_at': datetime.now().isoformat()
        }

        return combined_data

    def _clean_and_validate_data(self, data: Dict) -> Dict:
        """Nettoie et valide les données collectées"""
        # Suppression des valeurs vides
        data['common_names'] = [name for name in data['common_names'] if name and name.strip()]

        # Validation du nom scientifique
        if not data['scientific_name']:
            logger.warning("No scientific name found")
            return None

        # Ajout de catégories automatiques basées sur le nom
        data['categories'] = self._categorize_plant(data['scientific_name'])

        # Nettoyage de la description
        if data['description']:
            data['description'] = re.sub(r'<[^>]+>', '', data['description'])  # Remove HTML tags
            data['description'] = data['description'][:1000]  # Limit length

        return data

    def _categorize_plant(self, scientific_name: str) -> List[Dict[str, str]]:
        """Catégorise automatiquement une plante"""
        categories = []
        name_lower = scientific_name.lower()

        # Détection basée sur des mots-clés
        if any(word in name_lower for word in ['rosa', 'tulipa', 'lilium', 'iris', 'daisy']):
            categories.append({'category': 'fleurs', 'subcategory': 'fleurs à bulbe'})

        if any(word in name_lower for word in ['quercus', 'fagus', 'acer', 'betula']):
            categories.append({'category': 'arbres', 'subcategory': 'feuillus'})

        if any(word in name_lower for word in ['pinus', 'abies', 'picea']):
            categories.append({'category': 'arbres', 'subcategory': 'conifères'})

        if any(word in name_lower for word in ['solanum', 'lycopersicum']):
            categories.append({'category': 'fruits', 'subcategory': 'légumes-fruits'})

        if any(word in name_lower for word in ['daucus', 'carota']):
            categories.append({'category': 'legumes', 'subcategory': 'racines'})

        if any(word in name_lower for word in ['mentha', 'rosmarinus', 'thymus']):
            categories.append({'category': 'aromates', 'subcategory': 'fines herbes'})

        # Catégorie par défaut si aucune détection
        if not categories:
            categories.append({'category': 'divers', 'subcategory': 'autres'})

        return categories

    def _generate_common_name(self, scientific_name: str) -> str:
        """Génère un nom commun basé sur le nom scientifique"""
        genus = scientific_name.split()[0] if len(scientific_name.split()) > 1 else scientific_name

        common_names = {
            'rosa': 'Rose',
            'tulipa': 'Tulipe',
            'lilium': 'Lys',
            'iris': 'Iris',
            'quercus': 'Chêne',
            'acer': 'Érable',
            'pinus': 'Pin',
            'solanum': 'Tomate',
            'daucus': 'Carotte',
            'mentha': 'Menthe',
            'rosmarinus': 'Romarin',
            'thymus': 'Thym'
        }

        return common_names.get(genus.lower(), f"{genus} (nom commun inconnu)")

    def _extract_family_from_name(self, scientific_name: str) -> str:
        """Extrait la famille botanique du nom scientifique"""
        genus = scientific_name.split()[0] if len(scientific_name.split()) > 1 else scientific_name

        # Dictionnaire simplifié des familles
        family_map = {
            'rosa': 'Rosaceae',
            'tulipa': 'Liliaceae',
            'lilium': 'Liliaceae',
            'iris': 'Iridaceae',
            'quercus': 'Fagaceae',
            'acer': 'Sapindaceae',
            'pinus': 'Pinaceae',
            'solanum': 'Solanaceae',
            'daucus': 'Apiaceae',
            'mentha': 'Lamiaceae',
            'rosmarinus': 'Lamiaceae',
            'thymus': 'Lamiaceae'
        }

        return family_map.get(genus.lower(), 'Famille inconnue')

# Fonction principale pour tester le collecteur
if __name__ == "__main__":
    collector = PlantDataCollector()

    # Test avec quelques plantes
    test_plants = [
        "Rosa rugosa",
        "Tulipa gesneriana",
        "Quercus robur",
        "Solanum lycopersicum",
        "Mentha piperita"
    ]

    for plant in test_plants:
        try:
            data = collector.collect_comprehensive_plant_data(plant)
            print(f"\n=== Données collectées pour {plant} ===")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            time.sleep(1)  # Respect des limites API
        except Exception as e:
            logger.error(f"Erreur lors de la collecte pour {plant}: {e}")
