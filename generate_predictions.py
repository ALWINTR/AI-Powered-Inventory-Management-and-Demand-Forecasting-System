import pandas as pd
import joblib

# Load model
model = joblib.load("inventory_xgb.pkl")
encoder = joblib.load("item_encoder.pkl")

# Load Excel
df = pd.read_excel("sales.xlsx", sheet_name="MergedData")
df["Date"] = pd.to_datetime(df["Date"])

# Latest record for each item
latest_df = (
    df.sort_values("Date")
      .groupby("Itemcode")
      .tail(1)
      .reset_index(drop=True)
)

results = []

for _, row in latest_df.iterrows():

    itemcode = str(row["Itemcode"])

    try:
        item_id = encoder.transform([itemcode])[0]
    except:
        continue

    sample = pd.DataFrame([{
        "Item_ID": item_id,
        "Year": row["Date"].year,
        "Month": row["Date"].month + 1,
        "Op.Stock": row["Op.Stock"],
        "Purchase": row["Purchase"],
        "Sales Return": row["Sales Return"],
        "Purchase Return": row["Purchase Return"],
        "Other Inward": row["Other Inward"],
        "Other Outward": row["Other Outward"],
        "Balance": row["Balance"]
    }])

    forecast = float(model.predict(sample)[0])

    safety_stock = forecast * 0.20

    purchase_qty = max(
        0,
        forecast + safety_stock - row["Balance"]
    )

    if row["Balance"] == 0:
        status = "Stock Out"
    elif purchase_qty > 0:
        status = "Purchase Required"
    elif row["Purchase"] == 0:
        status = "Not Purchased"
    else:
        status = "OK"

    results.append({
        "Itemcode": itemcode,
        "Current_Stock": int(row["Balance"]),
        "Forecast": round(forecast),
        "Safety_Stock": round(safety_stock),
        "Purchase_Qty": round(purchase_qty),
        "Status": status
    })

pred_df = pd.DataFrame(results)

pred_df.to_excel("predictions.xlsx", index=False)

print("Done!")
print("Saved predictions.xlsx")
