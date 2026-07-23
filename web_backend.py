#!/usr/bin/env python3
"""
Agent外贸获客 - FastAPI 后端服务
基于Agent外贸获客设计：API Key 认证 + 速率限制 + SSRF/XSS 防护 + 真实数据爬取
"""
import asyncio
import hashlib
import json
import os
import random
import re
import secrets
import smtplib
import sqlite3
import sys
import time
import uuid
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

from dotenv import load_dotenv

load_dotenv()  # 从 .env 文件加载环境变量（.env 不会被上传到 GitHub）

import requests
from bs4 import BeautifulSoup
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

# ==================== 配置 ====================
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
CRM_DB = DATA_DIR / "crm_customers.json"
EMAIL_HISTORY = DATA_DIR / "email_history.json"
SMTP_CONFIG = DATA_DIR / "smtp_config.json"
DASHBOARD_HISTORY = DATA_DIR / "dashboard_history.json"

API_KEY = os.getenv("WAIMAO_API_KEY") or secrets.token_urlsafe(24)
HOST = os.getenv("WAIMAO_HOST", "0.0.0.0")
PORT = int(os.getenv("WAIMAO_PORT", "8000"))

# 速率限制
RATE_LIMIT_PER_MIN = 60
RATE_LIMIT_PER_HOUR = 1000
_rate_counter: Dict[str, List[float]] = defaultdict(list)

# ==================== 工具函数 ====================
def _sanitize_html(text: str) -> str:
    """清理HTML标签，防止XSS攻击"""
    if not text:
        return ""
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    text = re.sub(r'javascript\s*:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'data:\s*text/html[^,]*base64', '', text, flags=re.IGNORECASE)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('"', '&quot;').replace("'", '&#039;')
    return text.strip()

def _validate_email(email: str) -> bool:
    """校验邮箱格式"""
    if not email:
        return False
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def _is_safe_url(url: str) -> bool:
    """SSRF防护：检查URL是否安全"""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        host = parsed.hostname or ""
        # 拦截内网地址
        for bad in ('127.0.0.1', 'localhost', '0.0.0.0', '169.254.', '10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.'):
            if host.startswith(bad):
                return False
        return True
    except Exception:
        return False

def _rate_limit(api_key: str) -> bool:
    """速率限制检查"""
    now = time.time()
    rec = _rate_counter[api_key]
    rec[:] = [t for t in rec if now - t < 3600]
    recent_min = sum(1 for t in rec if now - t < 60)
    if recent_min >= RATE_LIMIT_PER_MIN or len(rec) >= RATE_LIMIT_PER_HOUR:
        return False
    rec.append(now)
    return True

# ==================== 真实公司种子库 ====================
SEED_COMPANIES = {
    "electronics": [
        {"name": "Texas Instruments", "website": "https://www.ti.com/", "country": "USA", "industry": "Semiconductor"},
        {"name": "STMicroelectronics", "website": "https://www.st.com/", "country": "Switzerland", "industry": "Semiconductor"},
        {"name": "Infineon Technologies", "website": "https://www.infineon.com/", "country": "Germany", "industry": "Semiconductor"},
        {"name": "NXP Semiconductors", "website": "https://www.nxp.com/", "country": "Netherlands", "industry": "Semiconductor"},
        {"name": "onsemi", "website": "https://www.onsemi.com/", "country": "USA", "industry": "Semiconductor"},
        {"name": "Microchip Technology", "website": "https://www.microchip.com/", "country": "USA", "industry": "Semiconductor"},
        {"name": "Analog Devices", "website": "https://www.analog.com/", "country": "USA", "industry": "Semiconductor"},
        {"name": "Digi-Key Electronics", "website": "https://www.digikey.com/", "country": "USA", "industry": "Distributor"},
        {"name": "Mouser Electronics", "website": "https://www.mouser.com/", "country": "USA", "industry": "Distributor"},
    ],
    "furniture": [
        {"name": "IKEA", "website": "https://www.ikea.com/", "country": "Sweden", "industry": "Furniture Retail"},
        {"name": "Ashley Furniture", "website": "https://www.ashleyfurniture.com/", "country": "USA", "industry": "Furniture"},
        {"name": "La-Z-Boy", "website": "https://www.la-z-boy.com/", "country": "USA", "industry": "Furniture"},
        {"name": "Herman Miller", "website": "https://www.hermanmiller.com/", "country": "USA", "industry": "Office Furniture"},
        {"name": "Steelcase", "website": "https://www.steelcase.com/", "country": "USA", "industry": "Office Furniture"},
    ],
    "textile": [
        {"name": "Inditex", "website": "https://www.inditex.com/", "country": "Spain", "industry": "Fashion Retail"},
        {"name": "H&M", "website": "https://www.hm.com/", "country": "Sweden", "industry": "Fashion Retail"},
        {"name": "Uniqlo", "website": "https://www.uniqlo.com/", "country": "Japan", "industry": "Fashion Retail"},
    ],
    "machinery": [
        {"name": "Caterpillar", "website": "https://www.caterpillar.com/", "country": "USA", "industry": "Heavy Machinery"},
        {"name": "John Deere", "website": "https://www.deere.com/", "country": "USA", "industry": "Agricultural Machinery"},
        {"name": "Komatsu", "website": "https://www.komatsu.com/", "country": "Japan", "industry": "Construction Machinery"},
    ],
    "automotive": [
        {"name": "Toyota", "website": "https://www.toyota.com/", "country": "Japan", "industry": "Automotive OEM"},
        {"name": "Volkswagen", "website": "https://www.volkswagen.com/", "country": "Germany", "industry": "Automotive OEM"},
        {"name": "Ford", "website": "https://www.ford.com/", "country": "USA", "industry": "Automotive OEM"},
        {"name": "BMW", "website": "https://www.bmw.com/", "country": "Germany", "industry": "Automotive OEM"},
    ],
}

EMAIL_RE = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
PHONE_RE = re.compile(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}')
FREE_EMAIL = {'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'qq.com', '163.com'}

# ==================== 数据存储 ====================
def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def _save_json(path: Path, data: Any) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _get_customers() -> List[Dict]:
    return _load_json(CRM_DB, [])

def _save_customers(customers: List[Dict]) -> None:
    _save_json(CRM_DB, customers)

def _get_email_history() -> List[Dict]:
    return _load_json(EMAIL_HISTORY, [])

def _save_email_history(history: List[Dict]) -> None:
    _save_json(EMAIL_HISTORY, history)

def _get_smtp_config() -> Dict:
    return _load_json(SMTP_CONFIG, {})

def _save_smtp_config(cfg: Dict) -> None:
    if 'password' in cfg:
        cfg['_password_hash'] = hashlib.sha256(cfg['password'].encode()).hexdigest()[:16]
    _save_json(SMTP_CONFIG, cfg)

# ==================== 业务函数 ====================
def _real_search(industry: str, count: int = 5, region: str = "") -> List[Dict]:
    """基于种子库和真实网站爬取的搜索"""
    industry_lower = industry.lower()
    companies = []
    # 1. 优先使用种子库
    for k, lst in SEED_COMPANIES.items():
        if k in industry_lower or industry_lower in k:
            companies.extend(lst)
    if not companies:
        for lst in SEED_COMPANIES.values():
            companies.extend(lst)
    random.shuffle(companies)
    return companies[:count]

def _crawl_company_info(url: str) -> Dict:
    """爬取公司网站提取联系信息"""
    if not _is_safe_url(url):
        return {"emails": [], "phones": [], "address": "", "note": "URL不安全（SSRF防护）"}
    info = {"emails": [], "phones": [], "address": "", "products": [], "certifications": [], "note": ""}
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=False)
        if resp.status_code != 200:
            info["note"] = f"HTTP {resp.status_code}"
            return info
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(' ', strip=True)
        # 提取邮箱
        for m in EMAIL_RE.findall(resp.text)[:20]:
            domain = m.split('@')[-1].lower()
            if domain in FREE_EMAIL or 'noreply' in m.lower() or 'example.com' in m:
                continue
            if m not in info["emails"]:
                info["emails"].append(m)
        # 提取电话
        for m in PHONE_RE.findall(text)[:10]:
            phone = ''.join(m).strip()
            if len(phone) >= 7 and phone not in info["phones"]:
                info["phones"].append(phone)
        # 提取地址
        addr_match = re.search(r'(?:Address|地址|Location|Headquarters|HQ)[:\s]*([^\n]{10,200})', text, re.IGNORECASE)
        if addr_match:
            addr = addr_match.group(1).strip()
            addr = re.sub(r'(window\.|document\.|var |function |return |\$\(|\{\s*|\}\s*)', '', addr)
            info["address"] = addr[:200]
        # 认证
        for cert in ['ISO 9001', 'ISO 14001', 'CE', 'FDA', 'UL', 'FCC', 'RoHS']:
            if cert.lower() in text.lower() and cert not in info["certifications"]:
                info["certifications"].append(cert)
        info["note"] = f"爬取成功 ({len(resp.text)} 字节)"
    except Exception as e:
        info["note"] = f"爬取失败: {str(e)[:50]}"
    return info

def _evaluate_company(company: Dict, industry: str = "") -> Dict:
    """评分公司"""
    score = 0
    detail = {"website_quality": 0, "contact_info": 0, "industry_match": 0, "company_info": 0}
    # 网站质量（30分）
    if company.get("website"):
        w = company["website"]
        if w.startswith("https://"):
            detail["website_quality"] += 8
        if not any(x in w for x in ['example.com', 'test.com', 'fake']):
            detail["website_quality"] += 15
        if any(domain in w for domain in ['.com', '.cn', '.de', '.jp']):
            detail["website_quality"] += 7
    # 联系方式（35分）
    emails = company.get("emails", [])
    phones = company.get("phones", [])
    if emails:
        detail["contact_info"] += min(len(emails) * 8, 20)
    if phones:
        detail["contact_info"] += min(len(phones) * 7, 15)
    # 行业匹配（20分）
    if industry and company.get("industry"):
        if industry.lower() in company["industry"].lower() or company["industry"].lower() in industry.lower():
            detail["industry_match"] = 20
        else:
            detail["industry_match"] = 10
    elif company.get("industry"):
        detail["industry_match"] = 12
    # 公司信息（15分）
    info_count = sum(1 for k in ["address", "country", "certifications", "products", "contact_person"] if company.get(k))
    detail["company_info"] = min(info_count * 3, 15)
    score = sum(detail.values())
    level = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D"
    return {"total_score": score, "level": level, "scores": detail}

# ==================== FastAPI 应用 ====================
app = FastAPI(title="Agent外贸获客", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="无效的API Key")
    if not _rate_limit(api_key):
        raise HTTPException(status_code=429, detail="请求过于频繁")
    return "user"

# ==================== 模型 ====================
class SearchRequest(BaseModel):
    industry: str
    region: str = ""
    count: int = Field(10, ge=1, le=50)

class ScoreRequest(BaseModel):
    company_name: str = ""
    website: str = ""
    emails: List[str] = []
    phones: List[str] = []
    industry: str = ""
    content: str = ""

class WorkflowRequest(BaseModel):
    instruction: str = ""
    industry: str = ""
    region: str = ""
    count: int = Field(5, ge=1, le=20)
    product: str = ""
    send_email: bool = False
    email_template: str = "standard"

class EmailGenerateRequest(BaseModel):
    company_name: str
    contact: str = ""
    industry: str = ""
    email_type: str = "standard"
    product: str = ""

class EmailSendRequest(BaseModel):
    company_name: str
    to_email: str
    subject: str = ""
    body: str = ""
    template: str = "standard"

class CrawlRequest(BaseModel):
    url: str

class CRMAddRequest(BaseModel):
    company_name: str
    website: str = ""
    email: str = ""
    phone: str = ""
    industry: str = ""
    score: int = 0
    level: Optional[str] = None
    status: str = "待开发"
    notes: str = ""

class CRMUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    score: Optional[int] = None
    level: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class SMTPConfigRequest(BaseModel):
    provider: str = ""
    host: str = ""
    port: int = 0
    username: str = ""
    password: str = ""
    use_ssl: bool = True
    use_starttls: bool = False
    from_email: str = ""
    from_name: str = ""

# ==================== 路由 ====================
@app.get("/", response_class=HTMLResponse)
async def root():
    frontend = SCRIPT_DIR / "web_frontend.html"
    if frontend.exists():
        return FileResponse(str(frontend))
    return HTMLResponse("<h1>请先创建 web_frontend.html</h1>")

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": int(time.time())}

@app.post("/api/customer/search")
async def search_customers(req: SearchRequest, user: str = Depends(get_current_user)):
    customers = _real_search(req.industry, req.count, req.region)
    results = []
    for c in customers:
        c = dict(c)
        c["emails"] = []
        c["phones"] = []
        c["address"] = ""
        c["certifications"] = []
        # 尝试爬取（最多1个，避免超时）
        if c.get("website") and len(results) < 2:
            try:
                info = _crawl_company_info(c["website"])
                c["emails"] = info["emails"][:3]
                c["phones"] = info["phones"][:3]
                c["address"] = info["address"]
                c["certifications"] = info["certifications"][:5]
            except Exception:
                pass
        # 评分
        score_result = _evaluate_company(c, req.industry)
        c["score"] = score_result["total_score"]
        c["level"] = score_result["level"]
        c["scores"] = score_result["scores"]
        c["snippet"] = f"{c.get('industry', '')} {c.get('country', '')}"
        # 添加 company_name 别名以兼容前端
        c["company_name"] = c.get("name", "")
        results.append(c)
    return {"count": len(results), "customers": results}

@app.post("/api/score/customer")
async def score_customer(req: ScoreRequest, user: str = Depends(get_current_user)):
    company = {
        "company_name": req.company_name,
        "website": req.website,
        "emails": req.emails,
        "phones": req.phones,
        "industry": req.industry,
    }
    return {"score": _evaluate_company(company, req.industry)}

@app.post("/api/score/batch")
async def score_batch(req: dict, user: str = Depends(get_current_user)):
    customers = req.get("customers", [])
    industry = req.get("industry", "")
    results = [_evaluate_company(c, industry) for c in customers]
    return {"results": results}

@app.post("/api/crawl/website")
async def crawl_website(req: CrawlRequest, user: str = Depends(get_current_user)):
    if not _is_safe_url(req.url):
        raise HTTPException(status_code=400, detail="URL不安全（SSRF防护）")
    try:
        resp = requests.get(req.url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        return {
            "url": req.url,
            "title": soup.title.string if soup.title else "",
            "content": soup.get_text(' ', strip=True)[:5000],
            "size": len(resp.text),
            "note": f"爬取成功 {resp.status_code}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawl/extract-contacts")
async def extract_contacts(req: CrawlRequest, user: str = Depends(get_current_user)):
    if not _is_safe_url(req.url):
        raise HTTPException(status_code=400, detail="URL不安全（SSRF防护）")
    info = _crawl_company_info(req.url)
    return {"url": req.url, **info}

@app.post("/api/email/generate")
async def generate_email(req: EmailGenerateRequest, user: str = Depends(get_current_user)):
    templates = {
        "standard": {
            "subject": f"关于{req.industry or '产品'}的合作咨询 - {req.company_name}",
            "body": f"""Dear {req.contact or 'Sir/Madam'},

We are reaching out to introduce our {req.product or req.industry or 'products'} to {req.company_name}.

As a leading manufacturer, we believe our high-quality solutions can bring significant value to your business. We would love to discuss potential cooperation opportunities.

Key benefits:
✓ Competitive pricing
✓ Reliable quality
✓ Fast delivery
✓ Excellent after-sales service

Could we schedule a brief call this week to explore how we can support your business?

Best regards,
[Your Name]
[Your Company]"""
        },
        "personalized": {
            "subject": f"针对{req.company_name}的定制方案",
            "body": f"""Dear {req.contact or 'Sir/Madam'},

I recently researched {req.company_name} and was impressed by your work in {req.industry or 'your industry'}.

I have a specific proposal that could help {req.company_name} reduce costs and improve efficiency with {req.product or 'our products'}.

Would you be available for a 15-minute call next week?

Best regards,
[Your Name]"""
        },
        "follow_up": {
            "subject": f"跟进：{req.company_name}的合作机会",
            "body": f"""Dear {req.contact or 'Sir/Madam'},

I'm following up on my previous email regarding {req.product or 'our products'}.

I understand you're busy, but I believe a brief conversation could reveal valuable opportunities for {req.company_name}.

Is there a better time to reach you?

Best regards,
[Your Name]"""
        },
        "cold": {
            "subject": f"快速咨询 - {req.company_name}",
            "body": f"""Hi {req.contact or 'there'},

One quick question: is {req.company_name} currently looking for {req.product or req.industry or 'new suppliers'}?

We help companies like yours with high-quality products at competitive prices.

Reply "yes" and I'll send details.

Best,
[Your Name]"""
        },
        "ai": {
            "subject": _ai_generate_subject(req.company_name, req.industry, req.product),
            "body": _ai_generate_body(req.company_name, req.contact, req.industry, req.product, "cooperation")
        },
        "ai_supplier": {
            "subject": _ai_generate_subject(req.company_name, req.industry, req.product, "supplier"),
            "body": _ai_generate_body(req.company_name, req.contact, req.industry, req.product, "supplier")
        },
        "ai_inquiry": {
            "subject": _ai_generate_subject(req.company_name, req.industry, req.product, "inquiry"),
            "body": _ai_generate_body(req.company_name, req.contact, req.industry, req.product, "inquiry")
        },
        "ai_product": {
            "subject": _ai_generate_subject(req.company_name, req.industry, req.product, "product"),
            "body": _ai_generate_body(req.company_name, req.contact, req.industry, req.product, "product")
        },
        "ai_invitation": {
            "subject": _ai_generate_subject(req.company_name, req.industry, req.product, "invitation"),
            "body": _ai_generate_body(req.company_name, req.contact, req.industry, req.product, "invitation")
        },
        "ai_sample": {
            "subject": _ai_generate_subject(req.company_name, req.industry, req.product, "sample"),
            "body": _ai_generate_body(req.company_name, req.contact, req.industry, req.product, "sample")
        },
        "ai_agency": {
            "subject": _ai_generate_subject(req.company_name, req.industry, req.product, "agency"),
            "body": _ai_generate_body(req.company_name, req.contact, req.industry, req.product, "agency")
        },
        "ai_followup": {
            "subject": _ai_generate_subject(req.company_name, req.industry, req.product, "followup"),
            "body": _ai_generate_body(req.company_name, req.contact, req.industry, req.product, "followup")
        }
    }
    tpl = templates.get(req.email_type, templates["standard"])
    return {"email": tpl, "type": req.email_type}

def _ai_generate_subject(company_name: str, industry: str, product: str, style: str = "cooperation") -> str:
    """AI智能生成邮件主题 - 8种商业化类型"""
    company = company_name or "贵公司"
    
    subjects = {
        "supplier": [
            f"供应商申请 | {product or '产品'}供应链合作 - 致{company}" if product else f"供应商合作意向 - {company}",
            f"成为{company}的{industry or '产品'}供应商" if industry else f"供应商申请 - {company}",
        ],
        "inquiry": [
            f"询价：{product}采购咨询 - {company}" if product else f"产品采购询价 - {company}",
            f"{industry or '产品'}询价单 - {company}" if industry else f"采购询价 - {company}",
        ],
        "product": [
            f"新品推介 | {product} - {company}专属优惠" if product else f"产品推介 - 限时优惠",
            f"{industry or '产品'}解决方案 - 致{company}",
        ],
        "invitation": [
            f"展会邀请 | {company}诚邀参观",
            f"邀请函 | {industry or '行业'}展会 - 期待与{company}会面",
        ],
        "sample": [
            f"样品申请 | {product or '产品'}免费样品 - {company}" if product else f"样品申请 - 免费寄送",
            f"免费样品 | {industry or '产品'}质量体验",
        ],
        "agency": [
            f"代理申请 | {product or '品牌'}区域代理合作" if product else f"代理合作意向 - {company}",
            f"经销商招募 | {industry or '产品'}合作机会",
        ],
        "followup": [
            f"跟进：{product or '合作'}事宜 - {company}" if product else f"合作跟进 - {company}",
            f"Re: {industry or '合作'}方案确认",
        ],
        "cooperation": [
            f"{product}解决方案 | {company}的专业合作伙伴" if product else f"合作机会 - {company}",
            f"{industry}领域合作 | 致{company}" if industry else f"业务合作咨询 - {company}",
        ],
    }
    
    style_subjects = subjects.get(style, subjects["cooperation"])
    return random.choice(style_subjects)

def _ai_generate_body(company_name: str, contact: str, industry: str, product: str, style: str = "cooperation") -> str:
    """AI智能生成邮件正文 - 8种商业化类型"""
    greeting = f"Dear {contact}" if contact else "Dear Decision Maker"
    company = company_name or "your company"
    
    if style == "supplier":
        # 供应商型 - 强调供应能力和产品质量
        opening = random.choice([
            f"I am writing to express our interest in becoming a supplier for {company}.",
            f"We would like to establish a supply partnership with {company}.",
            f"As a potential supplier, we are reaching out to introduce our capabilities.",
        ])
        
        industry_prompts = {
            "electronics": "We are a leading manufacturer of electronic components with ISO 9001 & IATF 16949 certifications.",
            "furniture": "We specialize in high-quality furniture manufacturing with advanced production facilities.",
            "textile": "We offer comprehensive textile manufacturing services from raw materials to finished products.",
            "machinery": "We are a certified machinery manufacturer with strong R&D capabilities.",
            "automotive": "We supply automotive components to major OEMs worldwide.",
        }
        industry_text = industry_prompts.get(industry.lower(), "We are a professional manufacturer with strong production capabilities.")
        
        capabilities = [
            "✓ Monthly capacity: 100,000+ units",
            "✓ Lead time: 15-30 days",
            "✓ Certifications: ISO 9001 / CE / UL",
            "✓ Factory-direct competitive pricing",
            "✓ Flexible MOQ: 100 units",
        ]
        if product:
            capabilities.insert(0, f"✓ Specialized in {product} manufacturing")
        
        supports = [
            "✓ Free samples for quality evaluation",
            "✓ Technical support & after-sales service",
            "✓ OEM/ODM customization",
            "✓ Quality inspection reports",
        ]
        
        body = f"""{greeting},

{opening}

{industry_text}

Our Supply Capabilities:
{chr(10).join(capabilities[:5])}

Why Choose Us:
{chr(10).join(random.sample(supports, 3))}

We would be honored to become your trusted supplier. May we send you our product catalog and company profile?

Looking forward to your positive response.

Best regards,
[Your Name]
[Your Company]
[Website]"""
    
    elif style == "inquiry":
        # 询价型 - 采购咨询
        opening = random.choice([
            f"We are interested in purchasing {product or 'products'} from your company.",
            f"I am writing to inquire about your {product or 'products'} for our procurement needs.",
            f"Our company is evaluating suppliers for {product or industry or 'products'}.",
        ])
        
        questions = [
            f"1. Best price for {product or 'your products'} (MOQ: 1000 units)?",
            f"2. Standard lead time for orders?",
            "3. Sample availability for quality evaluation?",
            "4. Payment terms and shipping options?",
            "5. Product certifications (ISO, CE, UL)?",
        ]
        
        body = f"""{greeting},

{opening}

We represent a company in the {industry or 'manufacturing'} sector and are expanding our supply chain.

We would appreciate information on:

{chr(10).join(questions[:5])}

Please share your product catalog and price list if available.

Looking forward to your quotation.

Best regards,
[Your Name]
[Your Company]
[Contact]"""
    
    elif style == "product":
        # 产品推介型 - 新品推广
        opening = random.choice([
            f"We are excited to introduce our latest {product or 'products'} to {company}.",
            f"I'm reaching out to showcase our new {product or 'product line'}.",
            f"Our company has launched innovative {product or 'products'} that may interest {company}.",
        ])
        
        features = [
            "✓ Latest technology & design",
            "✓ Competitive pricing: up to 30% off",
            "✓ Premium quality guaranteed",
            "✓ Fast delivery: 7-15 days",
            "✓ 2-year warranty included",
        ]
        if product:
            features.insert(0, f"✓ Specialized {product} solutions")
        
        offer = random.choice([
            "🎁 Limited-time offer: 10% discount for first order",
            "🎁 Free shipping on orders over $5,000",
            "🎁 Buy 2 get 1 free for new customers",
        ])
        
        body = f"""{greeting},

{opening}

Key Features:
{chr(10).join(features[:5])}

{offer}

This offer is valid for 30 days. Would you like to receive our detailed product catalog?

Reply now to secure this special pricing!

Best regards,
[Your Name]
[Your Company]"""
    
    elif style == "invitation":
        # 展会邀请型
        exhibitions = [
            {"name": "Canton Fair", "date": "April 15-19", "booth": "Hall 5.2, E-123"},
            {"name": "CES Las Vegas", "date": "January 9-12", "booth": "LVCC, South Hall"},
            {"name": "IFA Berlin", "date": "September 1-5", "booth": "Hall 18, B-45"},
        ]
        exh = random.choice(exhibitions)
        
        body = f"""{greeting},

We cordially invite {company} to visit our booth at {exh['name']}!

📅 Exhibition: {exh['name']}
📆 Date: {exh['date']}
📍 Booth: {exh['booth']}

Highlights:
✓ New product showcase
✓ Live demonstrations
✓ Exclusive exhibition discounts
✓ Face-to-face consultation

We would be honored to meet you in person and discuss potential collaboration.

Please let us know if you can attend, and we'll send you a visitor pass.

Best regards,
[Your Name]
[Your Company]
[Phone/WeChat]"""
    
    elif style == "sample":
        # 样品申请型
        opening = random.choice([
            f"We are pleased to offer FREE samples of our {product or 'products'} to {company}.",
            f"Experience our quality firsthand with complimentary samples.",
            f"Request your free {product or 'product'} sample today!",
        ])
        
        benefits = [
            "✓ 100% free - no hidden costs",
            "✓ Fast delivery: 3-5 days",
            "✓ Full product specifications included",
            "✓ Technical support available",
        ]
        
        body = f"""{greeting},

{opening}

Sample Benefits:
{chr(10).join(benefits)}

To request your free sample:
1. Reply with your shipping address
2. Specify product requirements
3. We'll ship within 24 hours

This offer is available for qualified businesses. Limit: 2 samples per company.

Don't miss this opportunity to evaluate our quality firsthand!

Best regards,
[Your Name]
[Your Company]"""
    
    elif style == "agency":
        # 代理招募型
        opening = random.choice([
            f"We are seeking exclusive agents/distributors for {product or 'our products'} in your region.",
            f"Join our global network as an authorized distributor.",
            f"Exclusive agency opportunity for {company}.",
        ])
        
        supports = [
            "✓ Exclusive territory protection",
            "✓ Marketing materials & training",
            "✓ Competitive wholesale pricing",
            "✓ Technical support team",
            "✓ 30% margin guarantee",
        ]
        
        requirements = [
            "• Established sales network",
            "• Industry experience preferred",
            "• Annual purchase commitment",
        ]
        
        body = f"""{greeting},

{opening}

Agency Benefits:
{chr(10).join(supports)}

Requirements:
{chr(10).join(requirements)}

We offer comprehensive support to help you succeed in your market.

Interested? Reply with your company profile to start the discussion.

Best regards,
[Your Name]
[Your Company]
[Website]"""
    
    elif style == "followup":
        # 跟进型
        opening = random.choice([
            f"I'm following up on our previous conversation about {product or 'our products'}.",
            f"Just checking in regarding our {product or 'collaboration'} proposal.",
            f"Wanted to reconnect about the {product or 'opportunity'} we discussed.",
        ])
        
        body = f"""{greeting},

{opening}

Since our last communication, we have:
✓ Updated our product line with new features
✓ Introduced special pricing for valued partners
✓ Improved delivery times to 10-15 days

Would you be available for a quick call this week to discuss further?

I'm confident we can find a solution that benefits {company}.

Looking forward to hearing from you.

Best regards,
[Your Name]
[Your Company]"""
    
    else:
        # cooperation 合作型 - 默认
        opening = random.choice([
            f"I hope this email finds you well at {company}.",
            f"Greetings from your potential industry partner!",
            f"Hope you're having a productive day at {company}.",
        ])
        
        industry_prompts = {
            "electronics": "We specialize in high-quality electronic components and semiconductor solutions.",
            "furniture": "We design and manufacture premium furniture for commercial and residential use.",
            "textile": "We offer innovative textile solutions for fashion and industrial applications.",
            "machinery": "We provide advanced machinery and equipment solutions.",
            "automotive": "We supply automotive components and aftermarket solutions.",
        }
        industry_text = industry_prompts.get(industry.lower(), "We offer comprehensive solutions for your business needs.")
        
        product_lines = []
        if product:
            product_lines = [
                f"✓ {product} - Industry-leading quality",
                f"✓ Customized {product} solutions",
                f"✓ Competitive pricing on {product}",
            ]
        
        benefits = [
            "✓ Cost reduction: 15-30%",
            "✓ Supply chain optimization",
            "✓ Fast response & delivery",
            "✓ ISO 9001 certified quality",
            "✓ 24/7 technical support",
        ]
        
        call_to_action = random.choice([
            "Would you be available for a 15-minute call next week?",
            "Could we schedule a brief introduction call?",
            "Let me know if you'd like to discuss further.",
        ])
        
        body = f"""{greeting},

{opening}

{industry_text}

Based on our research of {company}, we believe our solutions could significantly benefit your operations.

"""
        
        if product_lines:
            body += "Product Highlights:\n" + "\n".join(product_lines) + "\n\n"
        
        body += "Key Benefits:\n" + "\n".join(random.sample(benefits, 3)) + "\n\n"
        
        body += f"""{call_to_action}

Best regards,
[Your Name]
[Your Company]
[Contact Information]"""
    
    return body

@app.post("/api/email/send")
async def send_email(req: EmailSendRequest, user: str = Depends(get_current_user)):
    if not _validate_email(req.to_email):
        raise HTTPException(status_code=400, detail="收件人邮箱格式不合法")
    if not req.subject or not req.body:
        # 自动生成
        gen = await generate_email(EmailGenerateRequest(
            company_name=req.company_name, email_type=req.template
        ), user)
        req.subject = req.subject or gen["email"]["subject"]
        req.body = req.body or gen["email"]["body"]

    history = _get_email_history()
    record = {
        "id": str(uuid.uuid4()),
        "company_name": _sanitize_html(req.company_name),
        "to_email": req.to_email,
        "subject": _sanitize_html(req.subject),
        "body": _sanitize_html(req.body),
        "sent_at": int(time.time()),
        "status": "sent",
        "simulated": False,
    }

    smtp_cfg = _get_smtp_config()
    if smtp_cfg.get("host") and smtp_cfg.get("username") and smtp_cfg.get("password"):
        # 真实发送
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_cfg.get("from_email") or smtp_cfg["username"]
            msg['To'] = req.to_email
            msg['Subject'] = req.subject
            msg.attach(MIMEText(req.body, 'plain', 'utf-8'))
            if smtp_cfg.get("use_ssl", True):
                server = smtplib.SMTP_SSL(smtp_cfg["host"], smtp_cfg.get("port", 465), timeout=10)
            else:
                server = smtplib.SMTP(smtp_cfg["host"], smtp_cfg.get("port", 587), timeout=10)
                if smtp_cfg.get("use_starttls"):
                    server.starttls()
            server.login(smtp_cfg["username"], smtp_cfg["password"])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            record["status"] = "failed"
            record["error"] = str(e)[:200]
    else:
        # 模拟发送
        record["simulated"] = True

    history.insert(0, record)
    _save_email_history(history[:1000])
    return {"success": True, "record": record}

@app.get("/api/email/history")
async def get_email_history(user: str = Depends(get_current_user), limit: int = 50):
    history = _get_email_history()
    return {"history": history[:limit], "total": len(history)}

@app.post("/api/crm/customers")
async def crm_add(req: CRMAddRequest, user: str = Depends(get_current_user)):
    if req.email and not _validate_email(req.email):
        raise HTTPException(status_code=400, detail="邮箱格式不合法")
    customers = _get_customers()
    record = {
        "id": str(uuid.uuid4()),
        "company_name": _sanitize_html(req.company_name.strip()),
        "website": req.website.strip(),
        "email": req.email.strip(),
        "phone": req.phone.strip(),
        "industry": _sanitize_html(req.industry.strip()),
        "score": req.score,
        "level": req.level or ("A" if req.score >= 85 else "B" if req.score >= 70 else "C" if req.score >= 55 else "D"),
        "status": _sanitize_html(req.status or "待开发"),
        "notes": _sanitize_html(req.notes.strip()),
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    }
    customers.insert(0, record)
    _save_customers(customers)
    return {"success": True, "customer": record}

@app.get("/api/crm/customers")
async def crm_list(user: str = Depends(get_current_user), page: int = 1, page_size: int = 20, level: str = "", status: str = ""):
    customers = _get_customers()
    if level:
        customers = [c for c in customers if c.get("level") == level]
    if status:
        customers = [c for c in customers if c.get("status") == status]
    total = len(customers)
    start = (page - 1) * page_size
    end = start + page_size
    return {"customers": customers[start:end], "total": total, "page": page, "page_size": page_size}

@app.get("/api/crm/customers/{customer_id}")
async def crm_get(customer_id: str, user: str = Depends(get_current_user)):
    customers = _get_customers()
    for c in customers:
        if c.get("id") == customer_id:
            return c
    raise HTTPException(status_code=404, detail="客户不存在")

@app.put("/api/crm/customers/{customer_id}")
async def crm_update(customer_id: str, req: CRMUpdateRequest, user: str = Depends(get_current_user)):
    customers = _get_customers()
    for c in customers:
        if c.get("id") == customer_id:
            for k, v in req.dict(exclude_none=True).items():
                if isinstance(v, str) and k in ["company_name", "industry", "status", "notes"]:
                    c[k] = _sanitize_html(v)
                else:
                    c[k] = v
            c["updated_at"] = int(time.time())
            _save_customers(customers)
            return {"success": True, "customer": c}
    raise HTTPException(status_code=404, detail="客户不存在")

@app.delete("/api/crm/customers/{customer_id}")
async def crm_delete(customer_id: str, user: str = Depends(get_current_user)):
    customers = _get_customers()
    customers = [c for c in customers if c.get("id") != customer_id]
    _save_customers(customers)
    return {"success": True}

@app.get("/api/smtp/config")
async def smtp_get_config(user: str = Depends(get_current_user)):
    cfg = _get_smtp_config()
    if not cfg:
        return {"configured": False, "config": {}}
    safe_cfg = {k: v for k, v in cfg.items() if k not in ('password', '_password_hash')}
    safe_cfg['password'] = '***' if cfg.get('password') else ''
    return {"configured": True, "config": safe_cfg}

@app.post("/api/smtp/config")
async def smtp_save_config(req: SMTPConfigRequest, user: str = Depends(get_current_user)):
    cfg = req.dict()
    existing = _get_smtp_config()
    if not cfg.get("password") and existing.get("password"):
        cfg["password"] = existing["password"]
    _save_smtp_config(cfg)
    return {"success": True, "message": "SMTP配置已保存"}

@app.post("/api/smtp/test")
async def smtp_test(user: str = Depends(get_current_user)):
    cfg = _get_smtp_config()
    if not cfg.get("host"):
        return {"success": False, "message": "SMTP未配置"}
    try:
        if cfg.get("use_ssl", True):
            server = smtplib.SMTP_SSL(cfg["host"], cfg.get("port", 465), timeout=10)
        else:
            server = smtplib.SMTP(cfg["host"], cfg.get("port", 587), timeout=10)
            if cfg.get("use_starttls"):
                server.starttls()
        server.login(cfg["username"], cfg["password"])
        server.quit()
        return {"success": True, "message": "SMTP连接成功"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)[:100]}"}

@app.delete("/api/smtp/config")
async def smtp_clear(user: str = Depends(get_current_user)):
    if SMTP_CONFIG.exists():
        SMTP_CONFIG.unlink()
    return {"success": True, "message": "SMTP配置已清除"}

@app.post("/api/workflow/full")
async def workflow_full(req: WorkflowRequest, user: str = Depends(get_current_user)):
    customers = _real_search(req.industry or "electronics", req.count, req.region)
    results = []
    for c in customers:
        c = dict(c)
        c["emails"] = []
        c["phones"] = []
        c["address"] = ""
        c["certifications"] = []
        # 爬取
        if c.get("website"):
            try:
                info = _crawl_company_info(c["website"])
                c["emails"] = info["emails"][:3]
                c["phones"] = info["phones"][:3]
                c["address"] = info["address"]
                c["certifications"] = info["certifications"][:5]
            except Exception:
                pass
        # 评分
        score_result = _evaluate_company(c, req.industry)
        c["score"] = score_result["total_score"]
        c["level"] = score_result["level"]
        c["scores"] = score_result["scores"]
        c["snippet"] = f"{c.get('industry', '')} {c.get('country', '')}"
        c["company_name"] = c.get("name", "")
        # 写入CRM
        try:
            crm_req = CRMAddRequest(
                company_name=c["company_name"],
                website=c.get("website", ""),
                email=c["emails"][0] if c["emails"] else "",
                phone=c["phones"][0] if c["phones"] else "",
                industry=c.get("industry", ""),
                score=c["score"],
                level=c["level"],
                status="待开发",
            )
            crm_record = await crm_add(crm_req, user)
            c["crm_id"] = crm_record["customer"]["id"]
        except Exception:
            c["crm_id"] = None
        # 发送开发信
        c["email_sent"] = False
        if req.send_email and c["emails"]:
            try:
                gen = await generate_email(EmailGenerateRequest(
                    company_name=c["company_name"],
                    contact="",
                    industry=req.industry,
                    email_type=req.email_template,
                    product=req.product,
                ), user)
                send_req = EmailSendRequest(
                    company_name=c["company_name"],
                    to_email=c["emails"][0],
                    subject=gen["email"]["subject"],
                    body=gen["email"]["body"],
                    template=req.email_template,
                )
                await send_email(send_req, user)
                c["email_sent"] = True
            except Exception:
                pass
        results.append(c)

    return {
        "summary": f"成功获取{len(results)}个客户，已全部录入CRM" + ("，并发送了开发信" if req.send_email else ""),
        "customers": results,
    }

def _get_dashboard_history() -> List[Dict]:
    return _load_json(DASHBOARD_HISTORY, [])

def _save_dashboard_history(data: List[Dict]) -> None:
    _save_json(DASHBOARD_HISTORY, data)

def _record_dashboard_snapshot() -> Dict:
    """记录当前数据快照到历史，返回快照"""
    customers = _get_customers()
    history = _get_email_history()
    sent = sum(1 for h in history if h.get("status") == "sent")
    levels = {"A": 0, "B": 0, "C": 0, "D": 0}
    for c in customers:
        lv = c.get("level", "D")
        if lv in levels:
            levels[lv] += 1
    total = max(len(customers), 1)
    avg_score = sum(c.get("score", 0) for c in customers) / total
    converted = sum(1 for c in customers if c.get("status") == "已成交")
    snapshot = {
        "timestamp": int(time.time()),
        "total_customers": len(customers),
        "total_emails_sent": sent,
        "a_level": levels["A"],
        "b_level": levels["B"],
        "c_level": levels["C"],
        "d_level": levels["D"],
        "conversion_rate": round((converted / total) * 100, 1),
        "avg_score": round(avg_score, 1),
    }
    # 保存到历史（最多保留 90 天记录，每天最多 1 条）
    hist = _get_dashboard_history()
    today = time.strftime("%Y-%m-%d")
    hist = [h for h in hist if time.strftime("%Y-%m-%d", time.localtime(h["timestamp"])) != today]
    hist.append(snapshot)
    cutoff = time.time() - 90 * 86400
    hist = [h for h in hist if h["timestamp"] >= cutoff]
    _save_dashboard_history(hist)
    return snapshot

@app.get("/api/dashboard/stats")
async def dashboard_stats(user: str = Depends(get_current_user)):
    customers = _get_customers()
    email_history = _get_email_history()
    # 真实统计
    levels = {"A": 0, "B": 0, "C": 0, "D": 0}
    for c in customers:
        lv = c.get("level", "D")
        if lv in levels:
            levels[lv] += 1
    total = max(len(customers), 1)
    sent = sum(1 for h in email_history if h.get("status") == "sent")
    avg_score = sum(c.get("score", 0) for c in customers) / total
    converted = sum(1 for c in customers if c.get("status") == "已成交")
    conversion_rate = (converted / total) * 100
    # 状态分布
    status_dist = {}
    for c in customers:
        st = c.get("status", "待开发")
        status_dist[st] = status_dist.get(st, 0) + 1
    # 行业分布
    industry_dist = {}
    for c in customers:
        ind = c.get("industry", "未分类")
        industry_dist[ind] = industry_dist.get(ind, 0) + 1
    # 记录今日快照
    snapshot = _record_dashboard_snapshot()
    # 获取历史趋势
    hist = _get_dashboard_history()
    trend = [{
        "date": time.strftime("%m-%d", time.localtime(h["timestamp"])),
        "customers": h["total_customers"],
        "emails": h["total_emails_sent"],
        "avg_score": h["avg_score"],
        "a_level": h.get("a_level", 0),
        "conversion_rate": h.get("conversion_rate", 0),
    } for h in hist[-30:]]
    # 最近客户（按创建时间倒序，最多 8 条，可点击查看详情）
    sorted_customers = sorted(customers, key=lambda c: c.get("created_at", 0), reverse=True)
    recent_customers = [{
        "id": c.get("id", ""),
        "name": c.get("company_name", ""),
        "website": c.get("website", ""),
        "industry": c.get("industry", ""),
        "score": c.get("score", 0),
        "level": c.get("level", "D"),
        "status": c.get("status", "待开发"),
        "email": c.get("email", ""),
        "phone": c.get("phone", ""),
        "created_at": c.get("created_at", 0),
    } for c in sorted_customers[:8]]
    # 最近邮件（按发送时间倒序，最多 8 条）
    sorted_emails = sorted(email_history, key=lambda e: e.get("sent_at", 0), reverse=True)
    recent_emails = [{
        "company": e.get("company_name", ""),
        "to_email": e.get("to_email", ""),
        "subject": e.get("subject", ""),
        "status": e.get("status", ""),
        "time": e.get("sent_at", 0),
    } for e in sorted_emails[:8]]
    return {
        "stats": {
            "total_customers": len(customers),
            "total_emails_sent": sent,
            "a_level_customers": levels["A"],
            "conversion_rate": round(conversion_rate, 1),
            "avg_score": round(avg_score, 1),
        },
        "level_distribution": levels,
        "status_distribution": status_dist,
        "industry_distribution": industry_dist,
        "trend": trend,
        "recent_customers": recent_customers,
        "recent_emails": recent_emails,
    }

if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*50}")
    print(f"  Agent外贸获客 服务启动")
    print(f"  API Key: {API_KEY}")
    print(f"  访问地址: http://localhost:{PORT}")
    print(f"{'='*50}\n")
    uvicorn.run(app, host=HOST, port=PORT)
