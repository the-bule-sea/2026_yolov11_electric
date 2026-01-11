@echo off
REM 自动激活conda环境并安装Python后端依赖
REM 使用方法: 双击运行此文件

echo ========================================
echo 电力巡检系统 - 后端依赖安装脚本
echo ========================================
echo.

REM 激活conda环境
echo [1/2] 激活 conda 环境: electric_inspection
call conda activate electric_inspection
if %errorlevel% neq 0 (
    echo 错误: 无法激活 conda 环境
    echo 请确保已安装 Anaconda/Miniconda 并创建了 electric_inspection 环境
    pause
    exit /b 1
)

echo.
echo [2/2] 安装 Python 依赖包...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 依赖安装完成!
echo ========================================
echo.
echo 下一步:
echo 1. 配置 .env 文件 (复制 .env.example 并修改)
echo 2. 创建 MySQL 数据库: electric_inspection
echo 3. 运行: python app.py
echo.
pause
