import os
import joblib
import pandas as pd
import numpy as np

MODEL_FILE = "inventory_xgb.pkl"
ENCODER_FILE = "item_encoder.pkl"
INPUT_FILE = "sales.xlsx"
OUTPUT_FILE = "predictions.xlsx"


def main():

    # ----------------------------
    # Check files
    # ----------------------------

    for file in [MODEL_FILE, ENCODER_FILE, INPUT_FILE]:

        if not os.path.exists(file):
            print(f"Missing file: {file}")
            return

    print("Loading model...")

    model = joblib.load(MODEL_FILE)
    encoder = joblib.load(ENCODER_FILE)

    print("Reading Excel...")

    df = pd.read_excel(INPUT_FILE, sheet_name="MergedData")

    df["Date"] = pd.to_datetime(df["Date"])

    numeric_columns = [
        "Op.Stock",
        "Purchase",
        "Sales Return",
        "Purchase Return",
        "Other Inward",
        "Other Outward",
        "Balance"
    ]

    df[numeric_columns] = df[numeric_columns].fillna(0)

    latest_df = (
        df.sort_values("Date")
          .groupby("Itemcode")
          .tail(1)
          .reset_index(drop=True)
    )

    predictions = []

    print("Generating predictions...")

    for _, row in latest_df.iterrows():

        itemcode = str(row["Itemcode"])

        try:

            item_id = encoder.transform([itemcode])[0]

        except Exception:

            print(f"Skipped unknown item: {itemcode}")

            continue

        next_month = row["Date"].month + 1
        next_year = row["Date"].year

        if next_month > 12:
            next_month = 1
            next_year += 1

        sample = pd.DataFrame([{

            "Item_ID": item_id,

            "Year": next_year,

            "Month": next_month,

            "Op.Stock": row["Op.Stock"],

            "Purchase": row["Purchase"],

            "Sales Return": row["Sales Return"],

            "Purchase Return": row["Purchase Return"],

            "Other Inward": row["Other Inward"],

            "Other Outward": row["Other Outward"],

            "Balance": row["Balance"]

        }])

        forecast = float(model.predict(sample)[0])

        forecast = max(0, forecast)

        safety_stock = round(forecast * 0.20)

        purchase_qty = max(
            0,
            round(forecast + safety_stock - row["Balance"])
        )

        current_stock = int(row["Balance"])

        if current_stock == 0:

            status = "Stock Out"

        elif purchase_qty > 0:

            status = "Purchase Required"

        elif forecast == 0:

            status = "Dead Stock"

        elif row["Purchase"] == 0:

            status = "Not Purchased"

        else:

            status = "OK"

        predictions.append({

            "Itemcode": itemcode,

            "Current_Stock": current_stock,

            "Forecast": round(forecast),

            "Safety_Stock": safety_stock,

            "Purchase_Qty": purchase_qty,

            "Status": status

        })

    prediction_df = pd.DataFrame(predictions)

    prediction_df = prediction_df.sort_values(
        ["Status", "Purchase_Qty"],
        ascending=[True, False]
    )

    prediction_df.to_excel(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("=" * 50)
    print("Prediction completed successfully")
    print(f"Total Items : {len(prediction_df)}")
    print(f"Output File : {OUTPUT_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    main()
