# -*- coding: utf-8 -*-
"""读取所有Excel sheet完整内容"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳县充换电申报材料\充换电申报材料"
DATA_DIR = BASE + r"\data"

# ── 1. 各乡镇充电桩数量 ──────────────────────────
print("="*60)
print("【各乡镇充电桩数量】")
df1 = pd.read_excel(DATA_DIR + r"\各乡镇充电桩数量.xls", sheet_name="Sheet1",
                    header=1, engine="xlrd")
df1.columns = ["序号","乡镇名称","坐落","数量","备注"]
df1 = df1.dropna(subset=["序号"]).copy()
df1["数量"] = pd.to_numeric(df1["数量"], errors="coerce")
print(df1.to_string(index=False))

# ── 2. 基础数据统计 ──────────────────────────
print("\n" + "="*60)
print("【历年社会经济+汽车数据】")
xl2 = pd.ExcelFile(DATA_DIR + r"\基础数据统计（弋阳）(2).xlsx", engine="openpyxl")
df2 = xl2.parse("基础数据统计", header=None)
# 取第0列=弋阳, 第1列=年份
print(df2.to_string())

print("\n" + "="*60)
print("【弋阳现状2025年充电设施】")
df3 = xl2.parse("弋阳现状(2025年）", header=None)
print(df3.to_string())

# ── 3. 城区充电站（含坐标） ──────────────────────────
print("\n" + "="*60)
print("【城区充电站坐标表】")
df4 = pd.read_excel(DATA_DIR + r"\弋阳县城范围内充电站.xlsx", header=None, engine="openpyxl")
# 数据从第5行开始
df4_data = df4.iloc[4:].copy()
df4_data.columns = ["场站名称","位置","高德经度","高德纬度","场站照片","处理结果"]
df4_data = df4_data[df4_data["场站名称"].notna() & (df4_data["场站名称"] != "品牌+汽车充电站（站名）")].copy()
df4_data = df4_data[df4_data["场站名称"].astype(str).str.strip() != "场站名称"].copy()
print(df4_data.to_string(index=False))

# ── 4. 规划清单2026-2028 ──────────────────────────
print("\n" + "="*60)
print("【2026-2028规划充电站清单】")
xl4 = pd.ExcelFile(DATA_DIR + r"\计划规模汇总及统计表（弋阳）.xlsx", engine="openpyxl")
df5 = xl4.parse("2026-2028年清单（弋阳）", header=0)
print(df5.to_string())

# ── 5. 加油站详情 ──────────────────────────
print("\n" + "="*60)
print("【加油站详情（2024）】")
df6 = pd.read_excel(DATA_DIR + r"\（弋阳县）附表3：2024年度江西省加油站详细情况登记表.xls",
                    header=None, engine="xlrd")
# 数据从第5行开始
rows = df6.iloc[5:].copy()
cols = ["所属县","加油站总数","加油站名称","加油站详细地址",
        "中石化","中石油","中化","中海油","其他国有","民营",
        "自行经营","租赁经营","特许经营",
        "汽油销量","柴油销量","合计销量",
        "万吨以上","5千-1万吨","3千-5千吨","3千吨以下",
        "城区","省道国道","县乡道农网","高速公路","水域","其他",
        "成品油证书编号","成品油证书有效期","危化品证书编号","危化品证书有效期",
        "统一社会信用代码","建站时间","总储油能力","是否有充电设施",
        "成品油销售收入","非油品销售收入","法定代表人","联系电话"]
rows.columns = cols
rows = rows[rows["加油站名称"].notna()].copy()
key_cols = ["所属县","加油站名称","加油站详细地址","汽油销量","柴油销量","合计销量","总储油能力","是否有充电设施","成品油销售收入"]
print(rows[key_cols].to_string(index=False))

# ── 6. 欠款表 ──────────────────────────
print("\n" + "="*60)
print("【2026年欠款情况】")
df7 = pd.read_excel(DATA_DIR + r"\弋阳县2026年欠款情况汇总表.xlsx", header=1, engine="openpyxl")
print(df7.to_string())
