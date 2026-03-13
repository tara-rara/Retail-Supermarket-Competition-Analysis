from src.scrapers.base_scraper import BaseScraper
from datetime import datetime

class MetroScraper(BaseScraper):
    def get_categories(self):
        return {
            "Grocery": "https://www.metro-online.pk/grocery",
            "Fruits-Vegetables": "https://www.metro-online.pk/fruits-and-vegetables",
            "Meat-Poultry": "https://www.metro-online.pk/fresh-meat",
            "Dairy-Frozen": "https://www.metro-online.pk/dairy-and-frozen-food",
            "Beverages": "https://www.metro-online.pk/beverages",
            "Household-Cleaning": "https://www.metro-online.pk/household-cleaning",
            "Personal-Care": "https://www.metro-online.pk/personal-care",
            "Electronics": "https://www.metro-online.pk/electronics-and-appliances",
            "Baby-Care": "https://www.metro-online.pk/baby-care"
        }

    def parse_items(self, page):
        products = []
        
        # Consistent with test_metro_logic.py which found 106 cards
        container_selector = 'div[class*="product_"], div[class*="productCard"], div[class*="nameAndPricing"]'
        containers = page.query_selector_all(container_selector)
        
        if not containers:
            # Absolute fallback
            containers = page.query_selector_all('div[class*="product"]')
            
        self.logger.info(f"Found {len(containers)} potential product containers using: {container_selector}")

        for i, container in enumerate(containers):
            try:
                # Titles - look for anything with Name or title
                name_elem = container.query_selector('[class*="Name"], [class*="name"], [class*="title"]')
                # Prices - look for anything with Price or a <p>
                price_elem = container.query_selector('[class*="Price"], [class*="price"], p')
                
                # If selectors fail, try to find text directly
                name = name_elem.inner_text().strip() if name_elem else ""
                price = price_elem.inner_text().strip() if price_elem else ""
                
                # Fallback: if name is empty, maybe it's in a header
                if not name:
                    h_elem = container.query_selector('h1, h2, h3, h4, h5')
                    if h_elem: name = h_elem.inner_text().strip()

                # Fallback: if price is empty or lacks Rs, search the whole container text
                if "Rs" not in price:
                    all_text = container.inner_text()
                    import re
                    match = re.search(r'Rs\.?\s*[\d,]+', all_text)
                    if match:
                        price = match.group(0)

                # Image URL
                img_elem = container.query_selector('img')
                image_url = img_elem.get_attribute('src') if img_elem else ""
                
                # Product URL
                link_elem = container.query_selector('a')
                product_url = link_elem.get_attribute('href') if link_elem else ""
                if product_url and not product_url.startswith('http'):
                    product_url = f"https://www.metro-online.pk{product_url}"

                if not name or "Rs" not in price:
                    continue
                    
                products.append({
                    "product_id": "",
                    "raw_title": name,
                    "raw_price": price,
                    "brand": "Generic",
                    "availability": "In Stock",
                    "product_url": product_url,
                    "image_url": image_url,
                    "scrape_timestamp": datetime.now().isoformat()
                })
            except Exception:
                continue
        
        if products:
            self.logger.info(f"Successfully scraped {len(products)} products.")
        else:
            self.logger.warning(f"No valid products identified from {len(containers)} containers.")
            
        return products