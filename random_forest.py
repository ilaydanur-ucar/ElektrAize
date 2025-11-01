# random_forest_model.py
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from veri_cek import get_train_test

X_train, X_test, y_train, y_test = get_train_test()

rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
y_pred = rf_model.predict(X_test)

print("Random Forest MSE:", mean_squared_error(y_test, y_pred))
print("Random Forest R2 :", r2_score(y_test, y_pred))
