@echo off
cd /d %~dp0
uv sync --frozen
uv run python bot.py
pause
