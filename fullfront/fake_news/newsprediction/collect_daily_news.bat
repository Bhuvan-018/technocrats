@echo off
setlocal
cd /d %~dp0

python collect_live_news.py > collect_daily.log 2>&1

endlocal
