#!/usr/bin/env python3
"""
Agent外贸获客 - 简单Web界面启动器
集成 Skill 执行 + 简单Web UI
"""
import asyncio
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import webbrowser

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills'))

# 创建工作目录
os.chdir(os.path.dirname(__file__))

PORT = 8000

HTML_CONTENT = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Agent外贸获客</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, sans-serif; background: #f0f2f5; color: #1f2937; }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 24px; }
.header h1 { font-size: 20px; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.card-title { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 6px; }
.form-group input, .form-group textarea, .form-group select { width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 13px; }
.btn { padding: 10px 20px; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; }
.btn-primary { background: #667eea; color: white; }
.btn-success { background: #10b981; color: white; }
.btn:hover { opacity: 0.9; }
.result { background: #1e293b; color: #e2e8f0; padding: 16px; border-radius: 8px; font-family: monospace; font-size: 12px; white-space: pre-wrap; max-height: 500px; overflow: auto; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 16px; border-radius: 10px; text-align: center; }
.stat-num { font-size: 28px; font-weight: 700; }
.stat-label { font-size: 12px; opacity: 0.9; }
</style>
</head>
<body>
<div class="header">
    <h1>🎯 Agent外贸获客</h1>
    <p style="font-size: 12px; opacity: 0.9; margin-top: 4px;">全自动外贸客户开发系统</p>
</div>
<div class="container">
    <div class="stats">
        <div class="stat-card"><div class="stat-num" id="s1">0</div><div class="stat-label">搜索客户</div></div>
        <div class="stat-card"><div class="stat-num" id="s2">0</div><div class="stat-label">爬取页面</div></div>
        <div class="stat-card"><div class="stat-num" id="s3">0</div><div class="stat-label">提取联系</div></div>
        <div class="stat-card"><div class="stat-num" id="s4">0</div><div class="stat-label">评分客户</div></div>
    </div>
    <div class="card">
        <div class="card-title">🚀 运行获客任务</div>
        <div class="form-group"><label>自然语言指令</label>
            <input type="text" id="instruction" placeholder="例如：搜索电子行业5个美国客户" value="搜索 electronics 行业 5 个客户">
        </div>
        <div class="form-group"><label>行业</label><input type="text" id="industry" placeholder="如：electronics"></div>
        <div class="form-group"><label>地区</label><input type="text" id="region" placeholder="如：USA"></div>
        <div class="form-group"><label>数量</label><input type="number" id="count" value="5" min="1" max="20"></div>
        <button class="btn btn-primary" onclick="runTask()">▶ 开始任务</button>
        <button class="btn btn-success" onclick="runSkill()">▶ 直接调用Skill</button>
    </div>
    <div class="card">
        <div class="card-title">📊 执行结果</div>
        <div class="result" id="result">点击按钮开始执行任务...</div>
    </div>
    <div class="card">
        <div class="card-title">ℹ️ 系统信息</div>
        <p style="font-size: 13px; color: #6b7280; line-height: 1.8;">
            ✅ Python 3.14.4 已就绪<br>
            ✅ TradeCustomerSkill 模块已加载<br>
            ⚠️ 需要独立启动MCP插件（search/crawl/score/crm/email）<br>
            📚 完整功能请使用 <code>python3 main.py</code> 命令行模式
        </p>
    </div>
</div>
<script>
async function runTask() {
    const instruction = document.getElementById('instruction').value;
    const industry = document.getElementById('industry').value;
    const region = document.getElementById('region').value;
    const count = document.getElementById('count').value;
    document.getElementById('result').textContent = '⏳ 执行中...';
    try {
        const res = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction, industry, region, count: parseInt(count) })
        });
        const data = await res.json();
        document.getElementById('result').textContent = JSON.stringify(data, null, 2);
        if (data.results) {
            document.getElementById('s1').textContent = data.results.search_count || 0;
            document.getElementById('s2').textContent = data.results.crawl_count || 0;
            document.getElementById('s3').textContent = data.results.extract_count || 0;
            document.getElementById('s4').textContent = data.results.score_count || 0;
        }
    } catch (e) {
        document.getElementById('result').textContent = '❌ 错误: ' + e.message;
    }
}
async function runSkill() {
    const instruction = document.getElementById('instruction').value;
    const industry = document.getElementById('industry').value;
    const region = document.getElementById('region').value;
    const count = document.getElementById('count').value;
    document.getElementById('result').textContent = '⏳ 执行中...';
    try {
        const res = await fetch('/api/skill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction, industry, region, count: parseInt(count) })
        });
        const data = await res.json();
        document.getElementById('result').textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        document.getElementById('result').textContent = '❌ 错误: ' + e.message;
    }
}
</script>
</body>
</html>'''

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/run' or self.path == '/api/skill':
            content_length = int(self.headers['Content-Length'] or 0)
            body = self.rfile.read(content_length).decode('utf-8') if content_length else '{}'
            try:
                params = json.loads(body)
            except:
                params = {}

            try:
                from skills.trade_customer_skill.main import TradeCustomerSkill
                skill = TradeCustomerSkill()
                result = skill.execute(
                    instruction=params.get('instruction', ''),
                    count=params.get('count', 5),
                    industry=params.get('industry', ''),
                    region=params.get('region', '')
                )
                response = result
            except Exception as e:
                import traceback
                response = {"status": "error", "message": str(e), "trace": traceback.format_exc()}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 静默日志

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', PORT), MyHandler)
    print(f'🌐 Web服务启动: http://localhost:{PORT}')
    print(f'📚 简单UI模式 (无MCP插件，功能受限)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
