@echo off
setlocal

set TASK_NAME=FakeNewsWeeklyRetrain
set TASK_CMD=cmd /c ""%~dp0retrain_weekly.bat""

schtasks /Create /F /SC WEEKLY /D SUN /ST 00:00 /TN "%TASK_NAME%" /TR "%TASK_CMD%"
if %ERRORLEVEL% EQU 0 (
  echo Scheduled task "%TASK_NAME%" created/updated.
) else (
  echo Failed to create scheduled task. Run this command as Administrator.
)

endlocal
