#!/bin/bash
# VoceChat Webhook 转发服务启动脚本 (Linux/macOS)

set -e

echo "🚀 启动 VoceChat Webhook 转发服务..."

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.7+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖包..."
pip install -r requirements.txt

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️ 警告: 未找到 .env 配置文件"
    echo "请复制 .env.example 为 .env 并配置相关参数"
    echo "cp .env.example .env"
    echo "然后编辑 .env 文件填入实际配置"
    exit 1
fi

# 验证配置
echo "🔍 验证配置..."
python3 config.py

if [ $? -ne 0 ]; then
    echo "❌ 配置验证失败，请检查 .env 文件"
    exit 1
fi

# 启动服务
echo "✅ 启动服务..."
python3 app.py
