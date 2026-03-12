import logging
import os

def setup_logger(name):
    """Sets up a logger that saves to the logs/ folder."""
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        # Create file handler which logs even debug messages
        fh = logging.FileHandler(f'logs/{name}.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger