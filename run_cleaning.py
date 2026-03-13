import os
import logging
from src.processing.cleaner import DataCleaner

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/processing.log"),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger("ProcessingOrchestrator")
    
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    
    if not os.path.exists(raw_dir):
        logger.error(f"Raw data directory {raw_dir} not found.")
        return

    cleaner = DataCleaner()
    
    # Process each .csv file in raw_dir
    for filename in sorted(os.listdir(raw_dir)):
        if filename.endswith(".csv"):
            input_path = os.path.join(raw_dir, filename)
            output_path = os.path.join(processed_dir, filename.replace(".csv", "_cleaned.csv"))
            
            try:
                cleaner.run_pipeline(input_path, output_path)
            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")

    logger.info("Batch processing complete.")

if __name__ == "__main__":
    main()
