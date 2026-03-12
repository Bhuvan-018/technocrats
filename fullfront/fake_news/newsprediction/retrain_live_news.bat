@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "PY_EXE=D:\youngtechnocrats\.venv\Scripts\python.exe"

if not exist "%PY_EXE%" (
  echo [ERROR] Python environment not found at: %PY_EXE%
  exit /b 1
)

echo [INFO] Starting live-news augmentation and retraining...
cd /d "%ROOT_DIR%"
"%PY_EXE%" train_and_evaluate.py --live-news-per-feed 40

if errorlevel 1 (
  echo [ERROR] Retraining failed.
  exit /b 1
)

echo [INFO] Retraining completed successfully.
echo [INFO] Metrics file: %ROOT_DIR%training_metrics.json
exit /b 0
