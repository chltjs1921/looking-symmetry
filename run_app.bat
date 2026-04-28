@echo off
set GRADIO_ANALYTICS_ENABLED=False
cd /d "%~dp0"
"%~dp0learning-symmerty\Scripts\python.exe" -u -m app.app

