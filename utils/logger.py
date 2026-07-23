import logging
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.config import config

logger = logging.getLogger('trade-customer-agent')
logger.setLevel(getattr(logging, config.logging.get('level', 'INFO')))

formatter = logging.Formatter(config.logging.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)