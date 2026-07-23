@echo off
setlocal

set "SOURCE_DIR=%~dp0src\ida_pro_mcp"
set "PLUGIN_DIR=C:\Users\unk\Desktop\IDA9.2_AI\plugins"

if not exist "%PLUGIN_DIR%" (
    mkdir "%PLUGIN_DIR%"
    if errorlevel 1 exit /b 1
)

copy /Y "%SOURCE_DIR%\ida_mcp.py" "%PLUGIN_DIR%\ida_mcp.py" >nul
if errorlevel 1 exit /b 1

robocopy "%SOURCE_DIR%\ida_mcp" "%PLUGIN_DIR%\ida_mcp" /E /R:2 /W:1 >nul
if errorlevel 8 exit /b %errorlevel%

echo Installed IDA MCP plugin to "%PLUGIN_DIR%".
exit /b 0
