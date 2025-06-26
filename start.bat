@echo off
chcp 65001 >nul
REM VoceChat Webhook 转发服务启动脚本 (Windows)

echo 🚀 启动 VoceChat Webhook 转发服务...

REM 检查 Python 环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 python，请先安装 Python 3.7+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 📥 安装依赖包...
pip install -r requirements.txt

REM 检查配置文件
if not exist ".env" (
    echo ⚠️ 警告: 未找到 .env 配置文件
    echo 请复制 .env.example 为 .env 并配置相关参数
    echo copy .env.example .env
    echo 然后编辑 .env 文件填入实际配置
    pause
    exit /b 1
)

REM 验证配置
echo 🔍 验证配置...
python config.py
if %errorlevel% neq 0 (
    echo ❌ 配置验证失败，请检查 .env 文件
    pause
    exit /b 1
)

REM 启动服务
echo ✅ 启动服务...
python app.py

pause
