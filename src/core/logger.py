import logging
import os
import sys
from datetime import datetime

LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

def setup_logger(name="GameLogger", log_file=None, level=logging.DEBUG):
    """
    Sets up a logger with the specified name, log file, and logging level.
    
    Args:
        name (str): The name of the logger.
        log_file (str): The name of the log file. If None, generates a timestamped name.
        level (int): The logging level (e.g., logging.DEBUG, logging.INFO).
        
    Returns:
        logging.Logger: The configured logger instance.
    """
    if log_file is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(LOGS_DIR, f"game_{timestamp}.log")
    else:
        log_file = os.path.join(LOGS_DIR, log_file)

    logger = logging.getLogger(name)
    logger.setLevel(level)
 
    if not logger.handlers:
        c_handler = logging.StreamHandler(sys.stdout)
        f_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        c_handler.setLevel(level)
        f_handler.setLevel(level)

        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    return logger

logger = setup_logger()
