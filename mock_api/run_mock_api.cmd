@echo off
setlocal
cd /d %~dp0
set MOCK_API_PORT=9050
node server.js
