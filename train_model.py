# train_model.py  -  Step 4: train two models, compare them, save the best one
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CLEAN_PATH = "data/student_clean.csv"
MODEL_DIR = "model"
os.makedirs(MODEL_DIR, exist_ok=True)

# 1. LOAD the clean data
df = pd.read_csv(CLEAN_PATH)

# 2. CHOOSE inputs (X) and the answer we want to predict (y)
text_cols = ["Gender", "Department"]
number_cols = ["Attendance_Pct", "Study_Hours", "Previous_Score", "Assignments_Completed"]
X = df[text_cols + number_cols]
y = df["G3"]

# 3. SPLIT: 80% for studying (train), 20% hidden for the exam (test)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print("Training students:", len(X_train), "| Test students:", len(X_test))

# 4. PREPARE the data: words -> 0/1 columns, numbers -> same scale
prepare = ColumnTransformer([
    ("text", OneHotEncoder(handle_unknown="ignore"), text_cols),
    ("numbers", StandardScaler(), number_cols),
])

# 5. TWO candidate models
models = {
    "Linear Regression": LinearRegression(),
    "Random Forest": RandomForestRegressor(
        n_estimators=200, max_depth=8, min_samples_leaf=3, random_state=42
    ),
}

# 6. TRAIN and EVALUATE each one
results = {}
fitted = {}
for name, model in models.items():
    pipe = Pipeline([("prepare", prepare), ("model", model)])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)

    mae = mean_absolute_error(y_test, pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    r2 = r2_score(y_test, pred)
    cv_r2 = cross_val_score(pipe, X, y, cv=5, scoring="r2").mean()

    results[name] = {
        "MAE": round(mae, 3),
        "RMSE": round(rmse, 3),
        "R2": round(r2, 3),
        "CV_R2": round(float(cv_r2), 3),
    }
    fitted[name] = pipe
    print(f"\n{name}")
    print(f"  MAE  (average miss, in marks out of 20): {mae:.3f}")
    print(f"  RMSE (like MAE, punishes big misses)   : {rmse:.3f}")
    print(f"  R2   (1.0 = perfect, 0 = no better than guessing the average): {r2:.3f}")
    print(f"  5-fold CV R2 (a steadier check)        : {cv_r2:.3f}")

# 7. PICK the winner (highest R2 on the hidden test students)
best_name = max(results, key=lambda n: results[n]["R2"])
print("\nBest model:", best_name)

# 8. SAVE the winner and the report card
joblib.dump(fitted[best_name], f"{MODEL_DIR}/best_model.joblib")

report = {
    "best_model": best_name,
    "results": results,
    "features": text_cols + number_cols,
    "train_rows": len(X_train),
    "test_rows": len(X_test),
}
with open(f"{MODEL_DIR}/metrics.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"Saved {MODEL_DIR}/best_model.joblib and {MODEL_DIR}/metrics.json")