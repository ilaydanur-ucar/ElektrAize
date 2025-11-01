# xgboost_model.py
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, r2_score
from veri_cek import get_train_test

X_train, X_test, y_train, y_test = get_train_test()

xgb_model = XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
xgb_model.fit(X_train, y_train)
y_pred = xgb_model.predict(X_test)

print("XGBoost MSE:", mean_squared_error(y_test, y_pred))
print("XGBoost R2 :", r2_score(y_test, y_pred))
