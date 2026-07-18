import requests
import json
from typing import Dict, List, Any
from config import config
from logger import logger

class FeishuClient:
    def __init__(self):
        self.app_id = config.feishu['app_id']
        self.app_secret = config.feishu['app_secret']
        self.base_token = config.feishu['base_token']
        self.access_token = None
    
    def _get_access_token(self) -> str:
        if self.access_token:
            return self.access_token
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get('tenant_access_token', '')
            return self.access_token
        except Exception as e:
            logger.error(f"获取飞书AccessToken失败: {e}")
            raise
    
    def get_base_tables(self) -> List[Dict[str, Any]]:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_token}/tables"
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('data', {}).get('items', [])
        except Exception as e:
            logger.error(f"获取飞书Base表格失败: {e}")
            return []
    
    def get_table_records(self, table_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_token}/tables/{table_id}/records"
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}
        records = []
        page_token = ""
        
        while True:
            params = {"page_size": page_size}
            if page_token:
                params["page_token"] = page_token
            
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json().get('data', {})
                records.extend(data.get('items', []))
                page_token = data.get('page_token', '')
                if not page_token:
                    break
            except Exception as e:
                logger.error(f"获取表格记录失败: {e}")
                break
        
        return records
    
    def create_record(self, table_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_token}/tables/{table_id}/records"
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}
        payload = {"fields": fields}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json().get('data', {})
        except Exception as e:
            logger.error(f"创建记录失败: {e}")
            return {}
    
    def update_record(self, table_id: str, record_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/{record_id}"
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}
        payload = {"fields": fields}
        
        try:
            response = requests.patch(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json().get('data', {})
        except Exception as e:
            logger.error(f"更新记录失败: {e}")
            return {}
    
    def delete_record(self, table_id: str, record_id: str) -> bool:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/{record_id}"
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}
        
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            return False

feishu_client = FeishuClient()