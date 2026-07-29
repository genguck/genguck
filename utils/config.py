import os
from typing import Dict, Any
import yaml
from dotenv import load_dotenv

load_dotenv()

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        with open(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'), 'r', encoding='utf-8') as f:
            self.yaml_config = yaml.safe_load(f)
        
        self.app = self.yaml_config.get('app', {})
        self.server = self.yaml_config.get('server', {})
        self.feishu = {
            'app_id': os.getenv('FEISHU_APP_ID', self.yaml_config.get('feishu', {}).get('app_id', '')),
            'app_secret': os.getenv('FEISHU_APP_SECRET', self.yaml_config.get('feishu', {}).get('app_secret', '')),
            'base_token': os.getenv('FEISHU_BASE_TOKEN', self.yaml_config.get('feishu', {}).get('base_token', ''))
        }
        self.email = {
            'smtp_server': os.getenv('EMAIL_SMTP_SERVER', self.yaml_config.get('email', {}).get('smtp_server', '')),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', self.yaml_config.get('email', {}).get('smtp_port', 587))),
            'smtp_username': os.getenv('EMAIL_SMTP_USERNAME', self.yaml_config.get('email', {}).get('smtp_username', '')),
            'smtp_password': os.getenv('EMAIL_SMTP_PASSWORD', self.yaml_config.get('email', {}).get('smtp_password', '')),
            'sender_email': os.getenv('EMAIL_SENDER_EMAIL', self.yaml_config.get('email', {}).get('sender_email', ''))
        }
        self.search = {
            'serp_api_key': os.getenv('SEARCH_SERP_API_KEY', self.yaml_config.get('search', {}).get('serp_api_key', '')),
            'google_api_key': os.getenv('SEARCH_GOOGLE_API_KEY', self.yaml_config.get('search', {}).get('google_api_key', '')),
            'google_cse_id': os.getenv('SEARCH_GOOGLE_CSE_ID', self.yaml_config.get('search', {}).get('google_cse_id', ''))
        }
        self.google_maps = {
            'api_key': os.getenv('GOOGLE_MAPS_API_KEY', self.yaml_config.get('google_maps', {}).get('api_key', '')),
            'default_radius_km': self.yaml_config.get('google_maps', {}).get('default_radius_km', 50),
            'max_results_per_search': self.yaml_config.get('google_maps', {}).get('max_results_per_search', 60),
            'language': self.yaml_config.get('google_maps', {}).get('language', 'zh-CN'),
        }
        self.crm = self.yaml_config.get('crm', {})
        self.logging = self.yaml_config.get('logging', {})
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.yaml_config.get(key, default)

config = Config()