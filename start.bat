@echo off
cd /d "%~dp0frontend"
title 核心概念卡片 - 本地服务器
echo ====================================
echo   核心概念卡片 - 本地服务器
echo ====================================
echo.
echo 正在启动本地服务器...
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python 已就绪
    start http://localhost:8899
    echo 浏览器已打开，地址: http://localhost:8899
    echo.
    echo 按 Ctrl+C 关闭服务器
    echo.
    python -m http.server 8899
    goto :end
)

REM 检查 Node.js http-server
npx --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Node.js 已就绪
    start http://localhost:8899
    echo 浏览器已打开，地址: http://localhost:8899
    echo.
    echo 按 Ctrl+C 关闭服务器
    echo.
    npx http-server -p 8899 -c-1
    goto :end
)

echo 错误: 未找到 Python 或 Node.js
echo 请安装 Python 后重试: https://www.python.org/downloads/
pause
:end
pause
