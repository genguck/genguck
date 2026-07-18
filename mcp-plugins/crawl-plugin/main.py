from fastmcp.server import FastMCPServer, Tool
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger

server = FastMCPServer(name="crawl-plugin", version="1.0.0")

@server.register
class CrawlPlugin:
    class Meta:
        name = "crawl_plugin"
        description = "官网爬取与联系方式提取插件"
    
    @Tool(description="爬取网站首页内容")
    def crawl_website(self, url: str) -> Dict[str, Any]:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            title = soup.title.string if soup.title else ""
            meta_description = ""
            for meta in soup.find_all('meta'):
                if meta.get('name') == 'description':
                    meta_description = meta.get('content', '')
                    break
            
            text_content = soup.get_text(separator=' ', strip=True)[:5000]
            
            return {
                "url": url,
                "title": title,
                "description": meta_description,
                "content": text_content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"爬取网站失败 {url}: {e}")
            return {"url": url, "status": "failed", "error": str(e)}
    
    @Tool(description="从网站提取邮箱地址")
    def extract_emails(self, url: str) -> List[str]:
        try:
            content = self.crawl_website(url)
            if content.get("status") != "success":
                return []
            
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, content.get("content", ""))
            emails += re.findall(email_pattern, content.get("description", ""))
            
            emails = list(set(emails))
            
            return [e for e in emails if not e.startswith('//')]
        except Exception as e:
            logger.error(f"提取邮箱失败 {url}: {e}")
            return []
    
    @Tool(description="从网站提取电话号码")
    def extract_phones(self, url: str) -> List[str]:
        try:
            content = self.crawl_website(url)
            if content.get("status") != "success":
                return []
            
            phone_patterns = [
                r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                r'\+?86[-.\s]?1[3-9]\d{9}',
                r'1[3-9]\d{9}'
            ]
            
            phones = []
            for pattern in phone_patterns:
                phones.extend(re.findall(pattern, content.get("content", "")))
            
            phones = list(set(phones))
            
            return phones
        except Exception as e:
            logger.error(f"提取电话失败 {url}: {e}")
            return []
    
    @Tool(description="从网站提取联系人姓名")
    def extract_contacts(self, url: str) -> List[str]:
        try:
            content = self.crawl_website(url)
            if content.get("status") != "success":
                return []
            
            contact_keywords = ["contact", "about", "team", "staff", "people", "CEO", "manager", "director"]
            soup = BeautifulSoup(content.get("content", ""), 'lxml')
            
            contacts = []
            for keyword in contact_keywords:
                elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
                for element in elements:
                    parent = element.parent
                    if parent:
                        text = parent.get_text(strip=True)
                        name_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+)'
                        names = re.findall(name_pattern, text)
                        contacts.extend(names)
            
            contacts = list(set(contacts))
            return contacts[:10]
        except Exception as e:
            logger.error(f"提取联系人失败 {url}: {e}")
            return []
    
    @Tool(description="从网站提取社交媒体链接")
    def extract_social_links(self, url: str) -> Dict[str, str]:
        try:
            content = self.crawl_website(url)
            if content.get("status") != "success":
                return {}
            
            soup = BeautifulSoup(content.get("content", ""), 'lxml')
            
            social_patterns = {
                "linkedin": r'linkedin\.com',
                "twitter": r'twitter\.com|x\.com',
                "facebook": r'facebook\.com',
                "instagram": r'instagram\.com',
                "youtube": r'youtube\.com',
                "github": r'github\.com'
            }
            
            social_links = {}
            for link in soup.find_all('a', href=True):
                href = link['href']
                for platform, pattern in social_patterns.items():
                    if re.search(pattern, href, re.IGNORECASE):
                        social_links[platform] = href
                        break
            
            return social_links
        except Exception as e:
            logger.error(f"提取社交链接失败 {url}: {e}")
            return {}
    
    @Tool(description="完整提取网站所有联系信息")
    def extract_all_contacts(self, url: str) -> Dict[str, Any]:
        return {
            "url": url,
            "emails": self.extract_emails(url),
            "phones": self.extract_phones(url),
            "contacts": self.extract_contacts(url),
            "social_links": self.extract_social_links(url)
        }

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8003)