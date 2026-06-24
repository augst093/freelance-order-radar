import logging
import sys
from pathlib import Path

# Setup logging
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("freelance_radar.log", encoding="utf-8")
    ]
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
