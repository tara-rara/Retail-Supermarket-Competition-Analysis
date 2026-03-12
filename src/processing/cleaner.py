import json
import re
import os
import logging
from datetime import datetime
import numpy as np

class DataCleaner:
    def __init__(self, log_name="DataCleaner"):
        self.logger = logging.getLogger(log_name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Regex patterns
        self.price_pattern = re.compile(r'Rs\.?\s*([\d,]+(\.\d+)?)')
        # Pattern for quantity: digits + space? + units
        self.quantity_pattern = re.compile(r'(\d+(\.\d+)?)\s*(kg|g|gm|gram|grams|ml|l|liter|liters|mg|doz|dozen|pcs|pieces|per Dozen|per Doz)', re.IGNORECASE)
        
        # Brand mapping for standardization
        self.brand_map = {
            'nestle': 'Nestle',
            'nestl\u00e9': 'Nestle',
            'knorr': 'Knorr',
            'ponam': 'Ponam',
            'sabroso': 'Sabroso',
            'sufi': 'Sufi',
            'national': 'National',
            'shangrila': 'Shangrila',
            'meezan': 'Meezan',
            'dalda': 'Dalda',
            'habib': 'Habib',
            'tapal': 'Tapal',
            'lipton': 'Lipton',
            'lux': 'Lux',
            'safeguard': 'Safeguard',
            'lifebuoy': 'Lifebuoy',
            'surf excel': 'Surf Excel',
            'ariel': 'Ariel',
            'sunlight': 'Sunlight',
            'colgate': 'Colgate',
            'sensodyne': 'Sensodyne',
            'pepsodent': 'Pepsodent'
        }
        
        # Unit conversion to standard (kg, L, pcs)
        self.unit_map = {
            'kg': ('kg', 1.0),
            'g': ('kg', 0.001),
            'gm': ('kg', 0.001),
            'gram': ('kg', 0.001),
            'grams': ('kg', 0.001),
            'mg': ('kg', 0.000001),
            'l': ('L', 1.0),
            'liter': ('L', 1.0),
            'liters': ('L', 1.0),
            'ml': ('L', 0.001),
            'dozen': ('pcs', 12.0),
            'doz': ('pcs', 12.0),
            'per dozen': ('pcs', 12.0),
            'per doz': ('pcs', 12.0),
            'pcs': ('pcs', 1.0),
            'pieces': ('pcs', 1.0)
        }


    def clean_price(self, price_str):
        """Extract the numeric price. If multiple, take the last one (usually the current price)."""
        if not price_str:
            return None
        matches = self.price_pattern.findall(price_str)
        if matches:
            # Take the last match which is often the discounted or current price
            last_match = matches[-1][0].replace(',', '')
            try:
                return float(last_match)
            except ValueError:
                return None
        return None

    def parse_quantity(self, title):
        """Extract quantity and unit from title."""
        if "per dozen" in title.lower() or "per doz" in title.lower():
            return 12.0, "pcs"
        
        match = self.quantity_pattern.search(title)
        if match:
            val = float(match.group(1))
            unit = match.group(3).lower()
            std_unit, multiplier = self.unit_map.get(unit, (unit, 1.0))
            return val * multiplier, std_unit
            
        return 1.0, "unit"

    def extract_brand(self, title):
        """Standardize brand naming."""
        title_lower = title.lower()
        for brand_key, brand_val in self.brand_map.items():
            if brand_key in title_lower:
                return brand_val
        # If not in map, maybe the first word is the brand
        first_word = title.split()[0] if title.split() else "Generic"
        return first_word

    def process_item(self, item):
        """Clean and normalize a single item."""
        raw_title = item.get('raw_title', '')
        raw_price = item.get('raw_price', '')
        
        price = self.clean_price(raw_price)
        if price is None:
            price = self.clean_price(raw_title)
            
        std_qty, std_unit = self.parse_quantity(raw_title)
        
        unit_price = round(price / std_qty, 2) if (price and std_qty and std_qty > 0) else None
        
        clean_title = raw_title.split('\n')[0].strip()
        brand = self.extract_brand(clean_title)
        
        processed = {
            "title": clean_title,
            "brand": brand,
            "price": price,
            "quantity": std_qty,
            "unit": std_unit,
            "unit_price": unit_price,
            "store": item.get('metadata', {}).get('store'),
            "city": item.get('metadata', {}).get('city'),
            "category": item.get('metadata', {}).get('cat'),
            "scrape_timestamp": item.get('scrape_timestamp'),
            "processed_timestamp": datetime.now().isoformat()
        }
        return processed

    def remove_output_outliers(self, processed_data):
        """
        Combined outlier detection: Z-score and IQR + Mandatory Sanity Checks.
        Handles unrealistic prices and missing value thresholds.
        """
        if not processed_data:
            return processed_data
            
        # MANDATORY: Missing value thresholds 
        # (Drop items if more than 3 critical fields are empty)
        def is_valid(item):
            missing_count = sum(1 for v in item.values() if v is None or v == "")
            return missing_count <= 3

        processed_data = [item for item in processed_data if is_valid(item)]

        # MANDATORY: Price Sanity Checks (Unit Price Bounds)
        # Filters out extreme anomalies (e.g., Rs. 0 or Rs. 1,000,000 for a liter of milk)
        def price_is_sane(item):
            up = item.get('unit_price')
            if up is None: return False
            return 1.0 < up < 50000.0 # Heuristic bounds per standard unit

        processed_data = [item for item in processed_data if price_is_sane(item)]

        if not processed_data:
            return processed_data
            
        categories = {}
        for item in processed_data:
            cat = item.get('category', 'Unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
            
        cleaned_data = []
        for cat, items in categories.items():
            prices = [item['price'] for item in items if item['price'] is not None]
            if len(prices) < 5:
                cleaned_data.extend(items)
                continue
                
            # Z-score check
            mean = np.mean(prices)
            std = np.std(prices)
            
            # IQR check
            q1 = np.percentile(prices, 25)
            q3 = np.percentile(prices, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            for item in items:
                if item['price'] is None:
                    cleaned_data.append(item)
                    continue
                
                # Use Z-score for extreme outliers
                z_score = abs((item['price'] - mean) / std) if std > 0 else 0
                
                # Use IQR for standard outliers
                is_iqr_outlier = (item['price'] < lower_bound) or (item['price'] > upper_bound)
                
                if z_score <= 4 and not is_iqr_outlier:
                    cleaned_data.append(item)
                else:
                    self.logger.warning(f"Removing outlier in {cat}: {item['title']} at {item['price']} (Z:{z_score:.2f}, IQR:{is_iqr_outlier})")
                    
        return cleaned_data


    def run_pipeline(self, input_path, output_path):
        """Process a whole .jsonl file."""
        if not os.path.exists(input_path):
            self.logger.error(f"Input file {input_path} not found.")
            return

        self.logger.info(f"Processing {input_path}...")
        raw_items = []
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    raw_items.append(json.loads(line))
                except:
                    continue
        
        # Deduplicate raw items (unique per store, city, category, title, price)
        unique_raw = []
        seen = set()
        for item in raw_items:
            # Metadata contains store and city
            meta = item.get('metadata', {})
            key = (
                item.get('raw_title'), 
                item.get('raw_price'), 
                meta.get('cat'), 
                meta.get('store'), 
                meta.get('city')
            )
            if key not in seen:
                unique_raw.append(item)
                seen.add(key)
        
        self.logger.info(f"Found {len(unique_raw)} unique items (removed {len(raw_items) - len(unique_raw)} duplicates).")
        
        processed_data = [self.process_item(item) for item in unique_raw if item]
        # Filter out items with no price
        processed_data = [p for p in processed_data if p['price'] is not None]
        
        # Remove outliers
        cleaned_data = self.remove_output_outliers(processed_data)
        
        # Save to processed layer
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in cleaned_data:
                f.write(json.dumps(item) + '\n')
                
        self.logger.info(f"Successfully processed {len(cleaned_data)} items. Saved to {output_path}")

if __name__ == "__main__":
    cleaner = DataCleaner()
    # Test on one file if run directly
    # cleaner.run_pipeline("data/raw/Metro_Karachi.jsonl", "data/processed/Metro_Karachi_Cleaned.jsonl")
