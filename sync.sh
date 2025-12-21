#!/bin/bash
# sync.sh - 快速同步到 GitHub
# 用法: ./sync.sh [commit message]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "🔄 同步到 GitHub"
echo "=================================================="

# 检查是否有更改
if git diff --quiet && git diff --staged --quiet; then
    echo -e "${YELLOW}⚠️  没有需要提交的更改${NC}"
    exit 0
fi

# 显示更改
echo ""
echo "📝 待提交的更改:"
git status --short

# 获取 commit message
if [ -n "$1" ]; then
    COMMIT_MSG="$1"
else
    COMMIT_MSG="chore: sync updates $(date '+%Y-%m-%d %H:%M')"
fi

echo ""
echo "📦 提交信息: $COMMIT_MSG"
echo ""

# 添加所有更改
git add -A

# 提交
git commit -m "$COMMIT_MSG

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# 推送
echo ""
echo "🚀 推送到 GitHub..."
git push origin main

echo ""
echo -e "${GREEN}✅ 同步完成！${NC}"
echo "🔗 https://github.com/sun-messi/youtube_monitor"
