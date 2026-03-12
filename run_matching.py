import json
import os
import logging
from src.matching.matcher import ProductMatcher

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/matching.log"),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger("MatchingOrchestrator")
    
    processed_dir = "data/processed"
    gold_dir = "data/gold"
    
    if not os.path.exists(processed_dir):
        logger.error(f"Processed data directory {processed_dir} not found.")
        return

    logger.info("Loading processed items...")
    all_processed_items = []
    
    for filename in os.listdir(processed_dir):
        if filename.endswith("_processed.jsonl"):
            filepath = os.path.join(processed_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        all_processed_items.append(json.loads(line))
                    except:
                        continue

    logger.info(f"Loaded {len(all_processed_items)} items from {processed_dir}.")
    
    matcher = ProductMatcher()
    gold_layer = matcher.resolve_entities(all_processed_items, threshold=85)
    
    # Save the consolidated Gold Layer
    os.makedirs(gold_dir, exist_ok=True)
    output_path = os.path.join(gold_dir, "gold_layer.jsonl")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for product in gold_layer:
            f.write(json.dumps(product) + '\n')
            
    # Statistics
    total_matches = sum(1 for p in gold_layer if len(p['offers']) > 1)
    logger.info(f"Gold Layer consolidated: {len(gold_layer)} unique products across stores.")
    logger.info(f"Found {total_matches} products available in multiple stores/locations.")
    logger.info(f"Total processing entries linked: {sum(len(p['offers']) for p in gold_layer)}")

if __name__ == "__main__":
    main()
