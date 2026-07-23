#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# 🎯 外贸获客 Agent - 启动脚本 (第一性原理设计)
# ============================================================
# 第一性原理：
# 1. 运行需要什么？ → Python 3.11+、pip、依赖包
# 2. 服务如何启动？ → python3 web_backend.py
# 3. 如何访问？     → 浏览器打开 http://localhost:8000
# 4. 出错了怎么办？ → 检查错误日志、端口占用、依赖缺失
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_FILE="${SCRIPT_DIR}/web_backend.py"
FRONTEND_FILE="${SCRIPT_DIR}/web_frontend.html"
MAIN_FILE="${SCRIPT_DIR}/main.py"
HOST="0.0.0.0"
PORT="8000"
API_KEY="sk-1247a1fea10b4f4db70d83dbc64edc97"
PYTHON_CMD=""
PID_FILE="/tmp/waimao-agent.pid"
LOG_FILE="/tmp/waimao-agent.log"

# ----------------------------------------------------------
# 工具函数
# ----------------------------------------------------------
log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}   $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "${CYAN}${BOLD}[STEP]${NC} $1"; }

check_command() {
    command -v "$1" >/dev/null 2>&1
}

check_port() {
    local port="$1"
    if check_command lsof; then
        lsof -i :"$port" >/dev/null 2>&1
    elif check_command netstat; then
        netstat -tuln 2>/dev/null | grep -q ":$port "
    elif check_command ss; then
        ss -tuln 2>/dev/null | grep -q ":$port "
    else
        (echo >/dev/tcp/localhost/$port) 2>/dev/null
    fi
}

find_python() {
    # 先尝试 python3（大多数系统的默认命令）
    for cmd in python3 python python3.11 python3.12 python3.13; do
        if check_command "$cmd"; then
            local ver
            ver=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
            if awk "BEGIN {exit !($ver >= 3.11)}"; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

print_banner() {
    echo -e ""
    echo -e "${CYAN}${BOLD}    ╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}    ║                                                   ║${NC}"
    echo -e "${CYAN}${BOLD}    ║   🎯 外贸获客 Agent                               ║${NC}"
    echo -e "${CYAN}${BOLD}    ║   全自动外贸客户开发系统                           ║${NC}"
    echo -e "${CYAN}${BOLD}    ║                                                   ║${NC}"
    echo -e "${CYAN}${BOLD}    ╚═══════════════════════════════════════════════════╝${NC}"
    echo -e ""
}

print_usage() {
    echo -e "${BOLD}用法:${NC} ./start.sh [命令] [选项]"
    echo -e ""
    echo -e "${BOLD}命令:${NC}"
    echo -e "  ${GREEN}start${NC}       启动服务 (前台运行)"
    echo -e "  ${GREEN}start -d${NC}    启动服务 (后台运行)"
    echo -e "  ${GREEN}stop${NC}        停止服务"
    echo -e "  ${GREEN}restart${NC}     重启服务"
    echo -e "  ${GREEN}status${NC}      查看服务状态"
    echo -e "  ${GREEN}health${NC}      健康检查"
    echo -e "  ${GREEN}setup${NC}       环境检查与依赖安装"
    echo -e "  ${GREEN}logs${NC}        查看运行日志"
    echo -e "  ${GREEN}skill${NC}       运行Skill模式 (需 --instruction)"
    echo -e "  ${GREEN}scheduler${NC}   运行调度器"
    echo -e ""
    echo -e "${BOLD}选项:${NC}"
    echo -e "  ${CYAN}-d, --daemon${NC}     后台运行"
    echo -e "  ${CYAN}-p, --port${NC}       指定端口 (默认: 8000)"
    echo -e "  ${CYAN}--instruction${NC}    Skill模式指令"
    echo -e "  ${CYAN}--industry${NC}       目标行业"
    echo -e "  ${CYAN}--region${NC}         目标地区"
    echo -e "  ${CYAN}--count${NC}          客户数量"
    echo -e "  ${CYAN}-h, --help${NC}       显示帮助"
    echo -e ""
    echo -e "${BOLD}示例:${NC}"
    echo -e "  ./start.sh start"
    echo -e "  ./start.sh start -d -p 8080"
    echo -e "  ./start.sh skill --instruction '搜索电子行业客户' --industry electronics"
    echo -e ""
}

# ----------------------------------------------------------
# 步骤函数
# ----------------------------------------------------------
step_check_python() {
    log_step "[1/5] 检查 Python 环境..."
    PYTHON_CMD=$(find_python)
    if [ -z "$PYTHON_CMD" ]; then
        log_error "未找到 Python 3.11+，请安装 Python 3.11 或更高版本"
        log_info "Ubuntu/Debian: sudo apt install python3.11 python3.11-pip"
        log_info "macOS: brew install python@3.11"
        exit 1
    fi
    local ver=$($PYTHON_CMD --version 2>&1)
    log_ok "找到 $ver ($PYTHON_CMD)"
}

step_check_deps() {
    log_step "[2/5] 检查依赖..."
    local req_file="${SCRIPT_DIR}/requirements.txt"
    if [ ! -f "$req_file" ]; then
        log_warn "未找到 requirements.txt"
        return
    fi

    local missing=()
    while IFS= read -r line || [[ -n "$line" ]]; do
        # 跳过空行和注释
        [[ -z "$line" || "$line" =~ ^# ]] && continue
        # 提取包名
        local pkg=$(echo "$line" | sed -E 's/([a-zA-Z0-9_-]+).*/\1/')
        if ! $PYTHON_CMD -c "import $pkg" 2>/dev/null; then
            # 特殊处理带横线的包名
            local pkg_underscore=$(echo "$pkg" | sed 's/-/_/g')
            if ! $PYTHON_CMD -c "import $pkg_underscore" 2>/dev/null; then
                missing+=("$line")
            fi
        fi
    done < "$req_file"

    if [ ${#missing[@]} -gt 0 ]; then
        log_warn "缺少 ${#missing[@]} 个依赖包"
        log_info "正在安装依赖..."
        $PYTHON_CMD -m pip install -r "$req_file" --quiet
        log_ok "依赖安装完成"
    else
        log_ok "所有依赖已安装"
    fi
}

step_check_files() {
    log_step "[3/5] 检查项目文件..."

    if [ -f "$BACKEND_FILE" ]; then
        log_ok "后端文件: web_backend.py"
        BACKEND_MODE="fastapi"
    elif [ -f "$MAIN_FILE" ]; then
        log_ok "主入口文件: main.py"
        BACKEND_MODE="main"
    elif [ -f "${SCRIPT_DIR}/web_simple.py" ]; then
        log_ok "简单Web入口: web_simple.py"
        BACKEND_MODE="simple"
    else
        log_error "未找到后端启动文件 (web_backend.py / main.py / web_simple.py)"
        exit 1
    fi

    if [ -f "$FRONTEND_FILE" ]; then
        log_ok "前端文件: web_frontend.html"
    else
        log_warn "未找到前端文件 web_frontend.html"
    fi

    if [ -f "${SCRIPT_DIR}/config.yaml" ]; then
        log_ok "配置文件: config.yaml"
    fi
}

step_check_port() {
    log_step "[4/5] 检查端口 $PORT..."
    if check_port "$PORT"; then
        log_warn "端口 $PORT 已被占用"
        local pid
        if check_command lsof; then
            pid=$(lsof -t -i :"$PORT" 2>/dev/null | head -1)
            log_info "占用进程 PID: $pid"
        fi
        read -p "是否终止占用进程并继续? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ -n "${pid:-}" ]; then
                kill "$pid" 2>/dev/null || true
                sleep 1
            fi
            if check_port "$PORT"; then
                log_error "端口仍被占用，请手动释放端口 $PORT"
                exit 1
            fi
        else
            log_error "用户取消启动"
            exit 1
        fi
    fi
    log_ok "端口 $PORT 可用"
}

step_start_server() {
    log_step "[5/5] 启动服务..."
    local daemon=${1:-false}

    # 导出环境变量
    export WAIMAO_API_KEY="$API_KEY"
    export WAIMAO_HOST="$HOST"
    export WAIMAO_PORT="$PORT"

    if [ "$BACKEND_MODE" = "fastapi" ]; then
        # FastAPI 模式
        if [ "$daemon" = "true" ]; then
            log_info "后台启动服务..."
            nohup $PYTHON_CMD "$BACKEND_FILE" > "$LOG_FILE" 2>&1 &
            local pid=$!
            echo $pid > "$PID_FILE"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                log_ok "服务已后台启动 (PID: $pid)"
            else
                log_error "服务启动失败，查看日志: $LOG_FILE"
                exit 1
            fi
        else
            log_ok "服务启动中..."
            echo -e ""
            echo -e "${GREEN}═════════════════════════════════════════════════════${NC}"
            echo -e "${GREEN}  服务地址: http://${HOST}:${PORT}${NC}"
            echo -e "${GREEN}  API Key:  ${API_KEY}${NC}"
            echo -e "${GREEN}═════════════════════════════════════════════════════${NC}"
            echo -e ""
            $PYTHON_CMD "$BACKEND_FILE"
        fi
    elif [ "$BACKEND_MODE" = "simple" ]; then
        # 简单Web模式
        if [ "$daemon" = "true" ]; then
            log_info "后台启动Web服务..."
            nohup $PYTHON_CMD "${SCRIPT_DIR}/web_simple.py" > "$LOG_FILE" 2>&1 &
            local pid=$!
            echo $pid > "$PID_FILE"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                log_ok "Web服务已后台启动 (PID: $pid)"
            else
                log_error "Web服务启动失败，查看日志: $LOG_FILE"
                exit 1
            fi
        else
            log_ok "Web服务启动中..."
            echo -e ""
            echo -e "${GREEN}═════════════════════════════════════════════════════${NC}"
            echo -e "${GREEN}  Web服务地址: http://${HOST}:${PORT}${NC}"
            echo -e "${GREEN}═════════════════════════════════════════════════════${NC}"
            echo -e ""
            $PYTHON_CMD "${SCRIPT_DIR}/web_simple.py"
        fi
    else
        # main.py 模式 - 不支持daemon，直接运行
        log_info "启动 main.py（注意：main.py不支持后台模式）..."
        $PYTHON_CMD "$MAIN_FILE"
    fi
}

# ----------------------------------------------------------
# 命令函数
# ----------------------------------------------------------
cmd_start() {
    local daemon=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--daemon) daemon=true; shift ;;
            -p|--port) PORT="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    print_banner
    step_check_python
    step_check_deps
    step_check_files
    step_check_port
    step_start_server "$daemon"

    if [ "$daemon" = "true" ]; then
        echo -e ""
        echo -e "${GREEN}═════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  服务已后台启动${NC}"
        echo -e "${GREEN}  访问地址: http://${HOST}:${PORT}${NC}"
        echo -e "${GREEN}  PID文件:  $PID_FILE${NC}"
        echo -e "${GREEN}  日志文件: $LOG_FILE${NC}"
        echo -e "${GREEN}═════════════════════════════════════════════════════${NC}"
        echo -e ""
        echo -e "查看日志: ${CYAN}./start.sh logs${NC}"
        echo -e "停止服务: ${CYAN}./start.sh stop${NC}"
    fi
}

cmd_stop() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            rm -f "$PID_FILE"
            log_ok "服务已停止 (PID: $pid)"
        else
            log_warn "进程 $pid 已不存在"
            rm -f "$PID_FILE"
        fi
    else
        # 尝试通过端口查找
        if check_command lsof; then
            local pid=$(lsof -t -i :"$PORT" 2>/dev/null | head -1)
            if [ -n "$pid" ]; then
                kill "$pid"
                log_ok "服务已停止 (PID: $pid)"
            else
                log_warn "未找到运行中的服务"
            fi
        else
            log_warn "未找到 PID 文件，无法停止服务"
        fi
    fi
}

cmd_restart() {
    cmd_stop 2>/dev/null || true
    sleep 1
    cmd_start "$@"
}

cmd_status() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log_ok "服务运行中 (PID: $pid)"
            log_info "访问地址: http://${HOST}:${PORT}"
            log_info "日志文件: $LOG_FILE"
        else
            log_warn "进程 $pid 已不存在"
            rm -f "$PID_FILE"
        fi
    else
        if check_port "$PORT"; then
            log_ok "端口 $PORT 正在使用，服务可能运行中"
        else
            log_warn "服务未运行"
        fi
    fi
}

cmd_health() {
    local url="http://${HOST}:${PORT}"
    log_info "检查服务健康状态: $url"

    if check_command curl; then
        local status
        status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        if [ "$status" = "200" ] || [ "$status" = "307" ]; then
            log_ok "服务健康 (HTTP $status)"
        else
            log_warn "服务响应异常 (HTTP $status)"
        fi
    elif check_command wget; then
        if wget -q --spider "$url" 2>/dev/null; then
            log_ok "服务健康"
        else
            log_warn "服务未响应"
        fi
    else
        log_warn "未找到 curl 或 wget，无法检查"
    fi
}

cmd_setup() {
    print_banner
    log_step "环境检查与设置"
    step_check_python
    step_check_deps
    step_check_files
    log_ok "环境检查完成"
}

cmd_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        log_warn "日志文件不存在: $LOG_FILE"
    fi
}

cmd_skill() {
    step_check_python
    step_check_deps

    local instruction=""
    local industry=""
    local region=""
    local count=5

    while [[ $# -gt 0 ]]; do
        case $1 in
            --instruction) instruction="$2"; shift 2 ;;
            --industry) industry="$2"; shift 2 ;;
            --region) region="$2"; shift 2 ;;
            --count) count="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    if [ -z "$instruction" ]; then
        log_error "请提供 --instruction 参数"
        exit 1
    fi

    log_info "运行 Skill: $instruction"
    $PYTHON_CMD "$MAIN_FILE" --mode skill \
        --instruction "$instruction" \
        ${industry:+--industry "$industry"} \
        ${region:+--region "$region"} \
        --count "$count"
}

cmd_scheduler() {
    step_check_python
    step_check_deps
    log_info "启动调度器..."
    $PYTHON_CMD "$MAIN_FILE" --mode scheduler
}

# ----------------------------------------------------------
# 主入口
# ----------------------------------------------------------
main() {
    case "${1:-}" in
        start)
            shift
            cmd_start "$@"
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            shift
            cmd_restart "$@"
            ;;
        status)
            cmd_status
            ;;
        health)
            cmd_health
            ;;
        setup)
            cmd_setup
            ;;
        logs)
            cmd_logs
            ;;
        skill)
            shift
            cmd_skill "$@"
            ;;
        scheduler)
            cmd_scheduler
            ;;
        -h|--help|help|"")
            print_usage
            ;;
        *)
            log_error "未知命令: $1"
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
