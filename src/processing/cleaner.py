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
        name = item.get('name', '')
        raw_price = item.get('price', '')
        
        price = self.clean_price(raw_price)
        if price is None:
            price = self.clean_price(name)
            
        std_qty, std_unit = self.parse_quantity(name)
        
        unit_price = round(price / std_qty, 2) if (price and std_qty and std_qty > 0) else None
        
        brand = item.get('brand', 'Generic')
        if not brand or brand == 'Generic':
            brand = self.extract_brand(name)
        
        processed = {
            "product_id": item.get('product_id', ''),
            "name": name,
            "brand": brand,
            "category": item.get('category', ''),
            "subcategory": item.get('subcategory', ''),
            "price": price,
            "quantity": std_qty,
            "unit": std_unit,
            "unit_price": unit_price,
            "availability": item.get('availability', 'In Stock'),
            "store": item.get('store', ''),
            "city": item.get('city', ''),
            "product_url": item.get('product_url', ''),
            "image_url": item.get('image_url', ''),
            "scrape_timestamp": item.get('timestamp'),
            "processed_timestamp": datetime.now().isoformat()
        }
        return processed

    def remove_output_outliers(self, processed_data):
        """Combined outlier detection."""
        if not processed_data:
            return processed_data
            
        def is_valid(item):
            # Check critical fields: name, price, store
            return all([item.get('name'), item.get('price'), item.get('store')])

        processed_data = [item for item in processed_data if is_valid(item)]

        def price_is_sane(item):
            up = item.get('unit_price')
            if up is None: return False
            return 1.0 < up < 100000.0

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
                
            mean = np.mean(prices)
            std = np.std(prices)
            
            q1 = np.percentile(prices, 25)
            q3 = np.percentile(prices, 75)
            iqr = q3 - q1
            # Slightly more relaxed bounds for better coverage
            lower_bound = q1 - 2.5 * iqr
            upper_bound = q3 + 2.5 * iqr
            
            for item in items:
                z_score = abs((item['price'] - mean) / std) if std > 0 else 0
                is_iqr_outlier = (item['price'] < lower_bound) or (item['price'] > upper_bound)
                
                if z_score <= 5 and not is_iqr_outlier:
                    cleaned_data.append(item)
                else:
                    self.logger.warning(f"Removing outlier in {cat}: {item['name']} at {item['price']}")
                    
        return cleaned_data

    def run_pipeline(self, input_path, output_path):
        """Process a whole .csv file."""
        if not os.path.exists(input_path):
            self.logger.error(f"Input file {input_path} not found.")
            return

        import csv
        self.logger.info(f"Processing CSV {input_path}...")
        raw_items = []
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_items.append(row)
        
        unique_raw = []
        seen = set()
        for item in raw_items:
            key = (item.get('name'), item.get('price'), item.get('store'), item.get('city'))
            if key not in seen:
                unique_raw.append(item)
                seen.add(key)
        
        self.logger.info(f"Found {len(unique_raw)} unique items.")
        
        processed_data = [self.process_item(item) for item in unique_raw]
        cleaned_data = self.remove_output_outliers(processed_data)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if cleaned_data:
            keys = cleaned_data[0].keys()
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(cleaned_data)
                
        self.logger.info(f"Successfully processed {len(cleaned_data)} items. Saved to {output_path}")

if __name__ == "__main__":
    import sys
    cleaner = DataCleaner()
    if len(sys.argv) > 2:
        cleaner.run_pipeline(sys.argv[1], sys.argv[2])
