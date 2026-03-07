import pandas as pd
import sqlite3

excel_file = r'C:\Users\lhn\OneDrive\Desktop\江西\上饶电动侧预测\基础数据统计（弋阳）-20260305.xlsx'
df_dict = pd.read_excel(excel_file, sheet_name=None)
keys = list(df_dict.keys())
print("Sheets:", keys)

df_existing = df_dict[keys[1]] # 弋阳现状
print(df_existing.head(10).to_string())
