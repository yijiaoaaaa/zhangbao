@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ========================================
echo   大学生理财 - 一键推送到 GitHub
echo ========================================
echo.

set "MSG=%~1"
if "%MSG%"=="" set "MSG=update"

echo [1/3] 暂存改动...
git add -A
if errorlevel 1 goto fail

echo [2/3] 提交...
git commit -m "%MSG%"
if errorlevel 1 (
    echo    （没有新改动，跳过提交）
)

echo [3/3] 推送到 GitHub...
git push
if errorlevel 1 goto fail

echo.
echo ========================================
echo   ✅ 完成！Vercel / Cloudflare 会自动更新
echo ========================================
echo.
pause
exit /b 0

:fail
echo.
echo ❌ 出错了，看上面的报错信息
pause
exit /b 1
