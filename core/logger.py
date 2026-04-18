import logging
import sys

# Get the root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# CLEAR existing handlers
if logger.hasHandlers():
    logger.handlers.clear()

# --- CONSOLE HANDLER ONLY (logs go to CloudWatch automatically) ---
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add handler
logger.addHandler(console_handler)

logger.propagate = False

__all__ = ["logger"]