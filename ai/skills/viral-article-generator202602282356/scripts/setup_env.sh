#!/bin/bash
# 设置环境变量脚本

# 千问文生图 API Key
export DASHSCOPE_API_KEY="your_dashscope_api_key"

# 绿联 API Key
export WECHAT_API_KEY="xhs_8d0a843b2b1ff33572f29859b5a3f96a"

# 公众号 AppID
export WECHAT_APPID="wx733dafb28f8804b0"

echo "✅ 环境变量已设置"
echo "DASHSCOPE_API_KEY: $DASHSCOPE_API_KEY"
echo "WECHAT_API_KEY: $WECHAT_API_KEY"
echo "WECHAT_APPID: $WECHAT_APPID"
echo ""
echo "💡 提示：请将此脚本添加到 ~/.bashrc 或 ~/.zshrc 中以永久生效"
echo "   source $(pwd)/setup_env.sh"
