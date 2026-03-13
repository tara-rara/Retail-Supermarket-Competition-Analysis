from src.scrapers.base_scraper import BaseScraper
from datetime import datetime

class AlfatahScraper(BaseScraper):
    def get_categories(self):
        return {
            "Grocery-Foods": "https://alfatah.pk/collections/grocery-foods",
            "Electronics": "https://alfatah.pk/collections/electronics",
            "Perfumes": "https://alfatah.pk/collections/perfumes",
            "Makeup": "https://alfatah.pk/collections/makeup",
            "Skin-Care": "https://alfatah.pk/collections/skin-care",
            "Baby-Care": "https://alfatah.pk/collections/baby-care",
            "Household-Items": "https://alfatah.pk/collections/household-items",
            "Beverages": "https://alfatah.pk/collections/drinks-beverages"
        }

    def parse_items(self, page):
        products = []
        # Updated Al-Fatah-specific CSS selectors
        cards = page.query_selector_all('div[class*="product-item"], div[class*="product-card"], a[class*="product"], div[class*="grid-product"]')
        for card in cards:
            try:
                title_elem = card.query_selector('div[class*="title"], h3[class*="title"], a[class*="title"]')
                price_elem = card.query_selector('div[class*="price"], span[class*="price"], div[class*="money"]')
                
                if not title_elem or not price_elem:
                    continue
                    
                title = title_elem.inner_text().strip()
                price = price_elem.inner_text().strip()
                
                if not title:
                    continue
                
                # Image URL
                img_elem = card.query_selector('img')
                image_url = img_elem.get_attribute('src') if img_elem else ""
                if image_url and image_url.startswith('//'):
                    image_url = f"https:{image_url}"
                
                # Product URL
                link_elem = card.query_selector('a')
                product_url = link_elem.get_attribute('href') if link_elem else ""
                if product_url and not product_url.startswith('http'):
                    product_url = f"https://alfatah.pk{product_url}"

                products.append({
                    "product_id": "",
                    "raw_title": title,
                    "raw_price": price,
                    "brand": "Generic",
                    "availability": "In Stock",
                    "product_url": product_url,
                    "image_url": image_url,
                    "scrape_timestamp": datetime.now().isoformat()
                })
            except Exception:
                continue
        return products