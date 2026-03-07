import pandas as pd

excel_file = r'C:\Users\lhn\OneDrive\Desktop\江西\上饶电动侧预测\计划规模汇总及统计表（弋阳） 20260306.xlsx'

try:
    df_planned = pd.read_excel(excel_file, sheet_name='2026-2028年清单（弋阳）-新')
    print("Planned columns:", df_planned.columns.tolist())
    # drop rows where plan no is null if there is such column, else just print first 5 rows
    df_planned = df_planned.dropna(subset=['站点'])
    print(df_planned.head(10).to_string())
    print("Total rows:", len(df_planned))
except Exception as e:
    print("Error reading planned:", e)

excel_file_2 = r'C:\Users\lhn\OneDrive\Desktop\江西\上饶电动侧预测\基础数据统计（弋阳）-20260305.xlsx'
try:
    df_base = pd.read_excel(excel_file_2, sheet_name=None)
    for k, v in df_base.items():
        print("Sheet:", k)
        print("Cols:", v.columns.tolist())
        print(v.head(3).to_string())
except Exception as e:
    print("Error reading base:", e)

