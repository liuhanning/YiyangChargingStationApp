# -*- coding: utf-8 -*-
"""
弋阳县充电桩规划 - 数据探查脚本
运行此脚本了解所有Excel文件的结构
"""
import pandas as pd
import os
import sys

# 确保输出UTF-8
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳县充换电申报材料\充换电申报材料"
DATA_DIR = os.path.join(BASE, "data")

files = [f for f in os.listdir(DATA_DIR) if not f.startswith("~$") and (f.endswith(".xls") or f.endswith(".xlsx"))]

for f in sorted(files):
    fp = os.path.join(DATA_DIR, f)
    print("=" * 70)
    print(f"文件: {f}")
    try:
        eng = "xlrd" if f.endswith(".xls") else "openpyxl"
        xl = pd.ExcelFile(fp, engine=eng)
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None)
            if df.empty:
                continue
            print(f"  [Sheet: {sheet}]  行:{df.shape[0]}  列:{df.shape[1]}")
            # 打印前10行，展示结构
            with pd.option_context('display.max_columns', 20, 'display.width', 200, 'display.max_colwidth', 40):
                print(df.head(10).to_string())
            print()
    except Exception as e:
        print(f"  错误: {e}")

print("\n探查完成")
