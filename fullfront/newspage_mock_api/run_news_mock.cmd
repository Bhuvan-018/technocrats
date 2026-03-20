@echo off
setlocal
cd /d %~dp0
set NEWS_MOCK_PORT=9060
node server.js
