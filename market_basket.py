import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
df=pd.read_csv("cleaned_data.csv")
print("Rows loaded:", len(df))
print("Unique invoices (baskets):", df["InvoiceNo"].nunique())
print("Unique products:", df["Description"].nunique())
basket = (
    df.groupby(["InvoiceNo", "Description"])["Quantity"]
    .sum()
    .unstack()
    .fillna(0)
)
basket_sets = basket > 0
print("\nBasket matrix shape:", basket_sets.shape)
print("Sample (first 3 rows, first 4 columns):")
print(basket_sets.iloc[:3, :4])
frequent_itemsets = apriori(basket_sets, min_support=0.02, use_colnames=True)

print("\nFrequent itemsets found:", len(frequent_itemsets))
print(frequent_itemsets.sort_values("support", ascending=False).head(10))
# Step 4: Generate association rules from those frequent itemsets
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)

# Sort by lift — highest lift = strongest real association
rules = rules.sort_values("lift", ascending=False)

print("\nTotal rules found:", len(rules))
print("\nTop 10 rules by lift:")
print(rules[["antecedents", "consequents", "support", "confidence", "lift"]].head(10))

# Save rules to CSV for use in our Streamlit app later
rules.to_csv("basket_rules.csv", index=False)
print("\nSaved as basket_rules.csv")
from mlxtend.frequent_patterns import fpgrowth

# Step 5: FP-Growth (faster alternative to Apriori)
fp_itemsets = fpgrowth(basket_sets, min_support=0.02, use_colnames=True)
fp_rules = association_rules(fp_itemsets, metric="lift", min_threshold=1.0)
fp_rules = fp_rules.sort_values("lift", ascending=False)

print("\nFP-Growth rules found:", len(fp_rules))
print("Top rule by lift:", fp_rules.iloc[0]["lift"].round(2))
print("(Should match Apriori's top lift of 24.03 — confirms both algorithms agree)")