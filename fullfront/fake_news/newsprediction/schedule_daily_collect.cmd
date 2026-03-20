@echo off
setlocal

set TASK_NAME=FakeNewsDailyCollect
set TASK_CMD=cmd /c ""%~dp0collect_daily_news.bat""

schtasks /Create /F /SC DAILY /ST 00:10 /TN "%TASK_NAME%" /TR "%TASK_CMD%"
if %ERRORLEVEL% EQU 0 (
  echo Scheduled task "%TASK_NAME%" created/updated.
) else (
  echo Failed to create scheduled task. Run this command as Administrator.
)

endlocal
