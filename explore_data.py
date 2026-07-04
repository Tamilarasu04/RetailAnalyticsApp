import pandas as pd

df = pd.read_csv("OnlineRetail.csv", encoding="ISO-8859-1")

print("Shape (rows, columns):", df.shape)
print()
print("Column names:", list(df.columns))
print()
print("First 5 rows:")
print(df.head())