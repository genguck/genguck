#!/bin/bash
# ================================================
# 谷歌地图全球外贸商家线索采集 & WhatsApp建联智能体
# 一键启动脚本 - 本地运行版
# ================================================

set -e

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  🌍 谷歌地图外贸商家采集 & WhatsApp建联${NC}"
echo -e "${CYAN}  本地启动脚本${NC}"
echo -e "${CYAN}========================================${NC}"

# 1. 检查Python
echo -e "\n${YELLOW}[1/5] 检查Python环境...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo -e "${RED}错误: 未找到Python，请先安装Python 3.8+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python: $($PYTHON --version)${NC}"

# 2. 安装依赖
echo -e "\n${YELLOW}[2/5] 安装依赖包...${NC}"
$PYTHON -m pip install --quiet pyyaml python-dotenv requests 2>/dev/null || {
    echo -e "${YELLOW}pip install 需要权限，尝试 --user 模式...${NC}"
    $PYTHON -m pip install --user --quiet pyyaml python-dotenv requests
}
echo -e "${GREEN}✓ 依赖安装完成${NC}"

# 3. 检查API Key
echo -e "\n${YELLOW}[3/5] 检查Google Maps API Key...${NC}"

# 从.env读取
API_KEY=""
if [ -f .env ]; then
    API_KEY=$(grep -oP 'GOOGLE_MAPS_API_KEY=\K.*' .env 2>/dev/null || true)
fi

# 从config.yaml读取
if [ -z "$API_KEY" ]; then
    API_KEY=$($PYTHON -c "
import yaml
with open('config.yaml','r') as f:
    c=yaml.safe_load(f)
print(c.get('google_maps',{}).get('api_key',''))
" 2>/dev/null || true)
fi

if [ -n "$API_KEY" ]; then
    # 检查Key格式
    if [[ "$API_KEY" == AIza* ]]; then
        echo -e "${GREEN}✓ API Key已配置: ${API_KEY:0:10}...${NC}"
    else
        echo -e "${YELLOW}⚠ API Key格式异常（标准Google Maps Key应以 AIza 开头）${NC}"
        echo -e "${YELLOW}  当前Key: ${API_KEY:0:10}...${NC}"
        echo -e "${YELLOW}  请确认是否为Google Maps API Key${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 未配置API Key${NC}"
    echo -e "  可通过以下方式配置："
    echo -e "  1. 在网页顶部API Key输入框直接输入"
    echo -e "  2. 编辑 .env 文件设置 GOOGLE_MAPS_API_KEY"
    echo -e "  3. 编辑 config.yaml 中 google_maps.api_key"
fi

# 4. 检查端口
echo -e "\n${YELLOW}[4/5] 检查端口...${NC}"
PORT=${PORT:-8080}
if lsof -i :$PORT &> /dev/null || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo -e "${YELLOW}⚠ 端口 $PORT 被占用，尝试 8081...${NC}"
    PORT=8081
fi
echo -e "${GREEN}✓ 使用端口: $PORT${NC}"

# 5. 启动服务
echo -e "\n${YELLOW}[5/5] 启动Web服务...${NC}"
export PORT=$PORT
echo -e "${GREEN}"
echo "  🌍 服务地址: http://localhost:$PORT"
echo "  💡 在页面顶部输入Google Maps API Key即可开始采集"
echo "  ⏹ 按 Ctrl+C 停止服务"
echo -e "${NC}"

exec $PYTHON gmaps_web.py
