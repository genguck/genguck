from typing import Dict, List, Any, Optional
import re
import requests
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger

class TradeCustomerSkill:
    def __init__(self):
        self.mcp_servers = {
            "crm": "http://localhost:8001",
            "search": "http://localhost:8002",
            "crawl": "http://localhost:8003",
            "score": "http://localhost:8004",
            "email": "http://localhost:8005"
        }
    
    def execute(self, instruction: str, **kwargs) -> Dict[str, Any]:
        parsed = self._parse_instruction(instruction)
        task_type = parsed.get("task_type", "full")
        
        logger.info(f"解析指令: {instruction}")
        logger.info(f"任务类型: {task_type}, 参数: {parsed}")
        
        result = {
            "status": "success",
            "task_type": task_type,
            "results": {},
            "customers": [],
            "summary": ""
        }
        
        try:
            if task_type == "full":
                result = self._execute_full_workflow(parsed)
            elif task_type == "search":
                result = self._execute_search(parsed)
            elif task_type == "extract":
                result = self._execute_extract(parsed, kwargs.get("customers", []))
            elif task_type == "score":
                result = self._execute_score(parsed, kwargs.get("customers", []))
            elif task_type == "email":
                result = self._execute_email(parsed, kwargs.get("customers", []))
            elif task_type == "crm":
                result = self._execute_crm(parsed)
            
            result["summary"] = self._generate_summary(result)
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def _parse_instruction(self, instruction: str) -> Dict[str, Any]:
        result = {
            "task_type": "full",
            "industry": "",
            "count": 5,
            "region": "",
            "action": ""
        }
        
        instruction_lower = instruction.lower()
        
        if "搜索" in instruction or "查找" in instruction or "寻找" in instruction:
            result["task_type"] = "search"
            result["action"] = "search"
        
        elif "提取" in instruction or "获取" in instruction or "完善" in instruction:
            result["task_type"] = "extract"
            result["action"] = "extract"
        
        elif "评分" in instruction or "评估" in instruction or "分级" in instruction:
            result["task_type"] = "score"
            result["action"] = "score"
        
        elif "发送" in instruction or "邮件" in instruction or "开发信" in instruction:
            result["task_type"] = "email"
            result["action"] = "email"
        
        elif "查看" in instruction or "列表" in instruction or "CRM" in instruction:
            result["task_type"] = "crm"
            result["action"] = "view"
        
        elif "开发" in instruction or "客户" in instruction:
            result["task_type"] = "full"
            result["action"] = "develop"
        
        industry_keywords = [
            "医疗", "电子", "机械", "化工", "食品", "服装", "建材", "汽车",
            "IT", "软件", "科技", "能源", "环保", "物流", "贸易", "制造"
        ]
        
        for keyword in industry_keywords:
            if keyword in instruction:
                result["industry"] = keyword
                break
        
        count_match = re.search(r'(\d+)\s*个', instruction)
        if count_match:
            result["count"] = int(count_match.group(1))
        
        region_keywords = ["美国", "欧洲", "德国", "英国", "法国", "日本", "韩国", "东南亚"]
        for keyword in region_keywords:
            if keyword in instruction:
                result["region"] = keyword
                break
        
        return result
    
    def _call_mcp(self, server_name: str, method: str, **kwargs) -> Any:
        server_url = self.mcp_servers.get(server_name)
        if not server_url:
            logger.error(f"MCP服务器 {server_name} 未配置")
            return None
        
        url = f"{server_url}/v1/invoke"
        payload = {
            "name": f"{server_name}_plugin.{method}",
            "arguments": kwargs
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("result")
        except Exception as e:
            logger.error(f"调用MCP {server_name}.{method} 失败: {e}")
            return None
    
    def _execute_full_workflow(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        industry = parsed.get("industry", "")
        count = parsed.get("count", 5)
        
        result = {
            "status": "success",
            "task_type": "full",
            "results": {
                "search_count": 0,
                "crawl_count": 0,
                "extract_count": 0,
                "score_count": 0,
                "crm_count": 0,
                "email_count": 0
            },
            "customers": []
        }
        
        search_query = f"{industry} company"
        if parsed.get("region"):
            search_query += f" {parsed['region']}"
        
        search_results = self._call_mcp("search", "search_customers", query=search_query, count=count * 2)
        if not search_results:
            result["status"] = "failed"
            result["error"] = "搜索客户失败"
            return result
        
        result["results"]["search_count"] = len(search_results)
        
        customers = []
        for sr in search_results[:count]:
            company_name = sr.get("title", "")
            website = sr.get("link", "")
            
            if not website:
                continue
            
            crawl_result = self._call_mcp("crawl", "crawl_website", url=website)
            if crawl_result and crawl_result.get("status") == "success":
                result["results"]["crawl_count"] += 1
                
                extract_result = self._call_mcp("crawl", "extract_all_contacts", url=website)
                if extract_result:
                    result["results"]["extract_count"] += 1
                    
                    customer = {
                        "company_name": company_name,
                        "website": website,
                        "emails": extract_result.get("emails", []),
                        "phones": extract_result.get("phones", []),
                        "contacts": extract_result.get("contacts", []),
                        "social_links": extract_result.get("social_links", {}),
                        "content": crawl_result.get("content", "")
                    }
                    
                    score_result = self._call_mcp("score", "score_customer",
                        company_name=company_name,
                        website=website,
                        emails=customer["emails"],
                        phones=customer["phones"],
                        industry=industry,
                        content=customer["content"]
                    )
                    
                    if score_result:
                        result["results"]["score_count"] += 1
                        customer["score"] = score_result.get("total_score", 0)
                        customer["level"] = score_result.get("level", "D")
                        customer["recommendation"] = score_result.get("recommendation", "")
                    
                    tables = self._call_mcp("crm", "list_tables")
                    if tables:
                        table_id = tables[0].get("table_id")
                        if table_id:
                            crm_result = self._call_mcp("crm", "add_customer",
                                table_id=table_id,
                                company_name=company_name,
                                website=website,
                                email=customer["emails"][0] if customer["emails"] else None,
                                phone=customer["phones"][0] if customer["phones"] else None,
                                contact=customer["contacts"][0] if customer["contacts"] else None,
                                industry=industry,
                                score=customer.get("score", 0),
                                status="待开发"
                            )
                            if crm_result:
                                result["results"]["crm_count"] += 1
                                customer["crm_record_id"] = crm_result.get("record_id")
                    
                    if customer["emails"]:
                        email_type = "personalized" if customer.get("level") == "A" else "standard"
                        email_result = self._call_mcp("email", "generate_and_send",
                            company_name=company_name,
                            to_email=customer["emails"][0],
                            contact=customer["contacts"][0] if customer["contacts"] else "",
                            industry=industry,
                            email_type=email_type
                        )
                        
                        if email_result and email_result.get("status") == "success":
                            result["results"]["email_count"] += 1
                            customer["email_sent"] = True
                        else:
                            customer["email_sent"] = False
                    else:
                        customer["email_sent"] = False
                    
                    customers.append(customer)
        
        result["customers"] = customers
        return result
    
    def _execute_search(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        industry = parsed.get("industry", "")
        count = parsed.get("count", 10)
        
        search_query = f"{industry} company"
        if parsed.get("region"):
            search_query += f" {parsed['region']}"
        
        results = self._call_mcp("search", "search_customers", query=search_query, count=count)
        
        return {
            "status": "success" if results else "failed",
            "task_type": "search",
            "results": {"search_count": len(results) if results else 0},
            "customers": results or []
        }
    
    def _execute_extract(self, parsed: Dict[str, Any], customers: List[Dict[str, Any]]) -> Dict[str, Any]:
        result = {
            "status": "success",
            "task_type": "extract",
            "results": {"extract_count": 0},
            "customers": []
        }
        
        for customer in customers:
            website = customer.get("website", "")
            if not website:
                continue
            
            extract_result = self._call_mcp("crawl", "extract_all_contacts", url=website)
            if extract_result:
                result["results"]["extract_count"] += 1
                customer["emails"] = extract_result.get("emails", [])
                customer["phones"] = extract_result.get("phones", [])
                customer["contacts"] = extract_result.get("contacts", [])
                customer["social_links"] = extract_result.get("social_links", {})
                result["customers"].append(customer)
        
        return result
    
    def _execute_score(self, parsed: Dict[str, Any], customers: List[Dict[str, Any]]) -> Dict[str, Any]:
        result = {
            "status": "success",
            "task_type": "score",
            "results": {"score_count": 0},
            "customers": []
        }
        
        industry = parsed.get("industry", "")
        
        for customer in customers:
            score_result = self._call_mcp("score", "score_customer",
                company_name=customer.get("company_name", ""),
                website=customer.get("website", ""),
                emails=customer.get("emails", []),
                phones=customer.get("phones", []),
                industry=industry,
                content=customer.get("content", "")
            )
            
            if score_result:
                result["results"]["score_count"] += 1
                customer["score"] = score_result.get("total_score", 0)
                customer["level"] = score_result.get("level", "D")
                customer["recommendation"] = score_result.get("recommendation", "")
                result["customers"].append(customer)
        
        return result
    
    def _execute_email(self, parsed: Dict[str, Any], customers: List[Dict[str, Any]]) -> Dict[str, Any]:
        result = {
            "status": "success",
            "task_type": "email",
            "results": {"email_count": 0},
            "customers": []
        }
        
        industry = parsed.get("industry", "")
        
        for customer in customers:
            if not customer.get("emails"):
                continue
            
            email_type = "personalized" if customer.get("level") == "A" else "standard"
            email_result = self._call_mcp("email", "generate_and_send",
                company_name=customer.get("company_name", ""),
                to_email=customer["emails"][0],
                contact=customer.get("contacts", [])[0] if customer.get("contacts") else "",
                industry=industry,
                email_type=email_type
            )
            
            if email_result and email_result.get("status") == "success":
                result["results"]["email_count"] += 1
                customer["email_sent"] = True
            else:
                customer["email_sent"] = False
            
            result["customers"].append(customer)
        
        return result
    
    def _execute_crm(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        tables = self._call_mcp("crm", "list_tables")
        
        if not tables:
            return {
                "status": "failed",
                "task_type": "crm",
                "error": "获取表格列表失败"
            }
        
        table_id = tables[0].get("table_id")
        customers = self._call_mcp("crm", "get_customers", table_id=table_id)
        
        return {
            "status": "success" if customers else "failed",
            "task_type": "crm",
            "results": {"crm_count": len(customers) if customers else 0},
            "customers": customers or []
        }
    
    def _generate_summary(self, result: Dict[str, Any]) -> str:
        if result.get("status") == "failed":
            return f"任务执行失败: {result.get('error', '未知错误')}"
        
        task_type = result.get("task_type", "")
        results = result.get("results", {})
        customers = result.get("customers", [])
        
        if task_type == "full":
            summary = f"完整获客流程完成："
            summary += f"\n- 搜索到 {results.get('search_count', 0)} 个潜在客户"
            summary += f"\n- 爬取了 {results.get('crawl_count', 0)} 个官网"
            summary += f"\n- 提取了 {results.get('extract_count', 0)} 个客户的联系方式"
            summary += f"\n- 评分了 {results.get('score_count', 0)} 个客户"
            summary += f"\n- 录入CRM {results.get('crm_count', 0)} 个客户"
            summary += f"\n- 发送了 {results.get('email_count', 0)} 封开发信"
            
            level_counts = {}
            for c in customers:
                level = c.get("level", "D")
                level_counts[level] = level_counts.get(level, 0) + 1
            
            if level_counts:
                summary += "\n- 客户等级分布："
                for level in ["A", "B", "C", "D"]:
                    if level_counts.get(level):
                        summary += f"{level}级{level_counts[level]}个，"
                summary = summary[:-1]
        
        elif task_type == "search":
            summary = f"搜索完成：共找到 {results.get('search_count', 0)} 个潜在客户"
        
        elif task_type == "extract":
            summary = f"联系方式提取完成：共提取 {results.get('extract_count', 0)} 个客户的联系方式"
        
        elif task_type == "score":
            summary = f"客户评分完成：共评估 {results.get('score_count', 0)} 个客户"
            
            level_counts = {}
            for c in customers:
                level = c.get("level", "D")
                level_counts[level] = level_counts.get(level, 0) + 1
            
            if level_counts:
                summary += "\n- 客户等级分布："
                for level in ["A", "B", "C", "D"]:
                    if level_counts.get(level):
                        summary += f"{level}级{level_counts[level]}个，"
                summary = summary[:-1]
        
        elif task_type == "email":
            summary = f"邮件发送完成：共发送 {results.get('email_count', 0)} 封开发信"
        
        elif task_type == "crm":
            summary = f"CRM查询完成：共 {results.get('crm_count', 0)} 个客户记录"
        
        else:
            summary = f"任务完成"
        
        return summary

if __name__ == "__main__":
    skill = TradeCustomerSkill()
    
    instruction = "帮我开发5个医疗客户"
    result = skill.execute(instruction)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))