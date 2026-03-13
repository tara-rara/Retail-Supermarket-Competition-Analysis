import os
import logging
import subprocess
import time

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/pipeline.log"),
            logging.StreamHandler()
        ]
    )

def run_step(script_name, description):
    logger = logging.getLogger("PipelineOrchestrator")
    logger.info(f">>> STEP: {description} ({script_name})")
    start = time.time()
    try:
        # Run as a subprocess to keep environments clean
        result = subprocess.run(["python", script_name], check=True, capture_output=True, text=True)
        # logger.info(result.stdout)
        duration = time.time() - start
        logger.info(f"Finished {description} in {duration:.2f}s")
    except subprocess.CalledProcessError as e:
        logger.error(f"FAILED: {description}. Error: {e.stderr}")
        return False
    return True

def main():
    setup_logging()
    logger = logging.getLogger("PipelineOrchestrator")
    logger.info("Initializing Pakistan Supermarket Analysis Pipeline (Inspired by pakistan_supermarket_analysis_dataset)")

    # 1. Scraping (Optional: user might want to run manually or this script runs all)
    # run_step("run_scrapers.py", "Global Data Scraping")

    # 2. Cleaning
    if not run_step("run_cleaning.py", "Data Cleaning & Normalization"):
        return

    # 3. Matching
    if not run_step("run_matching.py", "Product Entity Resolution (Fuzzy Matching)"):
        return

    # 4. Analytics
    if not run_step("run_analytics.py", "Statistical Analysis & Reporting"):
        return

    logger.info("Full pipeline execution completed successfully.")

if __name__ == "__main__":
    main()
