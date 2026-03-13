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
    matched_dir = "data/matched"
    
    if not os.path.exists(processed_dir):
        logger.error(f"Processed data directory {processed_dir} not found.")
        return
    
    import csv
    logger.info("Loading processed items from CSV...")
    all_processed_items = []
    
    for filename in os.listdir(processed_dir):
        if filename.endswith("_cleaned.csv"):
            filepath = os.path.join(processed_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert numeric fields
                    for key in ['price', 'quantity', 'unit_price']:
                        if row.get(key):
                            try: row[key] = float(row[key])
                            except: pass
                    all_processed_items.append(row)

    logger.info(f"Loaded {len(all_processed_items)} items from {processed_dir}.")
    
    matcher = ProductMatcher()
    gold_layer = matcher.resolve_entities(all_processed_items, threshold=85)
    
    # Save the consolidated Matched Layer
    os.makedirs(matched_dir, exist_ok=True)
    output_path_json = os.path.join(matched_dir, "matched_products.json")
    output_path_csv = os.path.join(matched_dir, "matched_products.csv")
    
    with open(output_path_json, 'w', encoding='utf-8') as f:
        json.dump(gold_layer, f, indent=2)
    
    # Save as JSONL for Streamlit app
    output_path_jsonl = os.path.join(matched_dir, "matched_products.jsonl")
    with open(output_path_jsonl, 'w', encoding='utf-8') as f:
        for item in gold_layer:
            f.write(json.dumps(item) + "\n")
            
    # Also save a CSV for analysis
    if gold_layer:
        # Flatten for CSV (top level stats + offers summary)
        flattened = []
        for p in gold_layer:
            flattened.append({
                "product_id": p['product_id'],
                "title": p['title'],
                "brand": p['brand'],
                "quantity": p['quantity'],
                "unit": p['unit'],
                "category": p['category'],
                "min_price": p['min_price'],
                "max_price": p['max_price'],
                "match_count": p['match_count']
            })
        
        with open(output_path_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=flattened[0].keys())
            writer.writeheader()
            writer.writerows(flattened)

    logger.info(f"Matched Layer consolidated: {len(gold_layer)} unique products.")
    logger.info(f"Saved results to {matched_dir}.")

if __name__ == "__main__":
    main()
