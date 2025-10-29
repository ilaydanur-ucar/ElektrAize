@echo off
echo Paketler kuruluyor...
python -m pip install pandas numpy scikit-learn --quiet
echo.
echo Temel paketler hazir. XGBoost icin (opsiyonel):
echo python -m pip install xgboost
echo.
pause


