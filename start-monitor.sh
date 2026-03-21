#!/bin/bash

# SSH服务器监控系统一键启动脚本
# 使用方法: ./start-monitor.sh

cd "$(dirname "$0")"

echo "🚀 启动服务器监控系统..."
echo ""

# 检查端口是否已被占用
if lsof -ti :8080 > /dev/null 2>&1; then
    echo "⚠️  端口 8080 已被占用，正在关闭旧进程..."
    lsof -ti :8080 | xargs kill -9 2>/dev/null
    sleep 1
fi

# 启动服务器
echo "📊 启动监控面板: http://localhost:8080"
echo "🔄 自动刷新间隔: 10秒"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

python3 ./sshmon serve servers.yml --port 8080 --refresh 10
