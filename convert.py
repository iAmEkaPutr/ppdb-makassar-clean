import pandas as pd

# Baca Excel (APA ADANYA)
df = pd.read_excel("data/ppdb.xlsx")

# Convert ke JSON TANPA mengubah data kosong
df.to_json(
    "public/ppdb.json",
    orient="records",
    force_ascii=False
)

print("✅ Convert selesai → public/ppdb.json")
print("Total baris:", len(df))
