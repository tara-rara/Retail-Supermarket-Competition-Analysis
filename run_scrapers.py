from src.scrapers.metro import MetroScraper
from src.scrapers.imtiaz import ImtiazScraper
from src.scrapers.alfatah import AlfatahScraper
from src.utils.logger import setup_logger
from multiprocessing import Pool
import os

main_logger = setup_logger("scrapers_main")

def run_scraper(args):
    """Worker function for parallel scraping."""
    ScraperClass, store_name, city = args
    try:
        main_logger.info(f"--- Starting {store_name} in {city} ---")
        scraper = ScraperClass(store_name=store_name, city=city)
        scraper.run()
        main_logger.info(f"--- Finished {store_name} in {city} ---")
        return True
    except Exception as e:
        main_logger.error(f"Batch failure for {store_name} ({city}): {e}")
        return False

def main():
    """
    Orchestrates the scraping of 3 major chains across multiple cities.
    Mandatory: 3 Stores, 2 Cities each.
    """
    tasks = [
        (MetroScraper, "Metro", "Karachi"),
        (MetroScraper, "Metro", "Lahore"),
        (ImtiazScraper, "Imtiaz", "Karachi"),
        (ImtiazScraper, "Imtiaz", "Islamabad"),
        (AlfatahScraper, "AlFatah", "Lahore"),
        (AlfatahScraper, "AlFatah", "Faisalabad")
    ]

    # Use a Pool to run tasks in parallel (adjust processes based on CPU/Memory)
    # We use mapping to execute all tasks across the pool
    with Pool(processes=min(len(tasks), 4)) as pool:
        results = pool.map(run_scraper, tasks)
    
    total = len(results)
    successes = sum(1 for r in results if r)
    main_logger.info(f"Scraping complete. {successes}/{total} tasks succeeded. Results: {results}")

if __name__ == "__main__":
    main()
