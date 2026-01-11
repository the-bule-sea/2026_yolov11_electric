@echo off
REM 启动Flask后端服务
REM 使用方法: 双击运行此文件

echo ========================================
echo 电力巡检系统 - 启动后端服务
echo ========================================
echo.

REM 激活conda环境
echo [1/2] 激活 conda 环境: electric_inspection
call conda activate electric_inspection
if %errorlevel% neq 0 (
    echo 错误: 无法激活 conda 环境
    pause
    exit /b 1
)

echo.
echo [2/2] 启动 Flask 服务...
echo 服务地址: http://0.0.0.0:5000
echo 按 Ctrl+C 停止服务
echo.

python app.py

pause
