import os
import joblib
import pandas as pd
import numpy as np

# ============================================
# CONFIGURATION
# ============================================

MODEL_FILE = "inventory_xgb.pkl"
ITEM_ENCODER_FILE = "item_encoder.pkl"
UNIT_ENCODER_FILE = "unit_encoder.pkl"

INPUT_FILE = "merged_sales.xlsx"

OUTPUT_FILE = "predictions.xlsx"

# ============================================
# CHECK FILES
# ============================================

files = [
    MODEL_FILE,
    ITEM_ENCODER_FILE,
    UNIT_ENCODER_FILE,
    INPUT_FILE
]

for f in files:

    if not os.path.exists(f):

        raise FileNotFoundError(f"{f} not found.")

print("="*60)
print("Loading AI Inventory Prediction Model")
print("="*60)

model = joblib.load(MODEL_FILE)

item_encoder = joblib.load(
    ITEM_ENCODER_FILE
)

unit_encoder = joblib.load(
    UNIT_ENCODER_FILE
)

df = pd.read_excel(INPUT_FILE)

df["Date"] = pd.to_datetime(df["Date"])

# ============================================
# MONTH MAP
# ============================================

month_map = {

    1:"JAN",

    2:"FEB",

    3:"MAR",

    4:"APR",

    5:"MAY",

    6:"JUN",

    7:"JUL",

    8:"AUG",

    9:"SEP",

    10:"OCT",

    11:"NOV",

    12:"DEC"

}

# ============================================
# LATEST RECORD OF EACH ITEM
# ============================================

latest = (

    df

    .sort_values("Date")

    .groupby("Itemcode")

    .tail(1)

    .reset_index(drop=True)

)

print("Items :",len(latest))

results=[]

print()

print("Predicting...")
# ============================================
# START PREDICTION
# ============================================

for _, row in latest.iterrows():

    itemcode = str(row["Itemcode"])
    unit = str(row["Unit"])

    try:

        item_id = item_encoder.transform([itemcode])[0]
        unit_id = unit_encoder.transform([unit])[0]

    except Exception:

        print(f"Skipping {itemcode}")
        continue

    current_stock = float(row["Balance"])

    purchase = float(row["Purchase"])

    sales_return = float(row["Sales Return"])

    purchase_return = float(row["Purchase Return"])

    other_inward = float(row["Other Inward"])

    other_outward = float(row["Other Outward"])

    year = int(row["Date"].year)

    month = int(row["Date"].month)

    monthly_prediction = []

    stock_simulation = current_stock

    # ----------------------------------------
    # Predict Next 6 Months
    # ----------------------------------------

    for i in range(6):

        pred_month = month + 1

        pred_year = year

        if pred_month > 12:

            pred_month = 1
            pred_year += 1
            month = 0
            year = pred_year

        features = pd.DataFrame([{

            "Item_ID": item_id,

            "Unit_ID": unit_id,

            "Year": pred_year,

            "Month": pred_month,

            "Op.Stock": stock_simulation,

            "Purchase": purchase,

            "Sales Return": sales_return,

            "Purchase Return": purchase_return,

            "Other Inward": other_inward,

            "Other Outward": other_outward,

            "Balance": stock_simulation

        }])

        forecast = float(model.predict(features)[0])

        forecast = max(0, round(forecast))

        monthly_prediction.append(forecast)

        # simulate inventory after forecast sales
        stock_simulation = max(
            0,
            stock_simulation - forecast
        )

        month = pred_month

    # ----------------------------------------
    # Individual Month Predictions
    # ----------------------------------------

    next_month_prediction = monthly_prediction[0]

    month1 = monthly_prediction[0]
    month2 = monthly_prediction[1]
    month3 = monthly_prediction[2]
    month4 = monthly_prediction[3]
    month5 = monthly_prediction[4]
    month6 = monthly_prediction[5]

    total_prediction = sum(monthly_prediction)
        # ============================================
    # INVENTORY ANALYSIS
    # ============================================

    avg_monthly_sales = round(
        np.mean(monthly_prediction),
        2
    )

    safety_stock = round(
        avg_monthly_sales * 0.20
    )

    reorder_level = round(
        avg_monthly_sales + safety_stock
    )

    purchase_qty = max(

        0,

        round(

            total_prediction +
            safety_stock -
            current_stock

        )

    )

    # --------------------------------------------
    # Dead Stock Detection
    # --------------------------------------------

    dead_stock = all(x == 0 for x in monthly_prediction)

    # --------------------------------------------
    # Slow Moving Stock
    # --------------------------------------------

    slow_moving = (

        avg_monthly_sales > 0 and

        avg_monthly_sales <= 5

    )

    # --------------------------------------------
    # Overstock
    # --------------------------------------------

    overstock = (

        current_stock >

        total_prediction * 2

    )

    # --------------------------------------------
    # Stock Out
    # --------------------------------------------

    stock_out = current_stock == 0

    # --------------------------------------------
    # Estimate Stock-Out Month
    # --------------------------------------------

    remaining_stock = current_stock

    stock_out_month = "Safe"

    for i, demand in enumerate(monthly_prediction):

        remaining_stock -= demand

        if remaining_stock <= 0:

            future_month = (

                row["Date"].month +

                i +

                1

            )

            future_year = row["Date"].year

            while future_month > 12:

                future_month -= 12
                future_year += 1

            stock_out_month = (

                f"{month_map[future_month]}-{future_year}"

            )

            break

    # --------------------------------------------
    # Final Status
    # --------------------------------------------

    if stock_out:

        status = "Stock Out"

    elif dead_stock:

        status = "Dead Stock"

    elif purchase_qty > 0:

        status = "Purchase Required"

    elif slow_moving:

        status = "Slow Moving"

    elif overstock:

        status = "Overstock"

    else:

        status = "OK"

    # --------------------------------------------
    # Save Result
    # --------------------------------------------

    results.append({

        "Itemcode": itemcode,

        "Unit": unit,

        "Current_Stock": round(current_stock),

        "Next_Month": next_month_prediction,

        "Month_1": month1,

        "Month_2": month2,

        "Month_3": month3,

        "Month_4": month4,

        "Month_5": month5,

        "Month_6": month6,

        "Total_6_Months": total_prediction,

        "Average_Monthly_Sales": avg_monthly_sales,

        "Safety_Stock": safety_stock,

        "Reorder_Level": reorder_level,

        "Purchase_Qty": purchase_qty,

        "Stock_Out_Month": stock_out_month,

        "Dead_Stock": "YES" if dead_stock else "NO",

        "Slow_Moving": "YES" if slow_moving else "NO",

        "Overstock": "YES" if overstock else "NO",

        "Status": status

    })
    # ============================================
# CREATE DATAFRAME
# ============================================

pred_df = pd.DataFrame(results)

# ============================================
# PRIORITY LEVEL
# ============================================

def get_priority(status):

    if status == "Stock Out":
        return "Critical"

    elif status == "Purchase Required":
        return "High"

    elif status == "Dead Stock":
        return "High"

    elif status == "Slow Moving":
        return "Medium"

    elif status == "Overstock":
        return "Medium"

    else:
        return "Low"


pred_df["Priority"] = pred_df["Status"].apply(get_priority)

# ============================================
# SORT ITEMS
# ============================================

priority_order = {

    "Critical": 1,

    "High": 2,

    "Medium": 3,

    "Low": 4

}

pred_df["Sort"] = pred_df["Priority"].map(priority_order)

pred_df = pred_df.sort_values(

    ["Sort", "Purchase_Qty"],

    ascending=[True, False]

)

pred_df.drop(columns=["Sort"], inplace=True)

# ============================================
# SAVE EXCEL
# ============================================

pred_df.to_excel(

    OUTPUT_FILE,

    index=False

)

# ============================================
# SUMMARY
# ============================================

print()
print("=" * 70)
print("AI INVENTORY PREDICTION COMPLETED")
print("=" * 70)

print(f"Total Items              : {len(pred_df)}")

print(f"Stock Out                : {(pred_df['Status']=='Stock Out').sum()}")

print(f"Purchase Required        : {(pred_df['Status']=='Purchase Required').sum()}")

print(f"Dead Stock               : {(pred_df['Status']=='Dead Stock').sum()}")

print(f"Slow Moving              : {(pred_df['Status']=='Slow Moving').sum()}")

print(f"Overstock                : {(pred_df['Status']=='Overstock').sum()}")

print(f"Healthy Items            : {(pred_df['Status']=='OK').sum()}")

print()

print("Prediction file saved as:")

print(f"   {OUTPUT_FILE}")

print("=" * 70)

# ============================================
# TOP PURCHASE ITEMS
# ============================================

print()
print("TOP 10 PURCHASE RECOMMENDATIONS")
print("=" * 70)

purchase_df = pred_df[
    pred_df["Purchase_Qty"] > 0
]

if not purchase_df.empty:

    print(

        purchase_df[[
            "Itemcode",
            "Current_Stock",
            "Purchase_Qty",
            "Status"
        ]].head(10)

    )

else:

    print("No purchase required.")

print()

# ============================================
# DEAD STOCK REPORT
# ============================================

dead_df = pred_df[
    pred_df["Dead_Stock"] == "YES"
]

print("Dead Stock Items :", len(dead_df))

# ============================================
# STOCK OUT REPORT
# ============================================

stockout_df = pred_df[
    pred_df["Status"] == "Stock Out"
]

print("Stock Out Items :", len(stockout_df))

# ============================================
# FINISH
# ============================================

print()
print("Prediction Finished Successfully.")
