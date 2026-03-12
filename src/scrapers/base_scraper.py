import abc
import json
import os
import time
from datetime import datetime
from src.utils.logger import setup_logger
from playwright.sync_api import sync_playwright

class BaseScraper(abc.ABC):
    def __init__(self, store_name, city):
        self.store_name = store_name
        self.city = city
        self.logger = setup_logger(f"{store_name}_{city}")
        self.raw_dir = "data/raw"

    @abc.abstractmethod
    def get_categories(self): pass

    @abc.abstractmethod
    def parse_items(self, page): pass

    def setup_page(self, page):
        """Optional hook to handle modals/popups before scraping categories."""
        pass

    def run(self):
        """Orchestrates the scrape with retry logic and rate limiting."""
        self.logger.info(f"Starting {self.store_name} in {self.city}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            page = context.new_page()

            # Optional hook for site-specific setup (like closing modals cookie popups)
            self.setup_page(page)

            for category, url in self.get_categories().items():
                success = False
                
                # Rate Limiting: Reduced but still present
                time.sleep(1)
                self.logger.info(f"Navigating to {category} at {url}")
                
                # Mandatory Retry Logic & Exponential Backoff
                for attempt in range(1, 4): 
                    try:
                        self.logger.info(f"Scraping {category} (Attempt {attempt})")
                        page.goto(url, wait_until="networkidle", timeout=60000)
                        
                        # Pagination / Infinite Scroll Logic
                        self.scroll_to_bottom(page)
                        
                        items = self.parse_items(page)
                        self.save_to_raw(items, category)
                        
                        success = True
                        self.logger.info(f"Successfully scraped {len(items)} items for {category}")
                        break # Success, move to next category
                    except Exception as e:
                        # Exponential backoff: attempt^2 * 5 or 2^attempt * 5
                        wait_time = (2 ** attempt) * 5 
                        self.logger.error(f"Error scraping {category}: {str(e)}. Retrying in {wait_time}s...")
                        time.sleep(wait_time) 
                        
                if not success:
                    self.logger.error(f"Failed to scrape {category} after all attempts.")
            
            browser.close()

    def scroll_to_bottom(self, page):
        """Helper to trigger pagination/infinite scroll robustly."""
        self.logger.info("Starting automated scrolling...")
        last_height = page.evaluate("document.body.scrollHeight")
        
        while True:
            # Scroll down to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            
            # Rate limiting between scrolls
            time.sleep(3)
            
            # Look for explicit 'Load More' buttons and click if possible
            try:
                # Common classes/texts for load more buttons
                load_more_btn = page.query_selector("button:has-text('Load More'), button:has-text('Show More'), button:has-text('Next')")
                if load_more_btn and load_more_btn.is_visible():
                    load_more_btn.click()
                    time.sleep(3)
            except Exception:
                pass
            
            # Calculate new scroll height and compare with last scroll height
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                # Wait one more time to be sure
                time.sleep(2)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break # Reached the bottom
            last_height = new_height
            
        self.logger.info("Finished scrolling.")

    def save_to_raw(self, items, category):
        """Saves to Raw layer as required."""
        if not os.path.exists(self.raw_dir): os.makedirs(self.raw_dir)
        filename = f"{self.raw_dir}/{self.store_name}_{self.city}.jsonl"
        with open(filename, 'a', encoding='utf-8') as f:
            for item in items:
                item['metadata'] = {'city': self.city, 'store': self.store_name, 'cat': category}
                f.write(json.dumps(item) + '\n')