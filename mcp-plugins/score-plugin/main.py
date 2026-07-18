from fastmcp.server import FastMCPServer, Tool
from typing import Dict, List, Any, Optional
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger

server = FastMCPServer(name="score-plugin", version="1.0.0")

@server.register
class ScorePlugin:
    class Meta:
        name = "score_plugin"
        description = "客户评分插件，根据多维度评估客户质量"
    
    @Tool(description="综合评估客户质量分数")
    def score_customer(self, company_name: str, website: str = "", emails: List[str] = [], 
                       phones: List[str] = [], industry: str = "", content: str = "") -> Dict[str, Any]:
        scores = {}
        
        scores["website_score"] = self._score_website(website)
        scores["contact_score"] = self._score_contacts(emails, phones)
        scores["industry_score"] = self._score_industry(industry, content)
        scores["company_score"] = self._score_company_name(company_name)
        
        total_score = sum(scores.values()) // len(scores)
        
        return {
            "company_name": company_name,
            "scores": scores,
            "total_score": total_score,
            "level": self._get_level(total_score),
            "recommendation": self._get_recommendation(total_score)
        }
    
    def _score_website(self, website: str) -> int:
        if not website:
            return 0
        
        score = 0
        
        if re.match(r'https?://', website):
            score += 20
        
        if '.' in website:
            parts = website.split('.')
            if len(parts) >= 2:
                score += 20
            
            tld = parts[-1].lower()
            if tld in ['com', 'net', 'org', 'io']:
                score += 10
            elif len(tld) == 2:
                score += 5
        
        if 'www.' in website.lower():
            score += 10
        
        if len(website) <= 50:
            score += 10
        
        return min(score, 100)
    
    def _score_contacts(self, emails: List[str], phones: List[str]) -> int:
        score = 0
        
        valid_emails = [e for e in emails if self._is_valid_email(e)]
        if valid_emails:
            score += 30 + min(len(valid_emails) * 10, 30)
        
        for email in valid_emails:
            if email.startswith(('info@', 'contact@', 'sales@', 'support@')):
                score += 10
            elif '@' in email and not email.startswith(('admin@', 'webmaster@')):
                score += 5
        
        if phones:
            score += min(len(phones) * 15, 30)
        
        return min(score, 100)
    
    def _is_valid_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _score_industry(self, industry: str, content: str) -> int:
        score = 0
        
        high_value_keywords = ["manufacturer", "factory", "supplier", "distributor", "wholesale", 
                              "retail", "importer", "exporter", "corporation", "inc", "limited"]
        
        if industry:
            score += 20
            for keyword in high_value_keywords:
                if keyword.lower() in industry.lower():
                    score += 10
        
        if content:
            content_lower = content.lower()
            for keyword in high_value_keywords:
                if keyword in content_lower:
                    score += 5
            
            employee_keywords = ["employees", "staff", "team", "people"]
            for keyword in employee_keywords:
                if keyword in content_lower:
                    score += 5
            
            revenue_keywords = ["revenue", "annual", "sales", "turnover"]
            for keyword in revenue_keywords:
                if keyword in content_lower:
                    score += 5
        
        return min(score, 100)
    
    def _score_company_name(self, company_name: str) -> int:
        score = 0
        
        if not company_name:
            return 0
        
        score += min(len(company_name) * 2, 30)
        
        suffixes = ["Inc", "Ltd", "Limited", "Corp", "Corporation", "Company", "Co"]
        for suffix in suffixes:
            if suffix.lower() in company_name.lower():
                score += 15
        
        if any(c.isupper() for c in company_name):
            score += 10
        
        if len(company_name.split()) >= 2:
            score += 10
        
        return min(score, 100)
    
    def _get_level(self, score: int) -> str:
        if score >= 80:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        else:
            return "D"
    
    def _get_recommendation(self, score: int) -> str:
        if score >= 80:
            return "高价值客户，优先开发，建议发送个性化开发信"
        elif score >= 60:
            return "中等价值客户，建议正常开发跟进"
        elif score >= 40:
            return "低价值客户，建议批量发送开发信"
        else:
            return "客户信息不足，建议进一步调研"
    
    @Tool(description="批量评估多个客户")
    def batch_score(self, customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for customer in customers:
            result = self.score_customer(
                company_name=customer.get("company_name", ""),
                website=customer.get("website", ""),
                emails=customer.get("emails", []),
                phones=customer.get("phones", []),
                industry=customer.get("industry", ""),
                content=customer.get("content", "")
            )
            results.append(result)
        return results

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8004)