"""
谷歌地图商家信息采集插件 - 基于Google Places API
支持Text Search + Place Details两阶段抓取
"""
from fastmcp.server import FastMCPServer, Tool
from typing import Dict, List, Any, Optional
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.config import config
from utils.logger import logger

server = FastMCPServer(name="google-maps-plugin", version="1.0.0")


@server.register
class GoogleMapsPlugin:
    class Meta:
        name = "google_maps_plugin"
        description = "谷歌地图商家采集插件，支持按地区+行业搜索商家公开信息"

    # 国际区号映射表（E.164规范）
    COUNTRY_CALLING_CODES = {
        "美国": "+1", "美利坚": "+1", "USA": "+1", "US": "+1",
        "英国": "+44", "UK": "+44", "联合王国": "+44",
        "德国": "+49", "DE": "+49",
        "法国": "+33", "FR": "+33",
        "意大利": "+39", "IT": "+39",
        "西班牙": "+34", "ES": "+34",
        "荷兰": "+31", "NL": "+31",
        "比利时": "+32", "BE": "+32",
        "瑞士": "+41", "CH": "+41",
        "奥地利": "+43", "AT": "+43",
        "瑞典": "+46", "SE": "+46",
        "挪威": "+47", "NO": "+47",
        "丹麦": "+45", "DK": "+45",
        "芬兰": "+358", "FI": "+358",
        "波兰": "+48", "PL": "+48",
        "捷克": "+420", "CZ": "+420",
        "葡萄牙": "+351", "PT": "+351",
        "爱尔兰": "+353", "IE": "+353",
        "俄罗斯": "+7", "RU": "+7",
        "乌克兰": "+380", "UA": "+380",
        "土耳其": "+90", "TR": "+90",
        "以色列": "+972", "IL": "+972",
        "阿联酋": "+971", "UAE": "+971", "迪拜": "+971",
        "沙特": "+966", "沙特阿拉伯": "+966", "SA": "+966",
        "卡塔尔": "+974", "QA": "+974",
        "日本": "+81", "JP": "+81",
        "韩国": "+82", "KR": "+82",
        "泰国": "+66", "TH": "+66",
        "越南": "+84", "VN": "+84",
        "马来西亚": "+60", "MY": "+60",
        "新加坡": "+65", "SG": "+65",
        "印度尼西亚": "+62", "ID": "+62",
        "菲律宾": "+63", "PH": "+63",
        "印度": "+91", "IN": "+91",
        "巴基斯坦": "+92", "PK": "+92",
        "孟加拉": "+880", "BD": "+880",
        "澳大利亚": "+61", "AU": "+61",
        "新西兰": "+64", "NZ": "+64",
        "巴西": "+55", "BR": "+55",
        "墨西哥": "+52", "MX": "+52",
        "阿根廷": "+54", "AR": "+54",
        "智利": "+56", "CL": "+56",
        "哥伦比亚": "+57", "CO": "+57",
        "秘鲁": "+51", "PE": "+51",
        "南非": "+27", "ZA": "+27",
        "尼日利亚": "+234", "NG": "+234",
        "埃及": "+20", "EG": "+20",
        "肯尼亚": "+254", "KE": "+254",
        "加拿大": "+1", "CA": "+1",
    }

    # 各国外贸核心城市（仅给国家时使用）
    COUNTRY_CORE_CITIES = {
        "美国": ["Los Angeles", "New York", "Miami"],
        "英国": ["London", "Manchester", "Birmingham"],
        "德国": ["Hamburg", "Frankfurt", "Dusseldorf"],
        "法国": ["Paris", "Lyon", "Marseille"],
        "日本": ["Tokyo", "Osaka", "Yokohama"],
        "韩国": ["Seoul", "Busan", "Incheon"],
        "泰国": ["Bangkok", "Chiang Mai", "Pattaya"],
        "马来西亚": ["Kuala Lumpur", "Penang", "Johor Bahru"],
        "越南": ["Ho Chi Minh City", "Hanoi", "Da Nang"],
        "印度尼西亚": ["Jakarta", "Surabaya", "Bandung"],
        "印度": ["Mumbai", "Delhi", "Bangalore"],
        "澳大利亚": ["Sydney", "Melbourne", "Brisbane"],
        "巴西": ["Sao Paulo", "Rio de Janeiro", "Curitiba"],
        "墨西哥": ["Mexico City", "Guadalajara", "Monterrey"],
        "加拿大": ["Toronto", "Vancouver", "Montreal"],
        "阿联酋": ["Dubai", "Abu Dhabi", "Sharjah"],
        "南非": ["Johannesburg", "Cape Town", "Durban"],
    }

    @Tool(description="搜索谷歌地图商家信息（Text Search + Place Details）")
    def search_places(self, query: str, location: str = "",
                      country: str = "", city: str = "",
                      radius: int = 50000, count: int = 20,
                      only_with_phone: bool = False,
                      filter_closed: bool = True,
                      need_website: bool = False,
                      language: str = "zh-CN") -> List[Dict[str, Any]]:
        """
        搜索谷歌地图商家信息
        query: 行业关键词（如 clothing wholesale）
        location: 完整地理位置描述
        country: 国家
        city: 城市
        radius: 搜索半径（米），默认50km
        count: 返回结果数量上限
        only_with_phone: 是否只返回有电话的商家
        filter_closed: 是否过滤已关闭商家
        need_website: 是否只返回有官网的商家
        """
        api_key = os.getenv('GOOGLE_MAPS_API_KEY',
                            config.google_maps.get('api_key', '') or config.search.get('google_api_key', ''))

        if not api_key:
            logger.error("Google Maps API Key 未配置")
            return []

        # 构建搜索查询
        search_query = query
        if location:
            search_query = f"{query} in {location}"
        elif city and country:
            search_query = f"{query} in {city}, {country}"
        elif country:
            search_query = f"{query} in {country}"

        logger.info(f"谷歌地图搜索: {search_query}")

        # 第一阶段：Text Search
        place_ids = self._text_search(api_key, search_query, radius, language)
        if not place_ids:
            logger.warning(f"未找到匹配商家: {search_query}")
            return []

        # 第二阶段：Place Details 逐个获取详细信息
        results = []
        for pid in place_ids[:count]:
            detail = self._place_details(api_key, pid, language)
            if not detail:
                continue

            # 过滤已关闭商家
            if filter_closed and detail.get("business_status") == "CLOSED_PERMANENTLY":
                continue

            # 过滤无电话
            if only_with_phone and not detail.get("phone"):
                continue

            # 过滤无网站
            if need_website and not detail.get("website"):
                continue

            results.append(detail)

            if len(results) >= count:
                break

        logger.info(f"抓取完成: 共 {len(results)} 条有效商家")
        return results

    @Tool(description="获取商家详细信息")
    def get_place_detail(self, place_id: str,
                         language: str = "zh-CN") -> Dict[str, Any]:
        """根据place_id获取商家详细信息"""
        api_key = os.getenv('GOOGLE_MAPS_API_KEY',
                            config.google_maps.get('api_key', '') or config.search.get('google_api_key', ''))
        if not api_key:
            return {}
        return self._place_details(api_key, place_id, language)

    @Tool(description="获取国家对应的国际区号")
    def get_country_code(self, country: str) -> str:
        """获取国家对应国际电话区号"""
        return self.COUNTRY_CALLING_CODES.get(country, "")

    @Tool(description="获取国家的外贸核心城市列表")
    def get_core_cities(self, country: str) -> List[str]:
        """获取指定国家的外贸核心城市"""
        return self.COUNTRY_CORE_CITIES.get(country, [])

    def _text_search(self, api_key: str, query: str,
                     radius: int, language: str) -> List[str]:
        """Google Places Text Search - 获取place_id列表"""
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "key": api_key,
            "language": language,
            "radius": radius,
        }

        place_ids = []
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK" and data.get("status") != "ZERO_RESULTS":
                logger.error(f"Text Search API错误: {data.get('status')} - {data.get('error_message', '')}")
                return []

            for result in data.get("results", []):
                pid = result.get("place_id")
                if pid:
                    place_ids.append(pid)

            # 处理分页 (next_page_token)
            next_token = data.get("next_page_token")
            page_count = 1
            while next_token and page_count < 3:  # 最多3页
                import time
                time.sleep(2)  # Google要求延迟
                params["pagetoken"] = next_token
                try:
                    resp = requests.get(url, params=params, timeout=30)
                    resp.raise_for_status()
                    page_data = resp.json()
                    for result in page_data.get("results", []):
                        pid = result.get("place_id")
                        if pid:
                            place_ids.append(pid)
                    next_token = page_data.get("next_page_token")
                    page_count += 1
                except Exception as e:
                    logger.error(f"分页请求失败: {e}")
                    break

        except Exception as e:
            logger.error(f"Text Search请求失败: {e}")
            return []

        return place_ids

    def _place_details(self, api_key: str, place_id: str,
                       language: str) -> Dict[str, Any]:
        """Google Places Details - 获取商家完整信息"""
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "key": api_key,
            "language": language,
            "fields": "name,formatted_phone_number,international_phone_number,"
                      "formatted_address,address_component,"
                      "geometry,business_status,rating,user_ratings_total,"
                      "website,url,types,opening_hours"
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK":
                logger.error(f"Place Details API错误: {data.get('status')}")
                return {}

            result = data.get("result", {})

            # 提取邮编
            postal_code = ""
            for comp in result.get("address_components", []):
                if "postal_code" in comp.get("types", []):
                    postal_code = comp.get("long_name", "")
                    break

            # 营业状态
            business_status = result.get("business_status", "")
            if business_status == "OPERATIONAL":
                status_cn = "营业中"
            elif business_status == "CLOSED_PERMANENTLY":
                status_cn = "已永久关闭"
            elif business_status == "CLOSED_TEMPORARILY":
                status_cn = "临时关闭"
            else:
                status_cn = "未知"

            # 经营类型（中文映射）
            types_cn = self._translate_types(result.get("types", []))

            return {
                "place_id": place_id,
                "name": result.get("name", ""),
                "phone": result.get("international_phone_number",
                                   result.get("formatted_phone_number", "")),
                "phone_formatted": result.get("formatted_phone_number", ""),
                "address": result.get("formatted_address", ""),
                "postal_code": postal_code,
                "lat": result.get("geometry", {}).get("location", {}).get("lat", 0),
                "lng": result.get("geometry", {}).get("location", {}).get("lng", 0),
                "business_status": business_status,
                "business_status_cn": status_cn,
                "rating": result.get("rating", 0),
                "user_ratings_total": result.get("user_ratings_total", 0),
                "website": result.get("website", ""),
                "google_maps_url": result.get("url", ""),
                "types": result.get("types", []),
                "types_cn": types_cn,
                "opening_hours": result.get("opening_hours", {}),
            }

        except Exception as e:
            logger.error(f"Place Details请求失败: {e}")
            return {}

    def _translate_types(self, types: List[str]) -> str:
        """将Google Places type映射为中文行业描述"""
        type_map = {
            "clothing_store": "服装", "shoe_store": "鞋类",
            "electronics_store": "电子产品", "furniture_store": "家具",
            "home_goods_store": "家居用品", "department_store": "百货",
            "wholesaler": "批发", "store": "零售",
            "logistics": "物流", "moving_company": "搬运/物流",
            "warehouse": "仓储", "storage": "仓储",
            "freight_forwarder": "货代",
            "shipping_company": "海运",
            "import_export": "进出口贸易",
            "textile": "纺织", "fabric": "面料",
            "food": "食品", "restaurant": "餐饮",
            "car_dealer": "汽车经销商", "car_rental": "汽车租赁",
            "car_repair": "汽车维修", "gas_station": "加油站",
            "hardware_store": "五金", "building_materials": "建材",
            "plumber": "管道", "electrician": "电气",
            "real_estate_agency": "房地产", "insurance_agency": "保险",
            "travel_agency": "旅行社", "accounting": "会计",
            "lawyer": "法律", "bank": "银行",
            "health": "医疗健康", "pharmacy": "药房",
            "hospital": "医院", "dentist": "牙科",
            "beauty_salon": "美容", "hair_care": "美发",
            "spa": "水疗", "gym": "健身",
            "school": "教育", "university": "大学",
            "local_government_office": "政府机构",
            "place_of_worship": "宗教场所",
            "parking": "停车场", "park": "公园",
            "shopping_mall": "购物中心", "supermarket": "超市",
            "convenience_store": "便利店",
            "general_contractor": "承包商",
            "establishment": "商户", "point_of_interest": "地点",
        }
        translated = []
        for t in types:
            cn = type_map.get(t)
            if cn:
                translated.append(cn)
        return "、".join(translated) if translated else "未分类"


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8006)
