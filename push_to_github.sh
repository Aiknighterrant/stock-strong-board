#!/bin/bash
# 推送代码到GitHub的脚本
# 使用方法：./push_to_github.sh <YOUR_GITHUB_TOKEN>

set -e  # 遇到错误时退出

echo "=== 准备推送代码到GitHub ==="
echo "仓库: https://github.com/Aiknighterrant/stock-strong-board.git"
echo ""

# 检查参数
if [ $# -eq 0 ]; then
    echo "错误: 需要提供GitHub个人访问令牌(PAT)"
    echo ""
    echo "使用方法:"
    echo "  $0 <YOUR_GITHUB_TOKEN>"
    echo ""
    echo "如何获取PAT:"
    echo "1. 访问 https://github.com/settings/tokens"
    echo "2. 点击 'Generate new token'"
    echo "3. 选择 'classic' token"
    echo "4. 设置权限: 选择 'repo' (完全控制仓库)"
    echo "5. 生成并复制token"
    echo ""
    exit 1
fi

GITHUB_TOKEN=$1
REPO_URL="https://${GITHUB_TOKEN}@github.com/Aiknighterrant/stock-strong-board.git"

echo "步骤1: 配置远程仓库..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

echo "步骤2: 推送代码到GitHub..."
echo "分支: main"
echo "文件数: $(git ls-files | wc -l)"

# 推送代码
if git push -u origin main; then
    echo ""
    echo "✅ 代码推送成功!"
    echo ""
    echo "仓库地址: https://github.com/Aiknighterrant/stock-strong-board"
    echo ""
    echo "包含的文件:"
    echo "- 技能文档: SKILL.md (OpenClaw技能主文档)"
    echo "- 项目说明: README.md"
    echo "- Python脚本: scripts/ 目录 (5个核心脚本)"
    echo "- 参考资料: references/ 目录 (3个详细文档)"
    echo "- 自动化测试: .github/workflows/test.yml"
    echo "- 安装配置: setup.py, requirements.txt"
    echo "- 许可证: LICENSE (MIT)"
else
    echo ""
    echo "❌ 推送失败!"
    echo "可能的原因:"
    echo "1. PAT权限不足"
    echo "2. 仓库不存在或没有访问权限"
    echo "3. 网络问题"
    echo ""
    echo "请检查:"
    echo "1. 确保PAT有 'repo' 权限"
    echo "2. 确保仓库 https://github.com/Aiknighterrant/stock-strong-board 存在"
    echo "3. 重新生成PAT并重试"
    echo ""
    exit 1
fi

echo "=== 推送完成 ==="
echo "您现在可以访问: https://github.com/Aiknighterrant/stock-strong-board"
echo "查看您的技能代码!"