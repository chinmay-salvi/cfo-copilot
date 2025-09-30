import pandas as pd

# Path to the Excel file
excel_file = 'data.xlsx'

# Load the Excel file
xls = pd.ExcelFile(excel_file)

# Loop through each sheet and save as CSV
for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    csv_file = f"{sheet_name}.csv"
    df.to_csv(csv_file, index=False)
    print(f"Saved {sheet_name} to {csv_file}")
