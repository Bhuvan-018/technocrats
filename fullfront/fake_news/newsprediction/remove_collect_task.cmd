@echo off
setlocal

set TASK_NAME=FakeNewsDailyCollect
schtasks /Delete /TN "%TASK_NAME%" /F

endlocal
