import logging
from config import config

logger = logging.getLogger('trade-customer-agent')
logger.setLevel(getattr(logging, config.logging.get('level', 'INFO')))

formatter = logging.Formatter(config.logging.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)