#!/usr/bin/env python3
"""
谷歌地图全球外贸商家线索采集 & WhatsApp建联智能体 - Web服务
自包含的HTTP服务器，集成搜索+WhatsApp链接生成+表格/CSV输出
"""
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skills.google_maps_whatsapp_skill.main import (
    GoogleMapsWhatsAppSkill,
    InstructionParser,
    WhatsAppProcessor,
    DataCleaner,
    OutputFormatter,
)

PORT = int(os.getenv('PORT', '8080'))
HOST = '0.0.0.0'

# 全局实例
_skill = GoogleMapsWhatsAppSkill()
_parser = InstructionParser()
_wa = WhatsAppProcessor()
_formatter = OutputFormatter()


HTML_PAGE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>谷歌地图外贸商家采集 & WhatsApp建联</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
.header { background: linear-gradient(135deg, #1e3a5f 0%, #0c4a6e 50%, #075985 100%); padding: 20px 30px; border-bottom: 3px solid #0ea5e9; box-shadow: 0 4px 20px rgba(14,165,233,0.2); }
.header-inner { max-width: 1400px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
.logo { display: flex; align-items: center; gap: 12px; }
.logo-icon { font-size: 32px; }
.logo-text h1 { font-size: 20px; font-weight: 700; color: #fff; }
.logo-text p { font-size: 12px; color: #7dd3fc; margin-top: 2px; }
.api-bar { display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.15); }
.api-bar input { background: transparent; border: none; color: #fff; font-size: 12px; width: 200px; outline: none; }
.api-bar input::placeholder { color: rgba(255,255,255,0.4); }
.api-bar label { font-size: 11px; color: #7dd3fc; white-space: nowrap; }
.container { max-width: 1400px; margin: 0 auto; padding: 24px; }
.search-card { background: #1e293b; border-radius: 16px; padding: 28px; margin-bottom: 20px; border: 1px solid #334155; box-shadow: 0 4px 24px rgba(0,0,0,0.3); }
.search-title { font-size: 18px; font-weight: 600; margin-bottom: 6px; color: #f1f5f9; display: flex; align-items: center; gap: 8px; }
.search-desc { font-size: 13px; color: #94a3b8; margin-bottom: 20px; }
.input-group { margin-bottom: 16px; }
.input-group label { display: block; font-size: 13px; font-weight: 500; color: #cbd5e1; margin-bottom: 6px; }
.input-group input[type="text"] { width: 100%; padding: 14px 16px; background: #0f172a; border: 2px solid #334155; border-radius: 10px; color: #f1f5f9; font-size: 15px; transition: all 0.2s; }
.input-group input[type="text"]:focus { border-color: #0ea5e9; box-shadow: 0 0 0 3px rgba(14,165,233,0.15); }
.examples { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.example-chip { padding: 6px 14px; background: #334155; border: 1px solid #475569; border-radius: 20px; font-size: 12px; color: #cbd5e1; cursor: pointer; transition: all 0.2s; }
.example-chip:hover { background: #0ea5e9; color: #fff; border-color: #0ea5e9; }
.btn-row { display: flex; gap: 12px; margin-top: 8px; flex-wrap: wrap; }
.btn { padding: 12px 28px; border: none; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px; }
.btn:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(0,0,0,0.3); }
.btn-primary { background: linear-gradient(135deg, #0ea5e9, #0284c7); color: #fff; }
.btn-success { background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; }
.btn-info { background: linear-gradient(135deg, #6366f1, #4f46e5); color: #fff; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.parsed-info { background: #0f172a; border-radius: 10px; padding: 14px 18px; margin-top: 16px; border-left: 4px solid #0ea5e9; display: none; }
.parsed-info.show { display: block; }
.parsed-info h4 { font-size: 13px; color: #7dd3fc; margin-bottom: 8px; }
.parsed-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.parsed-tag { padding: 4px 12px; background: #1e3a5f; border-radius: 6px; font-size: 12px; color: #bae6fd; }
.result-section { display: none; }
.result-section.show { display: block; }
.result-card { background: #1e293b; border-radius: 16px; padding: 24px; margin-bottom: 20px; border: 1px solid #334155; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px; }
.result-title { font-size: 16px; font-weight: 600; color: #f1f5f9; }
.result-count { padding: 4px 14px; background: #0ea5e9; color: #fff; border-radius: 20px; font-size: 12px; font-weight: 600; }
.stats-row { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.stat-box { background: #0f172a; border-radius: 10px; padding: 14px 20px; flex: 1; min-width: 140px; border: 1px solid #334155; }
.stat-box .num { font-size: 24px; font-weight: 700; color: #0ea5e9; }
.stat-box .label { font-size: 11px; color: #64748b; margin-top: 2px; }
.stat-box.whatsapp .num { color: #22c55e; }
.stat-box.no-phone .num { color: #f59e0b; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; padding: 12px 10px; background: #0f172a; color: #94a3b8; font-weight: 600; border-bottom: 2px solid #334155; position: sticky; top: 0; white-space: nowrap; }
td { padding: 12px 10px; border-bottom: 1px solid #1e293b; color: #cbd5e1; vertical-align: top; }
tr:hover td { background: rgba(14,165,233,0.05); }
.wa-link { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background: #22c55e; color: #fff; border-radius: 6px; font-size: 12px; text-decoration: none; font-weight: 500; margin: 2px 0; }
.wa-link:hover { background: #16a34a; }
.wa-badge { display: inline-block; padding: 2px 8px; background: #166534; color: #86efac; border-radius: 4px; font-size: 11px; margin-left: 4px; }
.no-phone { color: #f59e0b; font-size: 12px; }
.map-link { color: #0ea5e9; text-decoration: none; }
.map-link:hover { text-decoration: underline; }
.rating { color: #f59e0b; font-weight: 600; }
.status-open { color: #22c55e; }
.status-closed { color: #ef4444; }
.trade-tag { display: inline-block; padding: 2px 8px; background: #312e81; color: #a5b4fc; border-radius: 4px; font-size: 11px; margin-left: 4px; }
.table-wrap { overflow-x: auto; max-height: 600px; overflow-y: auto; border-radius: 10px; border: 1px solid #334155; }
.csv-section { background: #0f172a; border-radius: 10px; padding: 16px; border: 1px solid #334155; }
.csv-section pre { white-space: pre-wrap; word-break: break-all; font-size: 12px; color: #94a3b8; max-height: 300px; overflow-y: auto; font-family: 'Fira Code', 'Consolas', monospace; }
.tips-card { background: #1e293b; border-radius: 16px; padding: 24px; border: 1px solid #334155; border-left: 4px solid #22c55e; }
.tips-card h3 { font-size: 15px; color: #22c55e; margin-bottom: 12px; }
.tips-card ul { list-style: none; }
.tips-card li { padding: 8px 0; font-size: 13px; color: #cbd5e1; line-height: 1.7; padding-left: 24px; position: relative; }
.tips-card li::before { content: '\\u25b8'; position: absolute; left: 8px; color: #22c55e; }
.loading-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15,23,42,0.8); z-index: 9999; align-items: center; justify-content: center; flex-direction: column; gap: 20px; }
.loading-overlay.show { display: flex; }
.spinner { width: 60px; height: 60px; border: 5px solid #334155; border-top-color: #0ea5e9; border-radius: 50%; animation: spin 1s linear infinite; }
.loading-text { font-size: 16px; color: #7dd3fc; }
@keyframes spin { to { transform: rotate(360deg); } }
.alert { padding: 14px 18px; border-radius: 10px; margin-bottom: 16px; font-size: 13px; display: none; border-left: 4px solid; }
.alert.show { display: block; }
.alert-error { background: rgba(239,68,68,0.1); color: #fca5a5; border-left-color: #ef4444; }
.alert-warning { background: rgba(245,158,11,0.1); color: #fcd34d; border-left-color: #f59e0b; }
.alert-success { background: rgba(34,197,94,0.1); color: #86efac; border-left-color: #22c55e; }
.alert-info { background: rgba(14,165,233,0.1); color: #7dd3fc; border-left-color: #0ea5e9; }
.footer { text-align: center; padding: 30px; color: #475569; font-size: 12px; }
</style>
</head>
<body>

<div class="header">
    <div class="header-inner">
        <div class="logo">
            <span class="logo-icon">🌍</span>
            <div class="logo-text">
                <h1>谷歌地图外贸商家采集 & WhatsApp建联</h1>
                <p>全球谷歌地图商户信息抓取 · 手机号自动判定WhatsApp · 一键生成wa.me链接</p>
            </div>
        </div>
        <div class="api-bar">
            <label>API Key:</label>
            <input type="password" id="api-key" placeholder="Google Maps API Key（可选）">
        </div>
    </div>
</div>

<div class="container">
    <div class="search-card">
        <div class="search-title">🔍 自然语言搜索指令</div>
        <div class="search-desc">输入一句话，自动识别国家、城市、行业、筛选条件。例如：美国洛杉矶服装批发商家，最多10条，只保留可WhatsApp添加号码</div>
        <div class="input-group">
            <input type="text" id="instruction" placeholder="在此输入搜索指令..." value="美国洛杉矶服装批发商家，最多10条">
        </div>
        <div class="examples">
            <span class="example-chip" onclick="fillExample(this)">美国洛杉矶服装批发商家，最多10条，只保留可WhatsApp添加号码</span>
            <span class="example-chip" onclick="fillExample(this)">英国伦敦海运拼箱货代</span>
            <span class="example-chip" onclick="fillExample(this)">泰国曼谷电子产品供应商，20条</span>
            <span class="example-chip" onclick="fillExample(this)">迪拜海外仓一件代发</span>
            <span class="example-chip" onclick="fillExample(this)">马来西亚吉隆坡五金建材批发</span>
            <span class="example-chip" onclick="fillExample(this)">美国服装批发商家，最多6条</span>
        </div>
        <div class="btn-row">
            <button class="btn btn-primary" onclick="doSearch()" id="search-btn">🚀 开始采集</button>
            <button class="btn btn-info" onclick="parseOnly()">📝 仅解析指令</button>
            <button class="btn btn-success" onclick="exportCSV()" id="csv-btn" style="display:none;">📊 导出CSV</button>
        </div>
        <div id="parsed-info" class="parsed-info">
            <h4>📋 指令解析结果</h4>
            <div class="parsed-tags" id="parsed-tags"></div>
        </div>
        <div id="alert-box" class="alert"></div>
    </div>

    <div id="result-section" class="result-section">
        <div class="stats-row" id="stats-row"></div>

        <div class="result-card">
            <div class="result-header">
                <div class="result-title">📊 商家信息表格</div>
                <div id="result-count" class="result-count"></div>
            </div>
            <div class="table-wrap">
                <table id="result-table">
                    <thead>
                        <tr>
                            <th>序号</th>
                            <th>商家名称</th>
                            <th>完整联系电话</th>
                            <th>WhatsApp直达链接</th>
                            <th>详细地址</th>
                            <th>主营业务</th>
                            <th>谷歌地图链接</th>
                            <th>评分&营业状态</th>
                        </tr>
                    </thead>
                    <tbody id="result-tbody"></tbody>
                </table>
            </div>
        </div>

        <div class="result-card">
            <div class="result-header">
                <div class="result-title">📄 CSV纯文本（可导入Excel）</div>
                <button class="btn btn-success" onclick="copyCSV()" style="padding:8px 16px;font-size:12px;">📋 复制CSV</button>
            </div>
            <div class="csv-section">
                <pre id="csv-output"></pre>
            </div>
        </div>

        <div class="tips-card">
            <h3>💡 外贸操作小贴士</h3>
            <ul>
                <li>海外商家优先WhatsApp发起开发信，打开率远高于电话、邮件</li>
                <li>批量添加建议控制每日数量，避免账号风控限制</li>
                <li>建联开场白可使用简洁外贸询价话术</li>
                <li>批量号码可后续用WhatsApp号码验证工具核验是否注册账号，避免无效添加</li>
                <li>本工具仅用于合法外贸商务合作拓客，禁止批量骚扰营销，请合理合规使用号码线索</li>
            </ul>
        </div>
    </div>
</div>

<div id="loading" class="loading-overlay">
    <div class="spinner"></div>
    <div class="loading-text" id="loading-text">正在调用Google Places API采集商家信息...</div>
</div>

<div class="footer">
    谷歌地图全球外贸商家线索采集 & WhatsApp建联智能体 · 仅供合法外贸商务拓客使用
</div>

<script>
let _lastResult = null;
let _csvText = '';

function fillExample(el) {
    document.getElementById('instruction').value = el.textContent;
}

function showAlert(msg, type) {
    const box = document.getElementById('alert-box');
    box.className = 'alert alert-' + (type || 'info') + ' show';
    box.textContent = msg;
    if (type !== 'error' && type !== 'warning') {
        setTimeout(() => box.classList.remove('show'), 5000);
    }
}

function showLoading(text) {
    document.getElementById('loading-text').textContent = text || '加载中...';
    document.getElementById('loading').classList.add('show');
}
function hideLoading() {
    document.getElementById('loading').classList.remove('show');
}

async function parseOnly() {
    const instruction = document.getElementById('instruction').value.trim();
    if (!instruction) { showAlert('请输入搜索指令', 'error'); return; }
    try {
        const res = await fetch('/api/parse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction })
        });
        const data = await res.json();
        renderParsed(data.parsed);
        showAlert('指令解析完成', 'success');
    } catch(e) { showAlert('解析失败: ' + e.message, 'error'); }
}

async function doSearch() {
    const instruction = document.getElementById('instruction').value.trim();
    if (!instruction) { showAlert('请输入搜索指令', 'error'); return; }
    const apiKey = document.getElementById('api-key').value.trim();

    const btn = document.getElementById('search-btn');
    btn.disabled = true;
    showLoading('正在调用Google Places API采集商家信息...');

    try {
        const res = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction, api_key: apiKey })
        });
        const data = await res.json();

        hideLoading();

        if (data.status === 'need_info') {
            showAlert(data.message, 'warning');
            return;
        }

        if (data.status === 'no_results') {
            showAlert(data.message, 'warning');
            renderParsed(data.parsed);
            return;
        }

        if (data.status === 'error') {
            showAlert(data.message || '搜索失败', 'error');
            return;
        }

        _lastResult = data;
        renderParsed(data.parsed);
        renderResults(data);
        _csvText = data.csv_text || '';
        document.getElementById('csv-btn').style.display = 'inline-flex';
        showAlert('采集完成，共找到 ' + (data.count || 0) + ' 条商家信息', 'success');
    } catch(e) {
        hideLoading();
        showAlert('请求失败: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
    }
}

function renderParsed(parsed) {
    if (!parsed) return;
    const tags = [];
    if (parsed.country) tags.push(['国家', parsed.country]);
    if (parsed.city) tags.push(['城市', parsed.city]);
    if (parsed.district) tags.push(['区域', parsed.district]);
    if (parsed.industry) tags.push(['行业', parsed.industry]);
    if (parsed.industry_en) tags.push(['搜索词', parsed.industry_en]);
    tags.push(['条数上限', parsed.count || 20]);
    tags.push(['搜索半径', (parsed.radius_km || 50) + 'km']);
    if (parsed.only_with_phone) tags.push(['筛选', '只要带电话商家']);
    if (parsed.filter_closed !== false) tags.push(['筛选', '过滤停业']);
    if (parsed.need_website) tags.push(['筛选', '需要官网']);
    if (parsed.trade_types && parsed.trade_types.length) tags.push(['外贸类型', parsed.trade_types.join('/')]);

    const html = tags.map(t => '<span class="parsed-tag">' + escapeHtml(t[0]) + ': ' + escapeHtml(String(t[1])) + '</span>').join('');
    document.getElementById('parsed-tags').innerHTML = html;
    document.getElementById('parsed-info').classList.add('show');
}

function escapeHtml(s) {
    if (!s) return '';
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderResults(data) {
    const businesses = data.businesses || [];
    document.getElementById('result-section').classList.add('show');
    document.getElementById('result-count').textContent = '共 ' + businesses.length + ' 条';

    const mode = data.mode || '';
    if (mode) {
        document.getElementById('result-count').textContent = '共 ' + businesses.length + ' 条 (' + mode + ')';
    }

    let waCount = 0, noPhoneCount = 0;
    businesses.forEach(b => {
        if (b.phone) waCount++;
        else noPhoneCount++;
    });
    document.getElementById('stats-row').innerHTML =
        '<div class="stat-box"><div class="num">' + businesses.length + '</div><div class="label">采集商家总数</div></div>' +
        '<div class="stat-box whatsapp"><div class="num">' + waCount + '</div><div class="label">可WhatsApp建联</div></div>' +
        '<div class="stat-box no-phone"><div class="num">' + noPhoneCount + '</div><div class="label">无联系电话</div></div>';

    const tbody = document.getElementById('result-tbody');
    tbody.innerHTML = businesses.map((b, i) => {
        const name = escapeHtml(b.name || '');
        const phone = b.phone || '';
        const address = escapeHtml((b.address || '') + (b.postal_code ? ' ' + b.postal_code : ''));
        const types = escapeHtml(b.types_cn || '');
        const mapsUrl = b.google_maps_url || '';
        const rating = b.rating || 0;
        const statusCn = b.business_status_cn || '';
        const tradeType = b._trade_type || '';
        const website = b.website || '';

        let phoneHtml, waHtml;
        if (phone) {
            const phones = phone.split(/[,;，；\\n]/).filter(p => p.trim());
            const waLinks = phones.map(p => {
                const clean = p.trim().replace(/[^\\d+]/g, '');
                const digits = clean.replace(/\\+/g, '');
                if (digits) {
                    return '<a href="https://wa.me/' + digits + '" target="_blank" class="wa-link">💬 ' + escapeHtml(p.trim()) + '</a>';
                }
                return escapeHtml(p.trim());
            });
            phoneHtml = phones.map(p => '<div>' + escapeHtml(p.trim()) + '</div>').join('');
            waHtml = waLinks.join('<br>');
        } else {
            phoneHtml = '<span class="no-phone">【无联系电话，无法WhatsApp建联】</span>';
            waHtml = '<span class="no-phone">—</span>';
        }

        let ratingHtml = '';
        if (rating) ratingHtml += '<span class="rating">⭐ ' + rating + '</span>';
        if (statusCn) {
            const cls = statusCn === '营业中' ? 'status-open' : 'status-closed';
            ratingHtml += '<br><span class="' + cls + '">' + escapeHtml(statusCn) + '</span>';
        }

        let typesHtml = types;
        if (tradeType) typesHtml += '<span class="trade-tag">' + escapeHtml(tradeType) + '</span>';
        if (phone) typesHtml += '<span class="wa-badge">WhatsApp优先</span>';

        const mapHtml = mapsUrl ? '<a href="' + escapeHtml(mapsUrl) + '" target="_blank" class="map-link">📍 查看地图</a>' : '—';

        return '<tr>' +
            '<td>' + (i + 1) + '</td>' +
            '<td style="font-weight:600;">' + name + (website ? '<br><a href="' + escapeHtml(website) + '" target="_blank" style="font-size:11px;color:#0ea5e9;">官网</a>' : '') + '</td>' +
            '<td>' + phoneHtml + '</td>' +
            '<td>' + waHtml + '</td>' +
            '<td style="font-size:12px;max-width:250px;">' + address + '</td>' +
            '<td style="font-size:12px;">' + typesHtml + '</td>' +
            '<td>' + mapHtml + '</td>' +
            '<td>' + ratingHtml + '</td>' +
            '</tr>';
    }).join('');

    document.getElementById('csv-output').textContent = data.csv_text || '';
}

function exportCSV() {
    if (!_csvText) { showAlert('无CSV数据', 'warning'); return; }
    let filename = '外贸商家_' + new Date().toISOString().slice(0,10);
    const parsed = _lastResult && _lastResult.parsed;
    if (parsed) {
        const parts = [];
        if (parsed.country) parts.push(parsed.country);
        if (parsed.city) parts.push(parsed.city);
        if (parsed.industry) parts.push(parsed.industry);
        if (parts.length > 0) {
            filename = parts.join('_') + '_' + new Date().toISOString().slice(0,10);
        }
    }
    const blob = new Blob(['\\ufeff' + _csvText], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename + '.csv';
    a.click();
    URL.revokeObjectURL(url);
    showAlert('CSV文件已下载: ' + filename + '.csv', 'success');
}

function copyCSV() {
    if (!_csvText) { showAlert('无CSV数据', 'warning'); return; }
    navigator.clipboard.writeText(_csvText).then(() => {
        showAlert('CSV已复制到剪贴板', 'success');
    }).catch(() => {
        const ta = document.createElement('textarea');
        ta.value = _csvText;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showAlert('CSV已复制到剪贴板', 'success');
    });
}

document.getElementById('instruction').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') doSearch();
});
</script>
</body>
</html>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self._serve_html()
        elif self.path == '/api/health':
            self._json({'status': 'ok'})
        else:
            self._json({'error': 'not found'}, 404)

    def do_POST(self):
        body = self._read_body()
        if self.path == '/api/parse':
            self._handle_parse(body)
        elif self.path == '/api/search':
            self._handle_search(body)
        else:
            self._json({'error': 'not found'}, 404)

    def _serve_html(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode('utf-8'))

    def _handle_parse(self, body):
        instruction = body.get('instruction', '')
        parsed = _parser.parse(instruction)
        self._json({'status': 'ok', 'parsed': parsed})

    def _handle_search(self, body):
        instruction = body.get('instruction', '')
        api_key = body.get('api_key', '')

        if api_key:
            os.environ['GOOGLE_MAPS_API_KEY'] = api_key

        global _skill
        _skill = GoogleMapsWhatsAppSkill()

        try:
            result = _skill.execute(instruction)

            if result['status'] == 'need_info':
                self._json({
                    'status': 'need_info',
                    'message': result['message'],
                    'parsed': result.get('parsed'),
                    'mode': result.get('mode', '指令解析'),
                })
                return

            if result['status'] == 'no_results':
                self._json({
                    'status': 'no_results',
                    'message': result['message'],
                    'parsed': result.get('parsed'),
                    'markdown_table': result.get('markdown_table', ''),
                    'tips': result.get('tips', ''),
                    'mode': result.get('mode', ''),
                })
                return

            self._json({
                'status': 'success',
                'message': result.get('message', ''),
                'count': result.get('count', 0),
                'parsed': result.get('parsed'),
                'businesses': result.get('businesses', []),
                'markdown_table': result.get('markdown_table', ''),
                'csv_text': result.get('csv_text', ''),
                'tips': result.get('tips', ''),
                'mode': result.get('mode', 'Google Places API'),
            })

        except Exception as e:
            import traceback
            self._json({
                'status': 'error',
                'message': str(e),
                'trace': traceback.format_exc(),
            })

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode('utf-8'))
        except Exception:
            return {}

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    server = HTTPServer((HOST, PORT), Handler)
    print(f'\n{"="*60}')
    print(f'  🌍 谷歌地图外贸商家采集 & WhatsApp建联智能体')
    print(f'  📡 Web服务已启动: http://localhost:{PORT}')
    print(f'  💡 在页面顶部输入Google Maps API Key即可实际采集')
    print(f'  ⏹ 按 Ctrl+C 停止服务')
    print(f'{"="*60}\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n服务已停止')
        server.shutdown()


if __name__ == '__main__':
    main()
