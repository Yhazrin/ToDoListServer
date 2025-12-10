#!/bin/bash

# ToDoList 服务器管理脚本
# 用于管理 Flask 应用的启动、停止、重启等操作

# 配置变量
APP_NAME="ToDoList Server"
APP_FILE="app.py"
PID_FILE="server.pid"
LOG_FILE="server.log"
PORT=5000
HOST="0.0.0.0"
WORKERS=1
WS_WORKER="gevent"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] ${message}${NC}"
}

# 检查应用文件是否存在
check_app_file() {
    if [ ! -f "$APP_FILE" ]; then
        print_message $RED "错误: 找不到应用文件 $APP_FILE"
        exit 1
    fi
}

# 获取服务器进程ID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

# 检查服务器是否运行
is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# 启动服务器
start_server() {
    print_message $BLUE "正在启动 $APP_NAME..."
    
    check_app_file
    
    if is_running; then
        print_message $YELLOW "服务器已经在运行中 (PID: $(get_pid))"
        return 0
    fi
    
    # 清理旧的PID文件
    [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
    
    # 优先使用支持WebSocket的Gunicorn
    if command -v gunicorn >/dev/null 2>&1; then
        local entry="wsgi:app"
        # 如果找不到 wsgi.py 则回退使用工厂可调用
        if [ ! -f "wsgi.py" ]; then
            entry="app:create_app()"
        fi
        print_message $BLUE "检测到 Gunicorn，使用 WebSocket worker 启动"
        nohup gunicorn -k "$WS_WORKER" -w "$WORKERS" -b "$HOST:$PORT" "$entry" > "$LOG_FILE" 2>&1 &
        local pid=$!
    else
        print_message $YELLOW "未检测到 Gunicorn，使用内置服务器启动（WebSocket在生产环境可能不可用）"
        nohup python3 "$APP_FILE" --host="$HOST" --port="$PORT" > "$LOG_FILE" 2>&1 &
        local pid=$!
    fi
    
    # 保存PID
    echo $pid > "$PID_FILE"
    
    # 等待一下确保服务器启动
    sleep 2
    
    if is_running; then
        print_message $GREEN "✅ 服务器启动成功!"
        print_message $GREEN "   PID: $pid"
        print_message $GREEN "   地址: http://$HOST:$PORT"
        print_message $GREEN "   日志文件: $LOG_FILE"
    else
        print_message $RED "❌ 服务器启动失败，请检查日志文件: $LOG_FILE"
        [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
        return 1
    fi
}

# 停止服务器
stop_server() {
    print_message $BLUE "正在停止 $APP_NAME..."
    
    if ! is_running; then
        print_message $YELLOW "服务器未运行"
        [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
        return 0
    fi
    
    local pid=$(get_pid)
    print_message $BLUE "正在终止进程 $pid..."
    
    # 尝试优雅关闭
    kill "$pid" 2>/dev/null
    
    # 等待进程结束
    local count=0
    while [ $count -lt 10 ] && kill -0 "$pid" 2>/dev/null; do
        sleep 1
        count=$((count + 1))
    done
    
    # 如果还在运行，强制终止
    if kill -0 "$pid" 2>/dev/null; then
        print_message $YELLOW "强制终止进程..."
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi
    
    # 清理PID文件
    [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
    
    if ! kill -0 "$pid" 2>/dev/null; then
        print_message $GREEN "✅ 服务器已停止"
    else
        print_message $RED "❌ 无法停止服务器进程"
        return 1
    fi
}

# 重启服务器
restart_server() {
    print_message $BLUE "正在重启 $APP_NAME..."
    stop_server
    sleep 1
    start_server
}

# 查看服务器状态
show_status() {
    print_message $BLUE "检查 $APP_NAME 状态..."
    
    if is_running; then
        local pid=$(get_pid)
        print_message $GREEN "✅ 服务器正在运行"
        print_message $GREEN "   PID: $pid"
        print_message $GREEN "   地址: http://$HOST:$PORT"
        
        # 显示进程信息
        if command -v ps >/dev/null 2>&1; then
            echo ""
            print_message $BLUE "进程信息:"
            ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem 2>/dev/null || echo "无法获取进程详细信息"
        fi
        
        # 检查端口占用
        if command -v netstat >/dev/null 2>&1; then
            echo ""
            print_message $BLUE "端口占用情况:"
            netstat -tlnp 2>/dev/null | grep ":$PORT " || echo "端口 $PORT 未被占用"
        fi
    else
        print_message $RED "❌ 服务器未运行"
        [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
    fi
}

# 查看日志
show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        print_message $YELLOW "日志文件不存在: $LOG_FILE"
        return 1
    fi
    
    print_message $BLUE "显示服务器日志 (最后50行):"
    echo "----------------------------------------"
    tail -n 50 "$LOG_FILE"
    echo "----------------------------------------"
    print_message $BLUE "完整日志文件: $LOG_FILE"
}

# 测试服务器连接
test_server() {
    print_message $BLUE "测试服务器连接..."
    
    if ! is_running; then
        print_message $RED "❌ 服务器未运行"
        return 1
    fi
    
    # 测试HTTP连接
    if command -v curl >/dev/null 2>&1; then
        print_message $BLUE "使用 curl 测试连接..."
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT" | grep -q "200\|404\|500"; then
            print_message $GREEN "✅ 服务器响应正常"
            
            # 获取完整的API信息
            echo ""
            print_message $BLUE "API 测试:"
            api_response=$(curl -s "http://localhost:$PORT" 2>/dev/null)
            if [ $? -eq 0 ] && [ -n "$api_response" ]; then
                echo "$api_response" | python3 -m json.tool 2>/dev/null || echo "$api_response"
            else
                echo "无法获取API响应内容"
            fi
            
            # 测试各个端点的可访问性
            echo ""
            print_message $BLUE "端点连通性测试:"
            
            # 主要端点
            test_endpoint "GET" "/" "服务信息"
            test_endpoint "GET" "/health" "健康检查"
            
            # 认证端点
            test_endpoint "GET" "/auth/status" "认证服务状态"
            test_endpoint "POST" "/auth/register" "用户注册"
            test_endpoint "POST" "/auth/login" "用户登录"
            test_endpoint "POST" "/auth/logout" "用户登出"
            
            # OAuth端点
            test_endpoint "POST" "/auth/google/login" "Google登录/绑定"
            test_endpoint "POST" "/auth/google/callback" "Google回调"
            test_endpoint "POST" "/auth/github/login" "GitHub登录/绑定"
            test_endpoint "POST" "/auth/github/callback" "GitHub回调"
            
            # 用户资料端点（需要认证，预期401）
            test_endpoint_auth "GET" "/user/profile" "获取用户资料"
            test_endpoint_auth "PUT" "/user/profile" "更新用户资料"
            test_endpoint_auth "GET" "/user/tasks" "获取当前用户任务列表"
            
            # 项目组端点
            test_endpoint "POST" "/groups/create" "创建项目组"
            test_endpoint "POST" "/groups/join" "加入项目组"
            test_endpoint "POST" "/groups/join-by-code" "通过邀请码加入项目组"
            test_endpoint "GET" "/groups/list/1" "获取用户项目组列表"
            test_endpoint "GET" "/groups/info/1" "获取项目组信息"
            test_endpoint "PUT" "/groups/update/1" "更新项目组信息"
            test_endpoint "DELETE" "/groups/delete/1" "删除项目组"
            test_endpoint_auth "GET" "/groups/1/members" "获取项目组成员"
            test_endpoint_auth "GET" "/groups/1/overview" "获取项目组概览"

            # 任务系统端点（需要认证，预期401）
            test_endpoint_auth "GET" "/tasks" "获取任务列表"
            test_endpoint_auth "POST" "/tasks" "创建任务"
            test_endpoint_auth "GET" "/tasks/1" "获取任务详情"
            test_endpoint_auth "PUT" "/tasks/1" "更新任务"
            test_endpoint_auth "DELETE" "/tasks/1" "删除任务"
            test_endpoint_auth "GET" "/tasks/tree/1" "获取任务树"
            test_endpoint_auth "PUT" "/tasks/1/move" "移动任务"
            
            # 任务附件端点（需要认证，预期401）
            test_endpoint_auth "POST" "/tasks/1/attachments" "添加任务附件"
            test_endpoint_auth "GET" "/tasks/1/attachments" "获取任务附件列表"
            test_endpoint_auth "DELETE" "/tasks/1/attachments/1" "删除任务附件"
            
            # 文件系统端点（需要认证，预期401）
            test_endpoint_auth "POST" "/files/upload" "上传文件"
            test_endpoint_auth "GET" "/files/1" "获取文件信息"
            test_endpoint_auth "DELETE" "/files/1" "删除文件"
            test_endpoint_auth "GET" "/files/group/1" "获取项目组文件列表"
            test_endpoint_auth "GET" "/files/1/preview" "文件预览"

            # 聊天端点（需要认证，预期401）
            test_endpoint_auth "GET" "/chat/rooms" "获取聊天室列表"
            test_endpoint_auth "GET" "/chat/rooms/1/messages" "获取聊天消息"
            test_endpoint_auth "POST" "/chat/rooms/1/messages" "发送聊天消息"
            
            # 日历模块端点（需要认证，预期401）
            test_endpoint_auth "GET" "/calendar/events" "获取日历事件列表"
            test_endpoint_auth "POST" "/calendar/events" "创建日历事件"
            test_endpoint_auth "GET" "/calendar/events/1" "获取日历事件详情"
            test_endpoint_auth "PUT" "/calendar/events/1" "更新日历事件"
            test_endpoint_auth "DELETE" "/calendar/events/1" "删除日历事件"
            test_endpoint_auth "POST" "/calendar/from-task/1" "从任务创建日历事件"
            
            # Widget端点（需要认证，预期401）
            test_endpoint_auth "GET" "/widget/today-tasks" "获取今日任务"
            test_endpoint_auth "GET" "/widget/today-events" "获取今日事件"
            
        else
            print_message $RED "❌ 服务器无响应"
            return 1
        fi
    elif command -v wget >/dev/null 2>&1; then
        print_message $BLUE "使用 wget 测试连接..."
        if wget -q --spider "http://localhost:$PORT" 2>/dev/null; then
            print_message $GREEN "✅ 服务器响应正常"
        else
            print_message $RED "❌ 服务器无响应"
            return 1
        fi
    else
        print_message $YELLOW "⚠️  未找到 curl 或 wget，无法测试HTTP连接"
        print_message $BLUE "但服务器进程正在运行"
    fi
}

# 测试单个端点的函数
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    
    local url="http://localhost:$PORT$endpoint"
    local http_code
    
    if [ "$method" = "GET" ]; then
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    else
        # 对于POST/PUT/DELETE请求，发送空的JSON数据
        http_code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -d '{}' "$url" 2>/dev/null)
    fi
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ] || [ "$http_code" = "400" ] || [ "$http_code" = "404" ] || [ "$http_code" = "409" ] || [ "$http_code" = "500" ]; then
        printf "  ✅ %-8s %-35s [%s] %s\n" "$method" "$endpoint" "$http_code" "$description"
    else
        printf "  ❌ %-8s %-35s [%s] %s\n" "$method" "$endpoint" "$http_code" "$description"
    fi
}

# 测试需要认证的端点（预期401未授权或400错误）
test_endpoint_auth() {
    local method=$1
    local endpoint=$2
    local description=$3
    
    local url="http://localhost:$PORT$endpoint"
    local http_code
    
    if [ "$method" = "GET" ]; then
        # 尝试带token访问（使用测试token，预期401或400）
        http_code=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer test-token" "$url" 2>/dev/null)
    else
        # 对于POST/PUT/DELETE请求，发送空的JSON数据和token
        http_code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -H "Authorization: Bearer test-token" -d '{}' "$url" 2>/dev/null)
    fi
    
    # 对于需要认证的端点，401（未授权）表示端点存在且正常工作
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ] || [ "$http_code" = "400" ] || [ "$http_code" = "401" ] || [ "$http_code" = "403" ] || [ "$http_code" = "404" ] || [ "$http_code" = "409" ]; then
        printf "  ✅ %-8s %-35s [%s] %s (需认证)\n" "$method" "$endpoint" "$http_code" "$description"
    else
        printf "  ❌ %-8s %-35s [%s] %s (需认证)\n" "$method" "$endpoint" "$http_code" "$description"
    fi
}

# 显示帮助信息
show_help() {
    echo ""
    echo "ToDoList 服务器管理脚本"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs|test|help}"
    echo ""
    echo "命令说明:"
    echo "  start   - 启动服务器 (后台运行)"
    echo "  stop    - 停止服务器"
    echo "  restart - 重启服务器"
    echo "  status  - 查看服务器状态"
    echo "  logs    - 查看服务器日志"
    echo "  test    - 测试服务器连接"
    echo "  help    - 显示此帮助信息"
    echo ""
    echo "配置信息:"
    echo "  应用文件: $APP_FILE"
    echo "  PID文件: $PID_FILE"
    echo "  日志文件: $LOG_FILE"
    echo "  监听地址: $HOST:$PORT"
    echo ""
}

# 主程序
main() {
    case "$1" in
        start)
            start_server
            ;;
        stop)
            stop_server
            ;;
        restart)
            restart_server
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        test)
            test_server
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            print_message $YELLOW "请指定操作命令"
            show_help
            exit 1
            ;;
        *)
            print_message $RED "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"
