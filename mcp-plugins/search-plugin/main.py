from fastmcp.server import FastMCPServer, Tool
from typing import Dict, List, Any, Optional
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.config import config
from utils.logger import logger

server = FastMCPServer(name="search-plugin", version="1.0.0")

@server.register
class SearchPlugin:
    class Meta:
        name = "search_plugin"
        description = "客户搜索插件，支持Web搜索引擎搜索潜在客户"
    
    @Tool(description="使用搜索引擎搜索客户")
    def search_customers(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        results = []
        
        serp_api_key = config.search.get('serp_api_key')
        if serp_api_key:
            results = self._search_with_serpapi(query, count)
        else:
            google_api_key = config.search.get('google_api_key')
            google_cse_id = config.search.get('google_cse_id')
            if google_api_key and google_cse_id:
                results = self._search_with_google(query, count)
            else:
                results = self._search_with_bing(query, count)
        
        return results
    
    def _search_with_serpapi(self, query: str, count: int) -> List[Dict[str, Any]]:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": config.search['serp_api_key'],
            "num": count,
            "engine": "google"
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            results = []
            for result in data.get('organic_results', []):
                results.append({
                    "title": result.get('title', ''),
                    "link": result.get('link', ''),
                    "snippet": result.get('snippet', ''),
                    "source": "serpapi"
                })
            return results[:count]
        except Exception as e:
            logger.error(f"SerpAPI搜索失败: {e}")
            return []
    
    def _search_with_google(self, query: str, count: int) -> List[Dict[str, Any]]:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": config.search['google_api_key'],
            "cx": config.search['google_cse_id'],
            "num": min(count, 10)
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data.get('items', []):
                results.append({
                    "title": item.get('title', ''),
                    "link": item.get('link', ''),
                    "snippet": item.get('snippet', ''),
                    "source": "google"
                })
            return results
        except Exception as e:
            logger.error(f"Google搜索失败: {e}")
            return []
    
    def _search_with_bing(self, query: str, count: int) -> List[Dict[str, Any]]:
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": config.search.get('bing_api_key', '')}
        params = {
            "q": query,
            "count": count
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            results = []
            for result in data.get('webPages', {}).get('value', []):
                results.append({
                    "title": result.get('name', ''),
                    "link": result.get('url', ''),
                    "snippet": result.get('snippet', ''),
                    "source": "bing"
                })
            return results
        except Exception as e:
            logger.error(f"Bing搜索失败: {e}")
            return []
    
    @Tool(description="搜索LinkedIn上的公司和联系人")
    def search_linkedin(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        url = "https://serpapi.com/search"
        params = {
            "q": f"{query} site:linkedin.com",
            "api_key": config.search.get('serp_api_key', ''),
            "num": count,
            "engine": "google"
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            results = []
            for result in data.get('organic_results', []):
                results.append({
                    "title": result.get('title', ''),
                    "link": result.get('link', ''),
                    "snippet": result.get('snippet', ''),
                    "source": "linkedin"
                })
            return results[:count]
        except Exception as e:
            logger.error(f"LinkedIn搜索失败: {e}")
            return []
    
    @Tool(description="搜索行业相关的B2B平台")
    def search_b2b_platforms(self, industry: str, count: int = 10) -> List[Dict[str, Any]]:
        platforms = ["alibaba.com", "made-in-china.com", "globalsources.com", "ec21.com"]
        all_results = []
        
        for platform in platforms:
            query = f"{industry} site:{platform}"
            results = self.search_customers(query, count // len(platforms))
            all_results.extend(results)
        
        return all_results[:count]

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8002)