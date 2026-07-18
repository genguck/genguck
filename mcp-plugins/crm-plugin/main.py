from fastmcp.server import FastMCPServer, Tool
from typing import Dict, List, Any, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.feishu_client import feishu_client
from utils.logger import logger

server = FastMCPServer(name="crm-plugin", version="1.0.0")

@server.register
class CRMPlugin:
    class Meta:
        name = "crm_plugin"
        description = "外贸客户CRM管理插件，基于飞书多维表格"
    
    @Tool(description="获取所有CRM表格列表")
    def list_tables(self) -> List[Dict[str, str]]:
        tables = feishu_client.get_base_tables()
        return [{"table_id": t.get("table_id"), "name": t.get("name")} for t in tables]
    
    @Tool(description="获取表格中的客户记录")
    def get_customers(self, table_id: str) -> List[Dict[str, Any]]:
        records = feishu_client.get_table_records(table_id)
        return [{"record_id": r.get("record_id"), "fields": r.get("fields", {})} for r in records]
    
    @Tool(description="添加新客户到CRM")
    def add_customer(self, table_id: str, company_name: str, website: Optional[str] = None, 
                    email: Optional[str] = None, phone: Optional[str] = None,
                    contact: Optional[str] = None, industry: Optional[str] = None,
                    score: Optional[int] = None, status: str = "待开发") -> Dict[str, Any]:
        fields = {
            "公司名称": company_name,
            "状态": status
        }
        if website:
            fields["网址"] = website
        if email:
            fields["邮箱"] = email
        if phone:
            fields["电话"] = phone
        if contact:
            fields["联系人"] = contact
        if industry:
            fields["行业"] = industry
        if score is not None:
            fields["评分"] = score
        
        result = feishu_client.create_record(table_id, fields)
        logger.info(f"添加客户成功: {company_name}")
        return result
    
    @Tool(description="更新客户信息")
    def update_customer(self, table_id: str, record_id: str, **kwargs) -> Dict[str, Any]:
        fields = {}
        field_mapping = {
            "company_name": "公司名称",
            "website": "网址",
            "email": "邮箱",
            "phone": "电话",
            "contact": "联系人",
            "industry": "行业",
            "score": "评分",
            "status": "状态"
        }
        
        for key, value in kwargs.items():
            if value is not None and key in field_mapping:
                fields[field_mapping[key]] = value
        
        result = feishu_client.update_record(table_id, record_id, fields)
        logger.info(f"更新客户成功: {record_id}")
        return result
    
    @Tool(description="删除客户记录")
    def delete_customer(self, table_id: str, record_id: str) -> bool:
        result = feishu_client.delete_record(table_id, record_id)
        if result:
            logger.info(f"删除客户成功: {record_id}")
        return result
    
    @Tool(description="搜索客户")
    def search_customers(self, table_id: str, keyword: str) -> List[Dict[str, Any]]:
        records = feishu_client.get_table_records(table_id)
        filtered = []
        for record in records:
            fields = record.get("fields", {})
            for value in fields.values():
                if isinstance(value, str) and keyword.lower() in value.lower():
                    filtered.append({"record_id": record.get("record_id"), "fields": fields})
                    break
        return filtered

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8001)