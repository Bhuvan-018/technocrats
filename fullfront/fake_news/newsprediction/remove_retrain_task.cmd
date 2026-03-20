@echo off
setlocal

set TASK_NAME=FakeNewsWeeklyRetrain
schtasks /Delete /TN "%TASK_NAME%" /F

endlocal
