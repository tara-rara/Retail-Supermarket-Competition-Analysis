import json
import logging
import os
import re
from collections import defaultdict
import uuid
from datetime import datetime

class ProductMatcher:
    def __init__(self, log_name="ProductMatcher"):
        self.logger = logging.getLogger(log_name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            
        try:
            from rapidfuzz import fuzz
            self.fuzz = fuzz
        except ImportError:
            self.logger.warning("rapidfuzz not found. Using fallback matching (slower).")
            self.fuzz = None

    def clean_text(self, text):
        """Preprocess titles for better matching."""
        if not text:
            return ""
        # Lowercase, remove special characters, remove common unit text
        text = text.lower()
        # Remove common units/noise since we have them in metadata
        text = re.sub(r'\d+(\.\d+)?\s*(kg|g|gm|ml|l|liter|dozen|pcs|pieces)', '', text)
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        # Collapse whitespace
        text = " ".join(text.split())
        return text

    def get_similarity(self, s1, s2):
        """Calculate string similarity."""
        if self.fuzz:
            # token_sort_ratio is robust against word reordering (e.g., "Coke 1.5L" vs "1.5L Coke")
            return self.fuzz.token_sort_ratio(s1, s2)
        else:
            # Fallback simple Jaccard
            tokens1 = set(s1.split())
            tokens2 = set(s2.split())
            if not tokens1 or not tokens2:
                return 0.0
            intersection = tokens1.intersection(tokens2)
            union = tokens1.union(tokens2)
            return (len(intersection) / len(union)) * 100.0

    def resolve_entities(self, processed_data_list, threshold=85):
        """
        Groups identical products together.
        Input: Flat list of processed items.
        Output: List of unified products.
        """
        # Step 1: Blocking by Category, Quantity and Unit (Brand is unreliable)
        blocks = defaultdict(list)
        for item in processed_data_list:
            cat = item.get('category', 'Unknown').lower()
            qty = item.get('quantity', 1.0)
            unit = item.get('unit', 'unit').lower()
            block_key = f"{cat}|{qty}|{unit}"
            blocks[block_key].append(item)

        self.logger.info(f"Formed {len(blocks)} blocks for matching.")
        
        gold_layer = []
        
        for block_key, items in blocks.items():
            if not items:
                continue
            
            # Sub-grouping within blocks using fuzzy matching
            clusters = [] # Each cluster is a list of items representing the same product
            
            for item in items:
                matches_existing = False
                name = item.get('name', item.get('title', ''))
                cleaned_name = self.clean_text(name)
                
                for cluster in clusters:
                    rep = cluster[0]
                    rep_name = rep.get('name', rep.get('title', ''))
                    similarity = self.get_similarity(cleaned_name, self.clean_text(rep_name))
                    
                    if similarity >= threshold:
                        cluster.append(item)
                        matches_existing = True
                        break
                
                if not matches_existing:
                    clusters.append([item])
            
            # Create a unified product for each cluster
            for cluster in clusters:
                # Use the shortest name as the canonical one
                canonical_item = min(cluster, key=lambda x: len(x.get('name', x.get('title', ''))))
                
                unified_id = str(uuid.uuid4())
                
                # Combine store-level details
                store_prices = []
                for entry in cluster:
                    store_prices.append({
                        "store": entry.get('store', ''),
                        "city": entry.get('city', ''),
                        "price": entry.get('price', 0),
                        "unit_price": entry.get('unit_price', 0),
                        "timestamp": entry.get('scrape_timestamp', entry.get('timestamp', ''))
                    })
                
                # Deduplicate store entries
                best_store_prices = {}
                for sp in store_prices:
                    key = (sp['store'], sp['city'])
                    if key not in best_store_prices or sp['price'] < best_store_prices[key]['price']:
                        best_store_prices[key] = sp
                
                gold_product = {
                    "product_id": unified_id,
                    "title": canonical_item.get('name', canonical_item.get('title', '')),
                    "brand": canonical_item.get('brand', 'Generic'),
                    "quantity": canonical_item.get('quantity', 1.0),
                    "unit": canonical_item.get('unit', 'unit'),
                    "category": canonical_item.get('category', 'Unknown'),
                    "offers": list(best_store_prices.values()),
                    "min_price": min(sp['price'] for sp in best_store_prices.values()) if best_store_prices else 0,
                    "max_price": max(sp['price'] for sp in best_store_prices.values()) if best_store_prices else 0,
                    "match_count": len(best_store_prices),
                    "cluster_size": len(cluster),
                    "processed_at": datetime.now().isoformat()
                }
                gold_layer.append(gold_product)
                
        self.logger.info(f"Entity Resolution complete. Unified {len(processed_data_list)} raw entries into {len(gold_layer)} unique products.")
        return gold_layer
