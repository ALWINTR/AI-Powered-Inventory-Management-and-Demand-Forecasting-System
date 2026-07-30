import os
import joblib
import pandas as pd
import numpy as np

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from xgboost import XGBRegressor

# =====================================================
# CONFIGURATION
# =====================================================

INPUT_FILE = "merged_sales.xlsx"

MODEL_FILE = "inventory_xgb.pkl"
ITEM_ENCODER_FILE = "item_encoder.pkl"
UNIT_ENCODER_FILE = "unit_encoder.pkl"

# =====================================================
# CHECK INPUT FILE
# =====================================================

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"{INPUT_FILE} not found.")

print("=" * 60)
print("Loading Inventory Dataset...")
print("=" * 60)

df = pd.read_excel(INPUT_FILE)

print("Rows :", len(df))
print("Columns :", len(df.columns))
print()

# =====================================================
# REQUIRED COLUMNS
# =====================================================

required_columns = [

    "Date",

    "Itemcode",

    "Unit",

    "Op.Stock",

    "Purchase",

    "Sales Return",

    "Purchase Return",

    "Sales",

    "Other Inward",

    "Other Outward",

    "Balance",

    "Month"

]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    raise Exception(
        f"Missing columns: {missing}"
    )

# =====================================================
# DATE
# =====================================================

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

df["Year"] = df["Date"].dt.year

# =====================================================
# MONTH
# =====================================================

month_map = {

    "JANUARY": 1,
    "FEBRUARY": 2,
    "MARCH": 3,
    "APRIL": 4,
    "MAY": 5,
    "JUNE": 6,
    "JULY": 7,
    "AUGUST": 8,
    "SEPTEMBER": 9,
    "OCTOBER": 10,
    "NOVEMBER": 11,
    "DECEMBER": 12

}

df["Month"] = (
    df["Month"]
      .astype(str)
      .str.upper()
      .map(month_map)
)

# =====================================================
# NUMERIC COLUMNS
# =====================================================

numeric_cols = [

    "Op.Stock",

    "Purchase",

    "Sales Return",

    "Purchase Return",

    "Sales",

    "Other Inward",

    "Other Outward",

    "Balance"

]

for col in numeric_cols:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    ).fillna(0)

# =====================================================
# REMOVE INVALID ROWS
# =====================================================

df = df.dropna(
    subset=["Itemcode"]
)

df = df.reset_index(drop=True)

print("Rows after cleaning :", len(df))

# =====================================================
# LABEL ENCODERS
# =====================================================

item_encoder = LabelEncoder()

df["Item_ID"] = item_encoder.fit_transform(
    df["Itemcode"].astype(str)
)

joblib.dump(
    item_encoder,
    ITEM_ENCODER_FILE
)

unit_encoder = LabelEncoder()

df["Unit_ID"] = unit_encoder.fit_transform(
    df["Unit"].astype(str)
)

joblib.dump(
    unit_encoder,
    UNIT_ENCODER_FILE
)

print("Item encoder saved.")
print("Unit encoder saved.")
print()
# =====================================================
# FEATURE ENGINEERING
# =====================================================

print("=" * 60)
print("Preparing Training Data...")
print("=" * 60)

feature_columns = [

    "Item_ID",

    "Unit_ID",

    "Year",

    "Month",

    "Op.Stock",

    "Purchase",

    "Sales Return",

    "Purchase Return",

    "Other Inward",

    "Other Outward",

    "Balance"

]

target_column = "Sales"

X = df[feature_columns]

y = df[target_column]

print("Total Samples :", len(X))
print("Features      :", len(feature_columns))
print()

# =====================================================
# TRAIN / TEST SPLIT
# =====================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,

    y,

    test_size=0.20,

    random_state=42,

    shuffle=True

)

print("Training Samples :", len(X_train))
print("Testing Samples  :", len(X_test))
print()

# =====================================================
# BUILD XGBOOST MODEL
# =====================================================

print("=" * 60)
print("Training XGBoost Model...")
print("=" * 60)

model = XGBRegressor(

    objective="reg:squarederror",

    n_estimators=500,

    learning_rate=0.05,

    max_depth=8,

    min_child_weight=3,

    subsample=0.8,

    colsample_bytree=0.8,

    gamma=0,

    reg_alpha=0,

    reg_lambda=1,

    random_state=42,

    n_jobs=-1

)

# =====================================================
# TRAIN MODEL
# =====================================================

model.fit(

    X_train,

    y_train,

    verbose=True

)

print()
print("Model training completed successfully.")
print()

# =====================================================
# SAVE MODEL
# =====================================================

joblib.dump(

    model,

    MODEL_FILE

)

print("Saved :", MODEL_FILE)
print()
# =====================================================
# MODEL EVALUATION
# =====================================================

print("=" * 60)
print("Evaluating Model...")
print("=" * 60)

y_pred = model.predict(X_test)

mae = mean_absolute_error(
    y_test,
    y_pred
)

mse = mean_squared_error(
    y_test,
    y_pred
)

rmse = np.sqrt(mse)

r2 = r2_score(
    y_test,
    y_pred
)

print()

print(f"MAE  : {mae:.4f}")
print(f"MSE  : {mse:.4f}")
print(f"RMSE : {rmse:.4f}")
print(f"R²   : {r2:.4f}")

print()

# =====================================================
# FEATURE IMPORTANCE
# =====================================================

importance = pd.DataFrame({

    "Feature": feature_columns,

    "Importance": model.feature_importances_

})

importance = importance.sort_values(

    by="Importance",

    ascending=False

)

print("=" * 60)
print("Feature Importance")
print("=" * 60)

print(importance)

print()

# =====================================================
# SAMPLE PREDICTIONS
# =====================================================

comparison = pd.DataFrame({

    "Actual Sales": y_test.values,

    "Predicted Sales": np.round(
        y_pred,
        2
    )

})

comparison["Error"] = np.round(

    comparison["Predicted Sales"] -
    comparison["Actual Sales"],

    2

)

print("=" * 60)
print("Prediction Sample")
print("=" * 60)

print(comparison.head(20))

print()

# =====================================================
# SAVE FEATURE IMPORTANCE
# =====================================================

importance.to_excel(

    "feature_importance.xlsx",

    index=False

)

print("Saved feature_importance.xlsx")

print()
# =====================================================
# DATASET SUMMARY
# =====================================================

print("=" * 60)
print("Dataset Summary")
print("=" * 60)

print(f"Total Records        : {len(df)}")
print(f"Unique Items         : {df['Itemcode'].nunique()}")
print(f"Unique Units         : {df['Unit'].nunique()}")
print(f"Training Samples     : {len(X_train)}")
print(f"Testing Samples      : {len(X_test)}")
print()

# =====================================================
# TRAINING REPORT
# =====================================================

report = pd.DataFrame({

    "Metric": [
        "MAE",
        "MSE",
        "RMSE",
        "R2 Score",
        "Training Samples",
        "Testing Samples",
        "Total Records",
        "Unique Items"
    ],

    "Value": [
        round(mae, 4),
        round(mse, 4),
        round(rmse, 4),
        round(r2, 4),
        len(X_train),
        len(X_test),
        len(df),
        df["Itemcode"].nunique()
    ]

})

report.to_excel(
    "training_report.xlsx",
    index=False
)

print("Saved : training_report.xlsx")
print()

# =====================================================
# TOP 10 IMPORTANT FEATURES
# =====================================================

print("=" * 60)
print("Top 10 Features")
print("=" * 60)

print(importance.head(10))

print()

# =====================================================
# MODEL INFORMATION
# =====================================================

print("=" * 60)
print("Model Information")
print("=" * 60)

print("Algorithm       : XGBoost Regressor")
print("Objective       : reg:squarederror")
print("Estimators      :", model.n_estimators)
print("Learning Rate   :", model.learning_rate)
print("Max Depth       :", model.max_depth)
print()

# =====================================================
# GENERATED FILES
# =====================================================

generated_files = [

    MODEL_FILE,
    ITEM_ENCODER_FILE,
    UNIT_ENCODER_FILE,
    "feature_importance.xlsx",
    "training_report.xlsx"

]

print("=" * 60)
print("Generated Files")
print("=" * 60)

for file in generated_files:

    if os.path.exists(file):
        print(f"[OK] {file}")
    else:
        print(f"[MISSING] {file}")

print()

# =====================================================
# FINISHED
# =====================================================

print("=" * 60)
print("AI Inventory Model Training Completed Successfully")
print("=" * 60)

print("""
Next Steps:

1. Run prediction.py

2. It will load:
   - inventory_xgb.pkl
   - item_encoder.pkl
   - merged_sales.xlsx

3. It will generate:
   predictions.xlsx

4. Launch the Flask application:

   python app.py
""")
