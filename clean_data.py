import pandas as pd

# Load the raw data (same as before)
df = pd.read_csv("OnlineRetail.csv", encoding="ISO-8859-1")
print("BEFORE cleaning:", df.shape)

# Rule 1: Drop rows with no CustomerID
df = df.dropna(subset=["CustomerID"])

# Rule 2: Remove cancelled orders (InvoiceNo starting with "C")
df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]

# Rule 3: Remove non-positive Quantity or UnitPrice
df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]

# Rule 4: Convert InvoiceDate from text to a real date
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

print("AFTER cleaning:", df.shape)
print()
print(df.head())

# Save the cleaned version so future scripts don't have to redo this
df.to_csv("cleaned_data.csv", index=False)
print("\nSaved as cleaned_data.csv")