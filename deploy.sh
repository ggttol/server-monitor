#!/bin/bash

# GitHub 发布脚本
# 使用方法: ./deploy.sh <GITHUB_TOKEN> <REPO_NAME>
# 例如: ./deploy.sh ghp_xxxxx server-monitor

set -e

GITHUB_TOKEN=$1
REPO_NAME=${2:-server-monitor}
USER_NAME=${3:-your-github-username}

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ 请提供 GitHub Personal Access Token"
    echo "使用方法: ./deploy.sh <TOKEN> [仓库名] [用户名]"
    echo ""
    echo "创建 Token: https://github.com/settings/tokens"
    exit 1
fi

echo "🚀 开始发布到 GitHub..."

# 进入项目目录
cd "$(dirname "$0")"

# 初始化 Git（如果需要）
if [ ! -d .git ]; then
    echo "📦 初始化 Git 仓库..."
    git init
    git remote add origin https://github.com/${USER_NAME}/${REPO_NAME}.git
fi

# 创建 .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
*.log
EOF

# 添加所有文件
echo "📝 添加文件..."
git add .

# 提交
echo "💾 提交代码..."
git commit -m "feat: 服务器监控系统 - 实时Web监控面板

功能特性:
- 实时监控多台Linux服务器
- Web仪表盘支持亮色/暗色主题
- 自动刷新数据
- 添加/删除服务器管理
- 网络流量监控
- 内存、磁盘、CPU监控"

# 创建 GitHub 仓库
echo "🌐 创建 GitHub 仓库..."
RESPONSE=$(curl -s -X POST \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/user/repos \
    -d "{\"name\":\"${REPO_NAME}\",\"description\":\"Linux服务器实时监控系统\",\"private\":false,\"auto_init\":false}")

# 检查是否创建成功或仓库已存在
if echo "$RESPONSE" | grep -q '"full_name"'; then
    echo "✅ 仓库创建成功"
elif echo "$RESPONSE" | grep -q "already exists"; then
    echo "ℹ️  仓库已存在"
else
    echo "⚠️  创建仓库时出现问题，但继续推送..."
fi

# 设置远程仓库
git remote set-url origin https://${USER_NAME}:${GITHUB_TOKEN}@github.com/${USER_NAME}/${REPO_NAME}.git

# 推送代码
echo "📤 推送代码到 GitHub..."
git branch -M main
git push -u origin main --force

echo ""
echo "🎉 发布完成！"
echo "📖 访问: https://github.com/${USER_NAME}/${REPO_NAME}"
