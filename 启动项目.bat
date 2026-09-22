@echo off
chcp 65001 >nul
title 英语汇学 - 一键启动脚本

echo ===================================================
echo             英语汇学 (Smart English) 启动中...
echo ===================================================
echo.

:: 1. 检查 Python 环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+ 并添加到环境变量！
    pause
    exit
)

:: 2. 安装/检查后端依赖
echo [1/3] 正在检查并安装后端 Python 依赖...
pip install -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

:: 3. 启动后端服务
echo [2/3] 正在启动后端 FastAPI 服务 (http://127.0.0.1:8000)...
start "后端服务 (FastAPI)" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

:: 4. 启动前端服务
echo [3/3] 正在启动前端服务...
where npm >nul 2>&1
if %errorlevel% flex 0 (
    if exist "node_modules" (
        start "前端服务 (Vite)" cmd /k "npm run dev"
    ) else (
        echo [提示] 首次运行，正在安装前端依赖...
        call npm install --registry=https://registry.npmmirror.com
        start "前端服务 (Vite)" cmd /k "npm run dev"
    )
) else (
    echo [提示] 未检测到 Node.js 环境，准备尝试静态预览...
)

echo.
echo ===================================================
echo  系统启动指令已发出！
echo  后端地址: http://127.0.0.1:8000
echo  前端地址: http://localhost:5173 (或窗口中提示的地址)
echo ===================================================
echo.
pause
