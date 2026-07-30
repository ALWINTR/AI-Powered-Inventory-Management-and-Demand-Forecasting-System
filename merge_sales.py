import os
import pandas as pd

INPUT_FILE = "sales.xlsx"
OUTPUT_FILE = "merged_sales.xlsx"

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"{INPUT_FILE} not found.")

excel = pd.ExcelFile(INPUT_FILE)

print("Sheets found:")
print(excel.sheet_names)
print()

merged_df = pd.DataFrame()

for sheet in excel.sheet_names:

    print(f"Reading: {sheet}")

    df = pd.read_excel(INPUT_FILE, sheet_name=sheet)

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Remove completely empty columns
    df = df.dropna(axis=1, how="all")

    # Add month name if not already present
    if "Month" not in df.columns:
        df["Month"] = sheet

    merged_df = pd.concat([merged_df, df], ignore_index=True)

print("\nTotal rows before duplicate removal:", len(merged_df))

merged_df = merged_df.drop_duplicates()

print("Total rows after duplicate removal :", len(merged_df))

# Sort by Date if available
if "Date" in merged_df.columns:
    merged_df["Date"] = pd.to_datetime(
        merged_df["Date"],
        errors="coerce"
    )
    merged_df = merged_df.sort_values("Date")

merged_df.reset_index(drop=True, inplace=True)

merged_df.to_excel(
    OUTPUT_FILE,
    index=False
)

print("\nMerged file saved as:", OUTPUT_FILE)
print("Done.")
