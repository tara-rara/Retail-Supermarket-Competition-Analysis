from src.scrapers.base_scraper import BaseScraper
from datetime import datetime
import time

class ImtiazScraper(BaseScraper):
    def get_categories(self):
        # Targeting leaf categories for more reliable data extraction
        base_url = "https://shop.imtiaz.com.pk"
        return {
            "Rice": f"{base_url}/catalog/edible-grocery-4085/rice-40516",
            "Pulses-Grains": f"{base_url}/catalog/edible-grocery-4085/pulses--grains-40517",
            "Flour": f"{base_url}/catalog/edible-grocery-4085/flour-40518",
            "Oil-Ghee": f"{base_url}/catalog/edible-grocery-4085/edible-oil--ghee-40521",
            "Spices-Herbs": f"{base_url}/catalog/edible-grocery-4085/salt-spices--herbs-40515",
            "Beverages": f"{base_url}/catalog/beverages-4084",
            "Personal-Care": f"{base_url}/catalog/personal-care-4088",
            "Baby-Care": f"{base_url}/catalog/baby-care-4087"
        }

    def setup_page(self, page):
        """Handle the location selection modal on first visit."""
        self.logger.info("Checking for Imtiaz location modal...")
        
        # Fixed: Navigate and retry specifically for Imtiaz home
        max_retries = 3
        nav_success = False
        for i in range(max_retries):
            try:
                page.goto("https://shop.imtiaz.com.pk/", wait_until="networkidle", timeout=60000)
                nav_success = True
                break
            except Exception as e:
                self.logger.warning(f"Home page load attempt {i+1} failed: {e}")
                time.sleep(5)
        
        if not nav_success: return

        try:
            # Try multiple common selectors for the area/region input
            self.logger.info("Waiting for area input selector...")
            area_input = page.wait_for_selector('input[placeholder*="Area"], input[placeholder*="Region"]', timeout=20000)
            if area_input:
                self.logger.info("Found area input. Clicking...")
                area_input.click()
                time.sleep(2)
                
                self.logger.info("Typing city and selecting...")
                # page.keyboard.type(self.city) # Try typing first
                # time.sleep(1)
                page.keyboard.press("ArrowDown")
                page.keyboard.press("Enter")
                time.sleep(2)
                
                # Try multiple button labels
                self.logger.info("Waiting for confirm button...")
                confirm_btn = page.query_selector("button:has-text('Confirm'), button:has-text('Update'), button:has-text('Select')")
                if confirm_btn:
                    confirm_btn.click()
                    time.sleep(3)
                    self.logger.info("Modal bypassed successfully.")
                else:
                    self.logger.warning("Confirm button not found after selecting area.")
        except Exception as e:
            self.logger.info(f"Modal bypass interaction skipped/failed: {e}")

    def parse_items(self, page):
        products = []
        
        # 1. Attempt JSON extraction from __NEXT_DATA__ (Fast & Reliable)
        try:
            import json
            script = page.query_selector("script#__NEXT_DATA__")
            if script:
                data = json.loads(script.inner_text())
                raw_items = []
                # Common paths for product lists in Imtiaz
                try: raw_items = data['props']['pageProps']['initialState']['products']['list']
                except:
                    try: raw_items = data['props']['pageProps']['data']['products']
                    except: pass
                
                if raw_items:
                    for item in raw_items:
                        name = item.get('name') or item.get('title')
                        price = item.get('price') or item.get('sale_price')
                        if name and price:
                            products.append({
                                "raw_title": str(name),
                                "raw_price": f"Rs. {price}",
                                "scrape_timestamp": datetime.now().isoformat()
                            })
                    if products:
                        self.logger.info(f"Successfully extracted {len(products)} products from NEXT_DATA.")
                        return products
        except Exception as e:
            self.logger.debug(f"NEXT_DATA parsing failed: {e}")

        # 2. Fallback to DOM traversal
        containers = page.query_selector_all('div.MuiGrid-item, div[class*="MuiGrid"], div[class*="hazle-"]')
        if not containers:
            containers = page.query_selector_all('div')

        for container in containers:
            try:
                title_elem = container.query_selector('h4, div[class*="title"], p[class*="name"]')
                if not title_elem: continue
                
                title = title_elem.inner_text().strip()
                if not title or len(title) < 3: continue
                    
                price_elem = container.query_selector('p:has-text("Rs."), div:has-text("Rs."), span:has-text("Rs.")')
                if not price_elem: continue
                
                price = price_elem.inner_text().strip().split('\n')[-1]
                if not price or "Rs." not in price: continue
                
                if any(p["raw_title"] == title for p in products): continue
                    
                products.append({
                    "raw_title": title,
                    "raw_price": price,
                    "scrape_timestamp": datetime.now().isoformat()
                })
            except Exception:
                continue
        
        if products:
            self.logger.info(f"Successfully scraped {len(products)} products using DOM traversal.")
            
        return products