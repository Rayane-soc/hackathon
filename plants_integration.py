#!/usr/bin/env python3
"""
Script d'intégration complet pour la base de données de plantes
Combine la collecte de données et la sauvegarde en base
"""

import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from plants_database import plants_db
from plants_data_collector import PlantDataCollector

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('plants_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PlantsIntegrationSystem:
    """Système complet d'intégration des données de plantes"""

    def __init__(self):
        self.collector = PlantDataCollector()
        self.stats = {
            'total_processed': 0,
            'successful_collects': 0,
            'failed_collects': 0,
            'saved_to_db': 0,
            'errors': []
        }

    def process_plant_list(self, plant_list: List[str], batch_size: int = 10) -> Dict[str, Any]:
        """
        Traite une liste de plantes par lots
        """
        logger.info(f"Starting to process {len(plant_list)} plants")

        for i in range(0, len(plant_list), batch_size):
            batch = plant_list[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} plants")

            for plant_name in batch:
                try:
                    self._process_single_plant(plant_name)
                    time.sleep(1)  # Respect des limites API
                except Exception as e:
                    logger.error(f"Failed to process {plant_name}: {e}")
                    self.stats['errors'].append({
                        'plant': plant_name,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    self.stats['failed_collects'] += 1

            # Pause entre les lots
            if i + batch_size < len(plant_list):
                logger.info("Waiting 5 seconds before next batch...")
                time.sleep(5)

        return self.stats

    def _process_single_plant(self, plant_name: str) -> bool:
        """
        Traite une seule plante : collecte + sauvegarde
        """
        self.stats['total_processed'] += 1
        logger.info(f"Processing: {plant_name}")

        try:
            # 1. Collecte des données
            plant_data = self.collector.collect_comprehensive_plant_data(plant_name)

            if not plant_data:
                logger.warning(f"No data collected for {plant_name}")
                return False

            self.stats['successful_collects'] += 1

            # 2. Sauvegarde en base
            plant_id = plants_db.save_plant(plant_data)

            if plant_id:
                self.stats['saved_to_db'] += 1
                logger.info(f"Successfully saved {plant_name} (ID: {plant_id})")
                return True
            else:
                logger.error(f"Failed to save {plant_name} to database")
                return False

        except Exception as e:
            logger.error(f"Error processing {plant_name}: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la base de données"""
        db_stats = plants_db.get_stats()
        db_stats.update(self.stats)
        return db_stats

    def export_sample_data(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Exporte un échantillon de données pour vérification"""
        sample_plants = []

        # Récupère des plantes de différentes catégories
        categories = ['fleurs', 'arbres', 'legumes', 'fruits', 'aromates']

        for category in categories:
            try:
                plants = plants_db.get_plants_by_category(category, limit=2)
                sample_plants.extend(plants)
            except Exception as e:
                logger.warning(f"Could not get plants for category {category}: {e}")

        return sample_plants[:limit]

def create_initial_plant_list() -> List[str]:
    """
    Crée une liste initiale de plantes représentatives
    """
    plants = []

    # Fleurs
    flowers = [
        "Rosa rugosa", "Rosa damascena", "Rosa gallica", "Rosa centifolia",
        "Tulipa gesneriana", "Tulipa clusiana", "Tulipa tarda",
        "Lilium candidum", "Lilium longiflorum", "Lilium japonicum",
        "Iris germanica", "Iris sibirica", "Iris pseudacorus",
        "Dianthus caryophyllus", "Dianthus barbatus",
        "Viola tricolor", "Viola odorata"
    ]
    plants.extend(flowers)

    # Arbres
    trees = [
        "Quercus robur", "Quercus petraea", "Quercus ilex",
        "Acer saccharum", "Acer palmatum", "Acer pseudoplatanus",
        "Betula pendula", "Betula pubescens",
        "Fagus sylvatica", "Fagus grandifolia",
        "Pinus sylvestris", "Pinus nigra", "Pinus halepensis",
        "Abies alba", "Abies nordmanniana",
        "Picea abies", "Picea pungens"
    ]
    plants.extend(trees)

    # Légumes
    vegetables = [
        "Solanum lycopersicum", "Solanum melongena", "Solanum tuberosum",
        "Daucus carota", "Daucus carota subsp. sativus",
        "Allium cepa", "Allium sativum", "Allium porrum",
        "Lactuca sativa", "Lactuca serriola",
        "Spinacia oleracea", "Beta vulgaris",
        "Brassica oleracea", "Brassica napus", "Brassica rapa",
        "Cucumis sativus", "Cucumis melo",
        "Cucurbita pepo", "Cucurbita maxima"
    ]
    plants.extend(vegetables)

    # Fruits
    fruits = [
        "Malus domestica", "Malus sylvestris",
        "Pyrus communis", "Pyrus pyrifolia",
        "Prunus domestica", "Prunus persica", "Prunus avium",
        "Vitis vinifera", "Vitis labrusca",
        "Citrus limon", "Citrus sinensis", "Citrus reticulata",
        "Fragaria × ananassa",
        "Rubus idaeus", "Rubus fruticosus"
    ]
    plants.extend(fruits)

    # Aromates
    herbs = [
        "Mentha piperita", "Mentha spicata", "Mentha × piperita",
        "Rosmarinus officinalis",
        "Thymus vulgaris", "Thymus serpyllum",
        "Ocimum basilicum", "Ocimum tenuiflorum",
        "Petroselinum crispum",
        "Coriandrum sativum",
        "Salvia officinalis", "Salvia sclarea",
        "Origanum vulgare", "Origanum majorana"
    ]
    plants.extend(herbs)

    return plants

def main():
    """Fonction principale"""
    logger.info("Starting Plants Integration System")

    # Initialisation du système
    integration = PlantsIntegrationSystem()

    # Création de la liste de plantes
    plant_list = create_initial_plant_list()
    logger.info(f"Created plant list with {len(plant_list)} plants")

    # Traitement par lots
    try:
        stats = integration.process_plant_list(plant_list, batch_size=5)

        # Affichage des statistiques
        logger.info("=== TRAITEMENT TERMINÉ ===")
        logger.info(f"Total traité: {stats['total_processed']}")
        logger.info(f"Collectes réussies: {stats['successful_collects']}")
        logger.info(f"Sauvegardé en base: {stats['saved_to_db']}")
        logger.info(f"Échecs: {stats['failed_collects']}")

        # Statistiques de la base
        db_stats = integration.get_database_stats()
        logger.info("=== STATISTIQUES BASE DE DONNÉES ===")
        for key, value in db_stats.items():
            if not key.startswith('errors'):
                logger.info(f"{key}: {value}")

        # Export d'un échantillon
        sample_data = integration.export_sample_data(5)
        logger.info("=== ÉCHANTILLON DE DONNÉES ===")
        for plant in sample_data:
            logger.info(f"- {plant.get('scientific_name', 'Unknown')} ({plant.get('common_names', [''])[0]})")

        # Sauvegarde des erreurs
        if stats['errors']:
            with open('collection_errors.json', 'w', encoding='utf-8') as f:
                json.dump(stats['errors'], f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(stats['errors'])} errors to collection_errors.json")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
