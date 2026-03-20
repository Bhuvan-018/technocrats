@echo off
setlocal
cd /d %~dp0

python train_and_evaluate.py --use-db --db-days 90 --live-news-per-feed 40 > retrain_weekly.log 2>&1

endlocal
