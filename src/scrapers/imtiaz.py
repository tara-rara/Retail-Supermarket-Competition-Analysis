from src.scrapers.base_scraper import BaseScraper
from datetime import datetime
import time

class ImtiazScraper(BaseScraper):
    def get_categories(self):
        """Fetch leaf categories dynamically. Imtiaz uses a 2-level structure."""
        self.logger.info("Fetching categories dynamically (including subcategories)...")
        top_categories = {}
        try:
            # Ensure we are on home page
            if self.page.url != "https://shop.imtiaz.com.pk/":
                self.page.goto("https://shop.imtiaz.com.pk/", wait_until="networkidle")
                time.sleep(5)
            
            # Find all top level category links
            links = self.page.query_selector_all('a[href*="/catalog/"]')
            for link in links:
                try:
                    href = link.get_attribute('href')
                    name = link.inner_text().strip().split('\n')[0]
                    if name and href and '/catalog/' in href:
                        # Top level paths look like /catalog/name-id (length 3 when split by /)
                        # e.g. ['', 'catalog', 'edible-grocery-4085']
                        path_parts = href.strip('/').split('/')
                        if len(path_parts) == 2:
                            top_categories[name] = f"https://shop.imtiaz.com.pk/{href.lstrip('/')}"
                except: continue
            
            self.logger.info(f"Found {len(top_categories)} top categories. Checking for subcategories...")
            
            all_leaf_categories = {}
            # To save time and avoid getting blocked, we only check a few key categories 
            # if the list is too long, but for a full scrape we check all.
            for top_name, top_url in top_categories.items():
                try:
                    self.logger.info(f"Visiting {top_name} to find subcategories...")
                    self.page.goto(top_url, wait_until="networkidle", timeout=60000)
                    time.sleep(3)
                    
                    sub_links = self.page.query_selector_all('a[href*="/catalog/"]')
                    found_sub = False
                    for sub in sub_links:
                        sub_href = sub.get_attribute('href')
                        sub_name = sub.inner_text().strip().split('\n')[0]
                        if sub_href and sub_name and '/catalog/' in sub_href:
                            sub_path = sub_href.strip('/').split('/')
                            # Sub-category paths have 3 parts: catalog/category/subcategory-id
                            if len(sub_path) == 3:
                                full_sub_url = f"https://shop.imtiaz.com.pk/{sub_href.lstrip('/')}"
                                all_leaf_categories[f"{top_name} > {sub_name}"] = full_sub_url
                                found_sub = True
                    
                    if not found_sub:
                        # If no subcategories found, the top level might have products
                        all_leaf_categories[top_name] = top_url
                except Exception as e:
                    self.logger.warning(f"Failed to fetch subcategories for {top_name}: {e}")
                    all_leaf_categories[top_name] = top_url
            
            if not all_leaf_categories:
                return top_categories
                
            self.logger.info(f"Found {len(all_leaf_categories)} leaf categories in total.")
            return all_leaf_categories
        except Exception as e:
            self.logger.error(f"Error fetching categories: {e}")
            return {}

    def setup_page(self, page):
        """Handle the location selection modal on first visit using LocalStorage injection."""
        self.page = page 
        self.logger.info(f"Setting up Imtiaz page for {self.city} using LS injection...")
        
        # Branch IDs mapped by city
        branch_ids = {
            "karachi": 54934,
            "lahore": 54935,
            "islamabad": 54936,
            "faisalabad": 54937
        }
        branch_id = branch_ids.get(self.city.lower(), 54934)
        
        # This script simulates the selection of location in LocalStorage
        inject_script = f"""
        localStorage.setItem('stored_location', '"{branch_id}"');
        localStorage.setItem('location_selected_by_user', '1');
        // Partial state for redundancy
        const rootState = JSON.parse(localStorage.getItem('persist:root') || '{{}}');
        if (rootState.state) {{
            const state = JSON.parse(rootState.state);
            state.currentBranchId = {branch_id};
            rootState.state = JSON.stringify(state);
            localStorage.setItem('persist:root', JSON.stringify(rootState));
        }}
        """
        
        try:
            # 1. Add init script and navigate
            page.add_init_script(inject_script)
            page.goto("https://shop.imtiaz.com.pk/", wait_until="networkidle", timeout=120000)
            time.sleep(5)
            
            # 2. Check if modal is still there and close it if necessary
            # (Sometimes a cookie-based modal or a forced refresh happens)
            modal = page.query_selector('div[role="presentation"]')
            if modal:
                self.logger.info("Modal still present after injection, attempting manual bypass...")
                # Try the manual steps as fallback
                try:
                    # Look for Select/Confirm buttons to close it
                    close_btn = page.query_selector("button:has-text('Select'), button:has-text('Confirm')")
                    if close_btn:
                        close_btn.click(force=True)
                        time.sleep(3)
                except: pass
            
            # 3. Final verify by checking header text
            header = page.query_selector('header')
            if header:
                header_text = header.inner_text()
                if self.city.lower() in header_text.lower():
                    self.logger.info(f"Verified location {self.city} in header.")
                else:
                    self.logger.warning(f"Could not verify {self.city} in header. Moving on.")
                    
        except Exception as e:
            self.logger.error(f"Setup with LS injection failed/timed out: {e}")
            try:
                page.screenshot(path="logs/setup_failure.png")
            except: pass

    def parse_items(self, page):
        products_dict = {} # Use dict with title as key to avoid duplicates
        
        # 1. Attempt JSON extraction from __NEXT_DATA__
        self.logger.debug("Attempting NEXT_DATA extraction...")
        try:
            import json
            script = page.query_selector("script#__NEXT_DATA__")
            if script:
                data = json.loads(script.inner_text())
                raw_items = []
                # Check multiple possible paths in the JSON structure
                paths = [
                    ['props', 'pageProps', 'initialState', 'products', 'list'],
                    ['props', 'pageProps', 'data', 'products'],
                    ['props', 'pageProps', 'category', 'products'],
                    ['props', 'pageProps', 'section', 'products']
                ]
                
                for path in paths:
                    try:
                        temp = data
                        for key in path:
                            temp = temp[key]
                        if isinstance(temp, list):
                            raw_items.extend(temp)
                    except: continue
                
                for item in raw_items:
                    if not isinstance(item, dict): continue
                    name = item.get('name') or item.get('title')
                    price = item.get('price') or item.get('sale_price')
                    if name and price:
                        title = str(name).strip()
                        if title and title not in products_dict:
                            slug = item.get('slug', '')
                            # Extracting brand if available
                            brand = item.get('brand', {}).get('name') if isinstance(item.get('brand'), dict) else item.get('brand_name', 'Generic')
                            
                            products_dict[title] = {
                                "product_id": str(item.get('id', '')),
                                "raw_title": title,
                                "raw_price": f"Rs. {price}",
                                "brand": brand,
                                "availability": "In Stock" if item.get('status') == 1 else "Out of Stock",
                                "product_url": f"https://shop.imtiaz.com.pk/product/{slug}" if slug else "",
                                "image_url": item.get('thumbnail', '') or item.get('image', ''),
                                "scrape_timestamp": datetime.now().isoformat()
                            }
        except Exception as e:
            self.logger.debug(f"NEXT_DATA parsing failed: {e}")

        # 2. Extract from DOM (Crucial for items loaded via infinite scroll)
        self.logger.debug("Attempting DOM extraction...")
        # Common selectors for product containers
        selectors = [
            'div[class*="product_item"]',
            'div.MuiGrid-item',
            'div[class*="hazle-"]'
        ]
        
        containers = []
        for selector in selectors:
            containers = page.query_selector_all(selector)
            if len(containers) > 5: # Found enough items
                break

        for container in containers:
            try:
                # Title selectors
                title_elem = container.query_selector('h4[class*="title"], h4, div[class*="title"], p[class*="name"]')
                if not title_elem: continue
                
                title = title_elem.inner_text().strip()
                if not title or len(title) < 3: continue
                if title in products_dict: continue # Already found in NEXT_DATA
                    
                # Price selectors
                price_elem = container.query_selector('div[class*="price_label"], p:has-text("Rs."), div:has-text("Rs."), span:has-text("Rs.")')
                if not price_elem: continue
                
                price_text = price_elem.inner_text().strip()
                if "Rs." not in price_text: continue
                
                import re
                # Extract the price value (handles "Rs. 200" or multi-line prices)
                price_match = re.search(r'Rs\.\s*[\d,.]+', price_text)
                price = price_match.group(0) if price_match else price_text
                
                # Image URL
                img_elem = container.query_selector('img')
                image_url = img_elem.get_attribute('src') if img_elem else ""
                
                # Product URL
                link_elem = container.query_selector('a')
                product_url = link_elem.get_attribute('href') if link_elem else ""
                if product_url and not product_url.startswith('http'):
                    product_url = f"https://shop.imtiaz.com.pk{product_url}"

                products_dict[title] = {
                    "product_id": "", # Hard to get from DOM without data attributes
                    "raw_title": title,
                    "raw_price": price,
                    "brand": "Generic",
                    "availability": "In Stock",
                    "product_url": product_url,
                    "image_url": image_url,
                    "scrape_timestamp": datetime.now().isoformat()
                }
            except: continue
        
        final_products = list(products_dict.values())
        if final_products:
            self.logger.info(f"Total extracted: {len(final_products)} products (JSON + DOM).")
            
        return final_products
