"""
谷歌地图全球外贸商家线索采集 & WhatsApp建联智能体
功能：解析自然语言 → 调用Google Places API → 提取商家信息 → WhatsApp链接生成 → 格式化输出
"""
from typing import Dict, List, Any, Optional, Tuple
import re
import json
import sys
import os
import csv
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger


class InstructionParser:
    """自然语言指令解析器 - 自动识别地理范围、行业关键词、筛选条件"""

    # 国家-城市映射
    COUNTRY_KEYWORDS = {
        "美国": ["美国", "美利坚", "USA", "US", "United States", "美国本土"],
        "英国": ["英国", "UK", "United Kingdom", "联合王国", "英格兰"],
        "德国": ["德国", "DE", "Germany", "德意志"],
        "法国": ["法国", "FR", "France", "法兰西"],
        "意大利": ["意大利", "IT", "Italy"],
        "西班牙": ["西班牙", "ES", "Spain"],
        "荷兰": ["荷兰", "NL", "Netherlands", "Holland"],
        "比利时": ["比利时", "BE", "Belgium"],
        "瑞士": ["瑞士", "CH", "Switzerland"],
        "奥地利": ["奥地利", "AT", "Austria"],
        "瑞典": ["瑞典", "SE", "Sweden"],
        "挪威": ["挪威", "NO", "Norway"],
        "丹麦": ["丹麦", "DK", "Denmark"],
        "芬兰": ["芬兰", "FI", "Finland"],
        "波兰": ["波兰", "PL", "Poland"],
        "捷克": ["捷克", "CZ", "Czech"],
        "葡萄牙": ["葡萄牙", "PT", "Portugal"],
        "爱尔兰": ["爱尔兰", "IE", "Ireland"],
        "俄罗斯": ["俄罗斯", "RU", "Russia"],
        "土耳其": ["土耳其", "TR", "Turkey", "Türkiye"],
        "以色列": ["以色列", "IL", "Israel"],
        "阿联酋": ["阿联酋", "UAE", "迪拜", "Dubai", "United Arab Emirates"],
        "沙特": ["沙特", "沙特阿拉伯", "SA", "Saudi Arabia"],
        "日本": ["日本", "JP", "Japan"],
        "韩国": ["韩国", "KR", "Korea", "南韩"],
        "泰国": ["泰国", "TH", "Thailand"],
        "越南": ["越南", "VN", "Vietnam"],
        "马来西亚": ["马来西亚", "MY", "Malaysia", "大马"],
        "新加坡": ["新加坡", "SG", "Singapore"],
        "印度尼西亚": ["印度尼西亚", "ID", "Indonesia", "印尼"],
        "菲律宾": ["菲律宾", "PH", "Philippines"],
        "印度": ["印度", "IN", "India"],
        "巴基斯坦": ["巴基斯坦", "PK", "Pakistan"],
        "澳大利亚": ["澳大利亚", "AU", "Australia", "澳洲"],
        "新西兰": ["新西兰", "NZ", "New Zealand"],
        "巴西": ["巴西", "BR", "Brazil"],
        "墨西哥": ["墨西哥", "MX", "Mexico"],
        "阿根廷": ["阿根廷", "AR", "Argentina"],
        "智利": ["智利", "CL", "Chile"],
        "哥伦比亚": ["哥伦比亚", "CO", "Colombia"],
        "南非": ["南非", "ZA", "South Africa"],
        "尼日利亚": ["尼日利亚", "NG", "Nigeria"],
        "埃及": ["埃及", "EG", "Egypt"],
        "加拿大": ["加拿大", "CA", "Canada"],
    }

    # 行业关键词中英文映射
    INDUSTRY_KEYWORDS = {
        "服装批发": ["服装批发", "服装批发商", "clothing wholesale", "garment wholesale", "apparel wholesale", "服装市场", "时装批发"],
        "电子产品": ["电子产品", "电子供应商", "electronics supplier", "electronics wholesale", "电子批发"],
        "海运货代": ["海运货代", "海运", "货代", "freight forwarder", "shipping agent", "ocean freight", "海运代理"],
        "拼箱货代": ["拼箱货代", "LCL", "less than container", "海运拼箱"],
        "物流": ["物流", "logistics", "cargo", "货运", "运输"],
        "海外仓": ["海外仓", "一件代发", "warehouse", "fulfillment", "海外仓储", "dropshipping"],
        "OOCL物流": ["OOCL", "东方海外", "OOCL logistics"],
        "建材": ["建材", "building materials", "construction materials", "建筑材料"],
        "五金": ["五金", "hardware", "五金工具"],
        "机械": ["机械", "machinery", "工业机械", "设备"],
        "化工": ["化工", "chemical", "化学品", "化工原料"],
        "食品": ["食品", "food", "食品批发", "食品供应商"],
        "纺织": ["纺织", "textile", "面料", "fabric", "纺织面料"],
        "鞋类": ["鞋类", "shoes", "鞋批发", "footwear"],
        "家居": ["家居", "home goods", "furniture", "家具", "家居用品"],
        "汽车配件": ["汽车配件", "auto parts", "汽车零部件", "car parts"],
        "玩具": ["玩具", "toys", "玩具批发"],
        "珠宝": ["珠宝", "jewelry", "首饰", "jewellery"],
        "化妆品": ["化妆品", "cosmetics", "beauty products", "美妆"],
        "手机配件": ["手机配件", "phone accessories", "mobile accessories"],
        "LED照明": ["LED", "lighting", "照明", "灯具"],
        "太阳能": ["太阳能", "solar", "光伏"],
        "医疗器械": ["医疗器械", "medical devices", "医疗设备"],
        "包装": ["包装", "packaging", "包装材料"],
    }

    # 外贸相关主体类型标记
    TRADE_TYPE_KEYWORDS = {
        "工厂": ["factory", "工厂", "manufacturing", "manufacturer", "制造商", "生产"],
        "贸易商行": ["trading", "trade", "贸易", "import export", "进出口", "trading company"],
        "批发档口": ["wholesale", "批发", "批发商", "wholesaler", "市场档口", "market stall"],
        "物流仓储": ["warehouse", "logistics", "仓储", "货代", "freight", "shipping"],
    }

    def parse(self, instruction: str) -> Dict[str, Any]:
        """
        解析自然语言指令，提取三个核心要素
        返回: {
            country: str,        # 国家
            city: str,           # 城市
            district: str,       # 行政区/商圈
            radius_km: int,      # 搜索半径(公里)
            industry: str,       # 行业关键词
            industry_en: str,    # 行业英文关键词(用于API搜索)
            count: int,          # 条数上限
            only_with_phone: bool,  # 是否只要带电话商家
            filter_closed: bool,    # 是否过滤停业店铺
            need_website: bool,     # 是否需要官网链接
            missing: List[str],     # 缺失要素列表
            trade_types: List[str], # 外贸主体类型
        }
        """
        result = {
            "country": "",
            "city": "",
            "district": "",
            "radius_km": 50,
            "industry": "",
            "industry_en": "",
            "count": 20,
            "only_with_phone": False,
            "filter_closed": True,
            "need_website": False,
            "missing": [],
            "trade_types": [],
        }

        # 解析地理范围
        country, city, district = self._parse_location(instruction)
        result["country"] = country
        result["city"] = city
        result["district"] = district

        # 解析搜索半径
        radius_match = re.search(r'(\d+)\s*公里|(\d+)\s*km|(\d+)\s*KM', instruction)
        if radius_match:
            km = radius_match.group(1) or radius_match.group(2) or radius_match.group(3)
            result["radius_km"] = int(km)

        # 解析行业关键词
        industry, industry_en = self._parse_industry(instruction)
        result["industry"] = industry
        result["industry_en"] = industry_en

        # 解析条数上限
        count_match = re.search(r'最多\s*(\d+)\s*条|(\d+)\s*条|(\d+)\s*家|(\d+)\s*个', instruction)
        if count_match:
            for g in count_match.groups():
                if g:
                    result["count"] = int(g)
                    break

        # 解析筛选条件
        if "只" in instruction and ("电话" in instruction or "号码" in instruction or "WhatsApp" in instruction or "whatsapp" in instruction.lower()):
            result["only_with_phone"] = True
        if "不过滤" in instruction or "包含停业" in instruction or "包括停业" in instruction:
            result["filter_closed"] = False
        if "需要官网" in instruction or "要官网" in instruction or "带官网" in instruction:
            result["need_website"] = True

        # 解析外贸主体类型
        result["trade_types"] = self._parse_trade_types(instruction)

        # 检查缺失要素
        if not result["country"]:
            result["missing"].append("地理范围（国家/城市）")
        if not result["industry"]:
            result["missing"].append("行业关键词")

        return result

    def _parse_location(self, instruction: str) -> Tuple[str, str, str]:
        """解析地理位置：国家→城市→行政区/商圈"""
        country = ""
        city = ""
        district = ""

        # 匹配国家
        for cn_name, keywords in self.COUNTRY_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in instruction.lower():
                    country = cn_name
                    break
            if country:
                break

        # 匹配城市（从指令中提取"XX国家XX城市"模式后的城市名）
        # 常见城市名映射
        city_map = {
            "洛杉矶": "Los Angeles", "洛杉矶": "Los Angeles",
            "纽约": "New York", "纽约": "New York",
            "迈阿密": "Miami", "迈阿密": "Miami",
            "芝加哥": "Chicago", "芝加哥": "Chicago",
            "休斯顿": "Houston", "休斯顿": "Houston",
            "旧金山": "San Francisco", "旧金山": "San Francisco",
            "西雅图": "Seattle", "西雅图": "Seattle",
            "达拉斯": "Dallas", "达拉斯": "Dallas",
            "伦敦": "London", "伦敦": "London",
            "曼彻斯特": "Manchester", "曼彻斯特": "Manchester",
            "伯明翰": "Birmingham", "伯明翰": "Birmingham",
            "汉堡": "Hamburg", "汉堡": "Hamburg",
            "法兰克福": "Frankfurt", "法兰克福": "Frankfurt",
            "慕尼黑": "Munich", "慕尼黑": "Munich",
            "巴黎": "Paris", "巴黎": "Paris",
            "东京": "Tokyo", "东京": "Tokyo",
            "大阪": "Osaka", "大阪": "Osaka",
            "首尔": "Seoul", "首尔": "Seoul",
            "釜山": "Busan", "釜山": "Busan",
            "曼谷": "Bangkok", "曼谷": "Bangkok",
            "吉隆坡": "Kuala Lumpur", "吉隆坡": "Kuala Lumpur",
            "胡志明": "Ho Chi Minh City", "胡志明市": "Ho Chi Minh City",
            "河内": "Hanoi", "河内": "Hanoi",
            "雅加达": "Jakarta", "雅加达": "Jakarta",
            "孟买": "Mumbai", "孟买": "Mumbai",
            "德里": "Delhi", "新德里": "New Delhi",
            "迪拜": "Dubai", "迪拜": "Dubai",
            "悉尼": "Sydney", "悉尼": "Sydney",
            "墨尔本": "Melbourne", "墨尔本": "Melbourne",
            "多伦多": "Toronto", "多伦多": "Toronto",
            "温哥华": "Vancouver", "温哥华": "Vancouver",
            "圣保罗": "Sao Paulo", "圣保罗": "Sao Paulo",
            "墨西哥城": "Mexico City", "墨西哥城": "Mexico City",
            "约翰内斯堡": "Johannesburg", "约翰内斯堡": "Johannesburg",
            "开普敦": "Cape Town", "开普敦": "Cape Town",
        }

        for cn_name, en_name in city_map.items():
            if cn_name in instruction:
                city = en_name
                break

        # 如果指令中有英文城市名，也尝试匹配
        if not city:
            # 直接在指令中搜索常见英文城市名
            common_cities = [
                "Los Angeles", "New York", "Miami", "Chicago", "Houston",
                "San Francisco", "Seattle", "London", "Manchester", "Birmingham",
                "Hamburg", "Frankfurt", "Munich", "Paris", "Tokyo", "Osaka",
                "Seoul", "Busan", "Bangkok", "Kuala Lumpur", "Jakarta",
                "Mumbai", "Delhi", "Dubai", "Sydney", "Melbourne",
                "Toronto", "Vancouver", "Sao Paulo", "Mexico City",
            ]
            for c in common_cities:
                if c.lower() in instruction.lower():
                    city = c
                    break

        # 提取行政区/商圈（通常在"XX区"、"XX商圈"、"XX市场"附近）
        district_match = re.search(r'([\u4e00-\u9fff]{2,6}(?:区|商圈|市场|工业园|产业区|开发区))', instruction)
        if district_match:
            district = district_match.group(1)

        return country, city, district

    def _parse_industry(self, instruction: str) -> Tuple[str, str]:
        """解析行业关键词，返回(中文, 英文)"""
        for cn_name, keywords in self.INDUSTRY_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in instruction.lower():
                    # 返回中文行业名和第一个英文关键词
                    en_kw = ""
                    for k in keywords:
                        if re.match(r'^[a-zA-Z]', k):
                            en_kw = k
                            break
                    return cn_name, en_kw or cn_name
        return "", ""

    def _parse_trade_types(self, instruction: str) -> List[str]:
        """解析外贸主体类型"""
        found = []
        for trade_type, keywords in self.TRADE_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in instruction.lower():
                    found.append(trade_type)
                    break
        return found

    def format_missing_question(self, missing: List[str]) -> str:
        """生成缺失要素的反问提示"""
        if not missing:
            return ""
        parts = "、".join(missing)
        return f"请补充以下信息：{parts}。例如：美国洛杉矶服装批发商家，最多10条"


class WhatsAppProcessor:
    """WhatsApp号码处理与格式化模块"""

    # 座机号特征模式（按国家区号区分）
    LANDLINE_PATTERNS = {
        "+1": [  # 美国/加拿大座机：区号+7位号码
            # 美国常见座机区号前缀（非穷举，主要大城市）
        ],
    }

    # 移动号段模式（部分国家手机号前缀）
    MOBILE_PREFIXES = {
        "+1": [""],  # 美国手机号与座机格式相同，无法区分，默认判定为可WhatsApp
        "+44": ["7"],  # 英国手机号以7开头
        "+49": ["15", "16", "17"],  # 德国手机号
        "+33": ["6", "7"],  # 法国手机号
        "+81": ["70", "80", "90"],  # 日本手机号
        "+82": ["10"],  # 韩国手机号
        "+66": ["8", "9"],  # 泰国手机号
        "+60": ["1"],  # 马来西亚手机号
        "+65": ["8", "9"],  # 新加坡手机号
        "+91": ["9", "8", "7", "6"],  # 印度手机号
        "+61": ["4"],  # 澳大利亚手机号
        "+55": ["9"],  # 巴西手机号
        "+52": ["1"],  # 墨西哥手机号
        "+971": ["5"],  # 阿联酋手机号
        "+27": ["6", "7", "8"],  # 南非手机号
        "+7": ["9"],  # 俄罗斯手机号
        "+90": ["5"],  # 土耳其手机号
    }

    def process_phone(self, phone: str, country: str = "") -> Dict[str, Any]:
        """
        处理单个电话号码，返回格式化结果
        返回: {
            original: str,          # 原始号码
            clean: str,             # 清洗后纯数字(带区号)
            international: str,     # 国际标准格式 +XXXXXXXXXXX
            whatsapp_link: str,     # wa.me链接
            is_mobile: bool,        # 是否为手机号(可WhatsApp)
            whatsapp_available: str, # WhatsApp可用性标注
            note: str,              # 备注
        }
        """
        if not phone or not phone.strip():
            return {
                "original": "",
                "clean": "",
                "international": "",
                "whatsapp_link": "",
                "is_mobile": False,
                "whatsapp_available": "【无联系电话，无法WhatsApp建联】",
                "note": "无公开电话号码",
            }

        original = phone.strip()
        clean = self._clean_phone(original)
        international = self._format_international(clean)
        is_mobile = self._is_mobile_number(clean)
        whatsapp_link = self._generate_wa_link(clean)

        # 按规则：所有境外手机号默认判定为可WhatsApp添加
        if is_mobile:
            whatsapp_available = "可WhatsApp添加"
            note = "WhatsApp优先沟通、海外客户常用触达方式"
        else:
            # 座机号不标注WhatsApp
            whatsapp_available = ""
            note = "座机号码，不可WhatsApp"

        return {
            "original": original,
            "clean": clean,
            "international": international,
            "whatsapp_link": whatsapp_link,
            "is_mobile": is_mobile,
            "whatsapp_available": whatsapp_available,
            "note": note,
        }

    def process_business_phones(self, phone_str: str, country: str = "") -> List[Dict[str, Any]]:
        """
        处理商家所有电话号码（可能多条，用逗号或分号分隔）
        返回每条号码的完整处理结果列表
        """
        if not phone_str or not phone_str.strip():
            return [self.process_phone("", country)]

        # 分割多条号码
        phones = re.split(r'[,;，；\n]', phone_str)
        results = []
        for p in phones:
            p = p.strip()
            if p:
                results.append(self.process_phone(p, country))

        return results if results else [self.process_phone("", country)]

    def _clean_phone(self, phone: str) -> str:
        """清洗电话号码：去除横杠、空格、括号，仅保留+和纯数字"""
        # 先保留加号
        cleaned = re.sub(r'[^\d+]', '', phone)
        return cleaned

    def _format_international(self, clean_phone: str) -> str:
        """格式化为国际标准格式"""
        if not clean_phone:
            return ""
        # 确保以+开头
        if not clean_phone.startswith('+'):
            return f"+{clean_phone}"
        return clean_phone

    def _is_mobile_number(self, clean_phone: str) -> bool:
        """
        判断是否为手机号
        规则：所有带国际区号的境外手机号，默认判定可直接用于WhatsApp添加
        无法确定座机/手机的情况下，默认判定为可WhatsApp（按需求规则）
        """
        if not clean_phone:
            return False

        # 去掉+号
        digits = clean_phone.lstrip('+')

        if len(digits) < 7:
            return False

        # 检查是否匹配已知手机号前缀
        for country_code, prefixes in self.MOBILE_PREFIXES.items():
            code_digits = country_code.lstrip('+')
            if digits.startswith(code_digits):
                remaining = digits[len(code_digits):]
                for prefix in prefixes:
                    if prefix and remaining.startswith(prefix):
                        return True
                # 如果该国家区号在列表中但无明确手机前缀，
                # 默认判定为可WhatsApp（按需求规则：所有境外手机号默认判定）
                return True

        # 其他情况：如果有国际区号（+开头），默认判定可WhatsApp
        if clean_phone.startswith('+'):
            return True

        return True  # 按需求规则，默认判定

    def _generate_wa_link(self, clean_phone: str) -> str:
        """
        生成WhatsApp一键添加链接
        模板：https://wa.me/国际区号去掉加号+纯手机号
        举例：+1 323-588-1222 → https://wa.me/13235881222
        """
        if not clean_phone:
            return ""

        # 去掉所有非数字字符（包括+号）
        digits = re.sub(r'[^\d]', '', clean_phone)

        if not digits:
            return ""

        return f"https://wa.me/{digits}"


class DataCleaner:
    """数据清洗与去重模块"""

    def deduplicate(self, businesses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重：重复店名+重复地址自动合并
        """
        seen = set()
        unique = []
        for biz in businesses:
            name = biz.get("name", "").strip().lower()
            address = biz.get("address", "").strip().lower()
            key = f"{name}|{address}"
            if key not in seen:
                seen.add(key)
                unique.append(biz)
        return unique

    def filter_noise(self, businesses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤导航、评论数、保存、分享等无效页面文字"""
        noise_keywords = ["导航", "评论数", "保存", "分享", "directions",
                          "reviews", "save", "share"]
        filtered = []
        for biz in businesses:
            name = biz.get("name", "")
            is_noise = False
            for kw in noise_keywords:
                if kw in name:
                    is_noise = True
                    break
            if not is_noise:
                filtered.append(biz)
        return filtered

    def sort_by_trade_relevance(self, businesses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        外贸行业增强排序：
        货代、物流、服装批发市场档口结果靠前排序
        区分工厂、贸易商行、实体批发档口主体类型
        """

        def trade_score(biz: Dict[str, Any]) -> int:
            score = 0
            types_cn = biz.get("types_cn", "").lower()
            name = biz.get("name", "").lower()
            types = biz.get("types", [])

            # 货代/物流优先
            if any(k in types_cn for k in ["货代", "物流", "海运", "仓储"]):
                score += 100
            if any(k in name for k in ["freight", "logistics", "shipping", "cargo", "forwarder"]):
                score += 100

            # 批发优先
            if "批发" in types_cn or "wholesale" in name:
                score += 80

            # 进出口贸易
            if "进出口" in types_cn or "import" in name or "export" in name or "trading" in name:
                score += 70

            # 工厂
            if any(k in name for k in ["factory", "manufacturing", "manufacturer", "工厂", "制造"]):
                score += 50
                biz["_trade_type"] = "工厂"

            # 贸易商行
            if any(k in name for k in ["trading", "trade", "import", "export", "贸易", "进出口"]):
                score += 50
                if "_trade_type" not in biz:
                    biz["_trade_type"] = "贸易商行"

            # 批发档口
            if any(k in name for k in ["wholesale", "market", "批发", "市场", "档口"]):
                score += 50
                if "_trade_type" not in biz:
                    biz["_trade_type"] = "批发档口"

            # 外贸相关标记
            if any(k in types_cn for k in ["批发", "仓储", "物流", "进出口", "海运"]):
                biz["_trade_tag"] = True

            # 有电话号码加分
            if biz.get("phone"):
                score += 10

            # 有官网加分
            if biz.get("website"):
                score += 5

            # 评分加分
            rating = biz.get("rating", 0)
            if rating:
                score += int(rating * 2)

            return score

        for biz in businesses:
            biz["_sort_score"] = trade_score(biz)

        businesses.sort(key=lambda x: x.get("_sort_score", 0), reverse=True)
        return businesses


class OutputFormatter:
    """输出格式化模块 - Markdown表格 + CSV + 外贸小贴士"""

    def format_markdown_table(self, businesses: List[Dict[str, Any]],
                              wa_processor: WhatsAppProcessor) -> str:
        """
        生成Markdown正式表格
        表头：序号｜商家名称｜完整联系电话｜WhatsApp直达链接｜详细地址｜主营业务｜谷歌地图链接｜评分&营业状态
        """
        if not businesses:
            return "该区域无公开可抓取商户。"

        lines = []
        lines.append("| 序号 | 商家名称 | 完整联系电话 | WhatsApp直达链接 | 详细地址 | 主营业务 | 谷歌地图链接 | 评分&营业状态 |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")

        for idx, biz in enumerate(businesses, 1):
            name = biz.get("name", "")
            phone = biz.get("phone", "")
            address = biz.get("address", "")
            if biz.get("postal_code"):
                address += f" {biz['postal_code']}"
            types_cn = biz.get("types_cn", "")
            maps_url = biz.get("google_maps_url", "")
            rating = biz.get("rating", 0)
            status_cn = biz.get("business_status_cn", "")
            rating_status = f"{rating}分 {status_cn}" if rating else status_cn

            # 处理电话和WhatsApp链接
            if phone:
                wa_results = wa_processor.process_business_phones(phone)
                # 展开多条号码
                phone_display_parts = []
                wa_link_parts = []
                for wa in wa_results:
                    if wa["original"]:
                        phone_display_parts.append(wa["international"])
                        if wa["whatsapp_link"]:
                            wa_link_parts.append(f"[打开WhatsApp]({wa['whatsapp_link']})")
                        elif wa["whatsapp_available"]:
                            wa_link_parts.append(wa["whatsapp_available"])

                phone_display = "<br>".join(phone_display_parts) if phone_display_parts else "无"
                wa_display = "<br>".join(wa_link_parts) if wa_link_parts else ""
            else:
                phone_display = "【无联系电话，无法WhatsApp建联】"
                wa_display = "【无联系电话，无法WhatsApp建联】"

            # 主营业务：附加外贸备注
            trade_type = biz.get("_trade_type", "")
            trade_tag = biz.get("_trade_tag", False)
            business_note = ""
            if trade_type:
                business_note = f"（{trade_type}）"
            if trade_tag or phone:
                if phone:
                    business_note += " WhatsApp优先沟通"

            types_display = types_cn + business_note

            # 处理表格内管道符
            name = name.replace("|", "｜")
            address = address.replace("|", "｜")
            types_display = types_display.replace("|", "｜")

            lines.append(
                f"| {idx} | {name} | {phone_display} | {wa_display} | "
                f"{address} | {types_display} | [地图链接]({maps_url}) | {rating_status} |"
            )

        return "\n".join(lines)

    def format_csv(self, businesses: List[Dict[str, Any]],
                   wa_processor: WhatsAppProcessor) -> str:
        """
        生成可直接导入Excel的CSV纯文本
        逗号分隔，表头一致
        """
        if not businesses:
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        # 表头
        writer.writerow([
            "序号", "商家名称", "完整联系电话", "WhatsApp直达链接",
            "详细地址", "主营业务", "谷歌地图链接", "评分", "营业状态",
            "官方网站", "外贸主体类型"
        ])

        for idx, biz in enumerate(businesses, 1):
            name = biz.get("name", "")
            phone = biz.get("phone", "")
            address = biz.get("address", "")
            if biz.get("postal_code"):
                address += f" {biz['postal_code']}"
            types_cn = biz.get("types_cn", "")
            maps_url = biz.get("google_maps_url", "")
            rating = biz.get("rating", "")
            status_cn = biz.get("business_status_cn", "")
            website = biz.get("website", "")
            trade_type = biz.get("_trade_type", "")

            # WhatsApp链接
            if phone:
                wa_results = wa_processor.process_business_phones(phone)
                phone_parts = []
                wa_parts = []
                for wa in wa_results:
                    if wa["original"]:
                        phone_parts.append(wa["international"])
                        wa_parts.append(wa["whatsapp_link"])
                phone_display = " | ".join(phone_parts) if phone_parts else ""
                wa_display = " | ".join(wa_parts) if wa_parts else ""
            else:
                phone_display = "【无联系电话，无法WhatsApp建联】"
                wa_display = ""

            # 主营业务
            types_display = types_cn
            if trade_type:
                types_display += f"（{trade_type}）"

            writer.writerow([
                idx, name, phone_display, wa_display,
                address, types_display, maps_url, rating, status_cn,
                website, trade_type
            ])

        return output.getvalue()

    def format_trade_tips(self) -> str:
        """生成外贸操作小贴士"""
        tips = [
            "1. 海外商家优先WhatsApp发起开发信，打开率远高于电话、邮件；",
            "2. 批量添加建议控制每日数量，避免账号风控限制；",
            "3. 建联开场白可使用简洁外贸询价话术；",
            "4. 批量号码可后续用WhatsApp号码验证工具核验是否注册账号，避免无效添加；",
            "5. 本工具仅用于合法外贸商务合作拓客，禁止批量骚扰营销，请合理合规使用号码线索。",
        ]
        return "\n".join(tips)


class GoogleMapsWhatsAppSkill:
    """谷歌地图全球外贸商家线索采集 & WhatsApp建联智能体"""

    def __init__(self):
        self.parser = InstructionParser()
        self.wa_processor = WhatsAppProcessor()
        self.cleaner = DataCleaner()
        self.formatter = OutputFormatter()
        self.mcp_server = "http://localhost:8006"

    def execute(self, instruction: str, **kwargs) -> Dict[str, Any]:
        """
        执行完整的搜索流程
        1. 解析指令
        2. 调用Google Places API
        3. WhatsApp号码处理
        4. 数据清洗去重
        5. 格式化输出
        """
        logger.info(f"收到指令: {instruction}")

        # 1. 解析指令
        parsed = self.parser.parse(instruction)
        logger.info(f"解析结果: {json.dumps(parsed, ensure_ascii=False)}")

        # 检查缺失要素
        if parsed["missing"]:
            question = self.parser.format_missing_question(parsed["missing"])
            return {
                "status": "need_info",
                "message": question,
                "parsed": parsed,
                "markdown_table": "",
                "csv_text": "",
                "tips": "",
            }

        # 2. 调用Google Places API
        businesses = self._search_places(parsed)
        if not businesses:
            return {
                "status": "no_results",
                "message": f"该区域无公开可抓取商户：{parsed['country']} {parsed['city']} {parsed['industry']}",
                "parsed": parsed,
                "markdown_table": "该区域无公开可抓取商户。",
                "csv_text": "",
                "tips": self.formatter.format_trade_tips(),
            }

        # 3. 数据清洗去重
        businesses = self.cleaner.filter_noise(businesses)
        businesses = self.cleaner.deduplicate(businesses)
        businesses = self.cleaner.sort_by_trade_relevance(businesses)

        # 4. 格式化输出
        markdown = self.formatter.format_markdown_table(businesses, self.wa_processor)
        csv_text = self.formatter.format_csv(businesses, self.wa_processor)
        tips = self.formatter.format_trade_tips()

        return {
            "status": "success",
            "message": f"共找到 {len(businesses)} 条商家信息",
            "parsed": parsed,
            "count": len(businesses),
            "businesses": businesses,
            "markdown_table": markdown,
            "csv_text": csv_text,
            "tips": tips,
        }

    def search_only(self, instruction: str) -> Dict[str, Any]:
        """仅搜索，返回Markdown表格"""
        result = self.execute(instruction)
        output = ""
        if result.get("markdown_table"):
            output = result["markdown_table"]
        if result.get("tips"):
            output += "\n\n---\n**外贸操作小贴士：**\n" + result["tips"]
        result["output"] = output
        return result

    def export_csv(self, instruction: str) -> Dict[str, Any]:
        """导出CSV格式"""
        result = self.execute(instruction)
        result["output"] = result.get("csv_text", "")
        return result

    def _search_places(self, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """调用Google Maps MCP插件搜索商家"""
        import requests

        country = parsed.get("country", "")
        city = parsed.get("city", "")
        district = parsed.get("district", "")
        industry_en = parsed.get("industry_en", "")
        industry_cn = parsed.get("industry", "")
        radius_km = parsed.get("radius_km", 50)
        count = parsed.get("count", 20)
        only_with_phone = parsed.get("only_with_phone", False)
        filter_closed = parsed.get("filter_closed", True)
        need_website = parsed.get("need_website", False)

        # 构建搜索位置
        location = ""
        if district:
            location = f"{district}, "
        if city:
            location += f"{city}, "
        location += country

        # 构建搜索关键词（中英文混合，提高匹配率）
        query = industry_en or industry_cn

        # 如果仅指定国家，按3大外贸核心城市分别检索
        if country and not city:
            core_cities = self._get_core_cities(country)
            if core_cities:
                all_businesses = []
                per_city_count = max(count // len(core_cities), 5)
                for c in core_cities:
                    city_location = f"{c}, {country}"
                    biz_list = self._call_search_api(
                        query=query,
                        location=city_location,
                        country=country,
                        city=c,
                        radius=radius_km * 1000,
                        count=per_city_count,
                        only_with_phone=only_with_phone,
                        filter_closed=filter_closed,
                        need_website=need_website,
                    )
                    all_businesses.extend(biz_list)
                return all_businesses[:count]

        # 单城市搜索
        return self._call_search_api(
            query=query,
            location=location,
            country=country,
            city=city,
            radius=radius_km * 1000,
            count=count,
            only_with_phone=only_with_phone,
            filter_closed=filter_closed,
            need_website=need_website,
        )

    def _call_search_api(self, query: str, location: str,
                         country: str, city: str,
                         radius: int, count: int,
                         only_with_phone: bool,
                         filter_closed: bool,
                         need_website: bool) -> List[Dict[str, Any]]:
        """调用MCP搜索API"""
        import requests as req

        url = f"{self.mcp_server}/v1/invoke"
        payload = {
            "name": "google_maps_plugin.search_places",
            "arguments": {
                "query": query,
                "location": location,
                "country": country,
                "city": city,
                "radius": radius,
                "count": count,
                "only_with_phone": only_with_phone,
                "filter_closed": filter_closed,
                "need_website": need_website,
            }
        }

        try:
            response = req.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("result", [])
        except Exception as e:
            logger.error(f"调用Google Maps MCP失败: {e}")
            # 降级：直接调用Google Places API
            return self._direct_api_search(query, location, country, radius, count,
                                           only_with_phone, filter_closed, need_website)

    def _direct_api_search(self, query: str, location: str, country: str,
                           radius: int, count: int,
                           only_with_phone: bool,
                           filter_closed: bool,
                           need_website: bool) -> List[Dict[str, Any]]:
        """降级方案：直接调用Google Places API（不依赖MCP服务）"""
        api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
        if not api_key:
            try:
                from utils.config import config as _config
                api_key = _config.google_maps.get('api_key', '') or _config.search.get('google_api_key', '')
            except Exception:
                pass

        if not api_key:
            logger.error("Google Maps API Key 未配置，无法搜索")
            return []

        all_results = []
        search_query = f"{query} in {location}"

        # Text Search
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": search_query,
            "key": api_key,
            "language": "zh-CN",
            "radius": radius,
        }

        try:
            import requests as req
            response = req.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("status") not in ("OK", "ZERO_RESULTS"):
                logger.error(f"API错误: {data.get('status')} - {data.get('error_message', '')}")
                return []

            place_ids = [r["place_id"] for r in data.get("results", []) if "place_id" in r]

            # Place Details
            for pid in place_ids[:count]:
                detail = self._fetch_place_detail(api_key, pid)
                if not detail:
                    continue

                if filter_closed and detail.get("business_status") == "CLOSED_PERMANENTLY":
                    continue
                if only_with_phone and not detail.get("phone"):
                    continue
                if need_website and not detail.get("website"):
                    continue

                all_results.append(detail)

        except Exception as e:
            logger.error(f"直接API搜索失败: {e}")

        return all_results

    def _fetch_place_detail(self, api_key: str, place_id: str) -> Dict[str, Any]:
        """获取商家详情（降级方案内部使用）"""
        import requests as req

        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "key": api_key,
            "language": "zh-CN",
            "fields": "name,formatted_phone_number,international_phone_number,"
                      "formatted_address,address_component,"
                      "geometry,business_status,rating,user_ratings_total,"
                      "website,url,types"
        }

        try:
            response = req.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK":
                return {}

            result = data.get("result", {})
            postal_code = ""
            for comp in result.get("address_components", []):
                if "postal_code" in comp.get("types", []):
                    postal_code = comp.get("long_name", "")
                    break

            status_map = {
                "OPERATIONAL": "营业中",
                "CLOSED_PERMANENTLY": "已永久关闭",
                "CLOSED_TEMPORARILY": "临时关闭",
            }
            business_status = result.get("business_status", "")
            status_cn = status_map.get(business_status, "未知")

            return {
                "place_id": place_id,
                "name": result.get("name", ""),
                "phone": result.get("international_phone_number",
                                   result.get("formatted_phone_number", "")),
                "phone_formatted": result.get("formatted_phone_number", ""),
                "address": result.get("formatted_address", ""),
                "postal_code": postal_code,
                "business_status": business_status,
                "business_status_cn": status_cn,
                "rating": result.get("rating", 0),
                "user_ratings_total": result.get("user_ratings_total", 0),
                "website": result.get("website", ""),
                "google_maps_url": result.get("url", ""),
                "types": result.get("types", []),
                "types_cn": "",  # 简化处理
            }

        except Exception as e:
            logger.error(f"Place Details获取失败: {e}")
            return {}

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

    def _get_core_cities(self, country: str) -> List[str]:
        """获取国家外贸核心城市"""
        return self.COUNTRY_CORE_CITIES.get(country, [])


# 便捷入口函数
def search_businesses(instruction: str) -> str:
    """
    便捷入口：输入自然语言指令，输出Markdown表格+CSV+小贴士
    """
    skill = GoogleMapsWhatsAppSkill()
    result = skill.execute(instruction)

    output_parts = []

    if result["status"] == "need_info":
        return result["message"]

    if result.get("markdown_table"):
        output_parts.append(result["markdown_table"])

    if result.get("csv_text"):
        output_parts.append("\n\n---\n**CSV格式（可导入Excel）：**\n```csv\n" + result["csv_text"] + "```")

    if result.get("tips"):
        output_parts.append("\n\n---\n**外贸操作小贴士：**\n" + result["tips"])

    return "\n".join(output_parts)


if __name__ == "__main__":
    # 测试示例
    skill = GoogleMapsWhatsAppSkill()

    # 模拟测试（无API Key时的指令解析测试）
    test_instructions = [
        "美国洛杉矶服装批发商家，最多10条，只保留可WhatsApp添加号码",
        "英国伦敦海运拼箱货代",
        "泰国曼谷电子产品供应商，20条",
    ]

    for inst in test_instructions:
        print(f"\n{'='*60}")
        print(f"指令: {inst}")
        parsed = skill.parser.parse(inst)
        print(f"解析: {json.dumps(parsed, ensure_ascii=False, indent=2)}")

        if not parsed["missing"]:
            wa = WhatsAppProcessor()
            test_phone = "+1 323-588-1222"
            result = wa.process_phone(test_phone, "美国")
            print(f"\n号码测试: {test_phone}")
            print(f"WhatsApp链接: {result['whatsapp_link']}")
            print(f"可添加: {result['whatsapp_available']}")
