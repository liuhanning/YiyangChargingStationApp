# -*- coding: utf-8 -*-
"""
弋阳县充电桩规划 - 数据入库脚本
将所有Excel数据导入SQLite数据库
"""
import pandas as pd
import sqlite3
import os
import sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳县充换电申报材料\充换电申报材料"
DATA_DIR = os.path.join(BASE, "data")
DB_PATH = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ─────────────────────────────────────────────────────────
# 表1：历年社会经济 & 汽车数据
# ─────────────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS economic_stats")
cur.execute("""
CREATE TABLE economic_stats (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    region      TEXT,    -- 弋阳 / 上饶
    year        INTEGER,
    car_total   REAL,    -- 汽车保有量（万辆）
    car_new     REAL,    -- 年度新增汽车（万辆）
    nev_total   REAL,    -- 新能源车保有量（万辆）
    nev_new     REAL,    -- 年度新增新能源汽车（万辆）
    nev_rate    REAL,    -- 渗透率（%）
    gdp         REAL,    -- GDP（亿元）
    fiscal_rev  REAL,    -- 财政收入（亿元）
    population  REAL,    -- 常住人口（万人）
    remark      TEXT
)
""")

xl2 = pd.ExcelFile(os.path.join(DATA_DIR, "基础数据统计（弋阳）(2).xlsx"), engine="openpyxl")
raw = xl2.parse("基础数据统计", header=None)

rows_to_insert = []
# 弋阳数据：行2-11（index 2~11），region='弋阳'
# 上饶数据：行12-21（index 12~21），region='上饶'
region_map = {2: '弋阳', 12: '上饶'}
for start, region in region_map.items():
    for i in range(start, start + 10):
        row = raw.iloc[i]
        year_val = row[1]
        if pd.isna(year_val):
            continue
        try:
            year = int(float(str(year_val).replace('待公布', '')))
        except:
            continue
        def safe(v):
            if pd.isna(v): return None
            try: return float(str(v).replace('待公布','').replace('无数据',''))
            except: return None
        rows_to_insert.append((
            region, year,
            safe(row[2]), safe(row[3]), safe(row[4]), safe(row[5]), safe(row[6]),
            safe(row[16]), safe(row[17]), safe(row[18]),
            str(row[19]) if not pd.isna(row[19]) else None
        ))

cur.executemany("""
INSERT INTO economic_stats
(region,year,car_total,car_new,nev_total,nev_new,nev_rate,gdp,fiscal_rev,population,remark)
VALUES (?,?,?,?,?,?,?,?,?,?,?)
""", rows_to_insert)
print(f"[表1] economic_stats 写入 {len(rows_to_insert)} 条")

# ─────────────────────────────────────────────────────────
# 表2：各乡镇现有充电桩
# ─────────────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS stations_existing_township")
cur.execute("""
CREATE TABLE stations_existing_township (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    seq        INTEGER,
    township   TEXT,    -- 乡镇名称
    location   TEXT,    -- 坐落
    quantity   INTEGER, -- 数量（台）
    spec       TEXT     -- 备注/规格
)
""")

df1 = pd.read_excel(
    os.path.join(DATA_DIR, "各乡镇充电桩数量.xls"),
    sheet_name="Sheet1", header=1, engine="xlrd"
)
df1.columns = ["序号","乡镇名称","坐落","数量","备注"]
df1 = df1.dropna(subset=["序号"]).copy()
df1["数量"] = pd.to_numeric(df1["数量"], errors="coerce")

rows2 = []
for _, r in df1.iterrows():
    rows2.append((
        int(r["序号"]), str(r["乡镇名称"]).strip(),
        str(r["坐落"]).strip(),
        int(r["数量"]) if not pd.isna(r["数量"]) else 0,
        str(r["备注"]).strip() if not pd.isna(r["备注"]) else None
    ))
cur.executemany("""
INSERT INTO stations_existing_township (seq,township,location,quantity,spec)
VALUES (?,?,?,?,?)
""", rows2)
print(f"[表2] stations_existing_township 写入 {len(rows2)} 条")

# ─────────────────────────────────────────────────────────
# 表3：2025年充电设施现状（含各乡镇明细）
# ─────────────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS stations_status_2025")
cur.execute("""
CREATE TABLE stations_status_2025 (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    township       TEXT,    -- 乡镇
    station_name   TEXT,    -- 充电站名称
    quantity       INTEGER, -- 数量（台）
    swap_stations  INTEGER, -- 换电站（座）
    total_power_kw REAL,    -- 总功率（kW）
    power_util_pct REAL,    -- 功率利用率（%）
    above_120kw    INTEGER, -- 120kW以上的充电桩数量（台）
    scene          TEXT,    -- 应用场景
    tech_mode      TEXT,    -- 新技术新模式应用
    build_year     INTEGER, -- 建设年度
    car_pile_ratio REAL     -- 车桩比
)
""")

xl2b = pd.ExcelFile(os.path.join(DATA_DIR, "基础数据统计（弋阳）(2).xlsx"), engine="openpyxl")
raw3 = xl2b.parse("弋阳现状(2025年）", header=None)

rows3 = []
cur_township = None
for i in range(4, len(raw3)):
    row = raw3.iloc[i]
    # 列1 = 乡镇
    t = row[1]
    if not pd.isna(t) and str(t).strip() not in ('', 'nan'):
        cur_township = str(t).strip()
    # 列4 = 站点名称
    name = row[4]
    if pd.isna(name) or str(name).strip() in ('', 'nan'):
        continue
    def safe_int(v):
        if pd.isna(v): return None
        try: return int(float(v))
        except: return None
    def safe_float(v):
        if pd.isna(v): return None
        try: return float(v)
        except: return None
    rows3.append((
        cur_township, str(name).strip(),
        safe_int(row[5]), safe_int(row[6]),
        safe_float(row[7]), safe_float(row[8]), safe_int(row[9]),
        str(row[10]).strip() if not pd.isna(row[10]) else None,
        str(row[11]).strip() if not pd.isna(row[11]) else None,
        safe_int(row[12]), safe_float(row[13])
    ))

cur.executemany("""
INSERT INTO stations_status_2025
(township,station_name,quantity,swap_stations,total_power_kw,power_util_pct,
 above_120kw,scene,tech_mode,build_year,car_pile_ratio)
VALUES (?,?,?,?,?,?,?,?,?,?,?)
""", rows3)
print(f"[表3] stations_status_2025 写入 {len(rows3)} 条")

# ─────────────────────────────────────────────────────────
# 表4：城区充电站坐标表
# ─────────────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS stations_urban_coords")
cur.execute("""
CREATE TABLE stations_urban_coords (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    station_name TEXT,
    address      TEXT,
    longitude    REAL,   -- 高德经度
    latitude     REAL    -- 高德纬度
)
""")

df4 = pd.read_excel(
    os.path.join(DATA_DIR, "弋阳县城范围内充电站.xlsx"),
    header=None, engine="openpyxl"
)
df4_data = df4.iloc[4:].copy()
df4_data.columns = ["场站名称","位置","高德经度","高德纬度","场站照片","处理结果"]
df4_data = df4_data[df4_data["场站名称"].notna()].copy()
skip = {"品牌+汽车充电站（站名）", "场站名称", ""}
df4_data = df4_data[~df4_data["场站名称"].astype(str).str.strip().isin(skip)].copy()

def parse_coord(v):
    if pd.isna(v): return None
    s = str(v).replace('°E','').replace('°N','').strip()
    try: return float(s)
    except: return None

rows4 = []
for _, r in df4_data.iterrows():
    rows4.append((
        str(r["场站名称"]).strip(),
        str(r["位置"]).strip() if not pd.isna(r["位置"]) else None,
        parse_coord(r["高德经度"]),
        parse_coord(r["高德纬度"])
    ))
cur.executemany("""
INSERT INTO stations_urban_coords (station_name,address,longitude,latitude)
VALUES (?,?,?,?)
""", rows4)
print(f"[表4] stations_urban_coords 写入 {len(rows4)} 条")

# ─────────────────────────────────────────────────────────
# 表5：2026-2028规划充电站清单
# ─────────────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS stations_planned")
cur.execute("""
CREATE TABLE stations_planned (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_no      INTEGER, -- 序号
    township     TEXT,    -- 所在乡镇
    year         INTEGER, -- 建设年度
    scene        TEXT,    -- 应用场景
    station_name TEXT,    -- 站点
    quantity     INTEGER, -- 实际桩数量（台）
    power_kw     REAL,    -- 总功率（kW）
    spec         TEXT,    -- 说明/规格
    land_area    REAL,    -- 占地面积
    conv_factor  REAL,    -- 折算系数
    std_piles    INTEGER, -- 标准桩数
    tech_mode    TEXT,    -- 新技术新模式应用
    equipment    TEXT,    -- 设备容量
    reporter     TEXT     -- 填报单位
)
""")

xl4 = pd.ExcelFile(
    os.path.join(DATA_DIR, "计划规模汇总及统计表（弋阳）.xlsx"),
    engine="openpyxl"
)
raw5 = xl4.parse("2026-2028年清单（弋阳）", header=0)

rows5 = []
cur_no = None
cur_township = None
stop_keyword = "填报说明"
for _, r in raw5.iterrows():
    # 检测到说明行则停止
    first = str(r.iloc[0]) if not pd.isna(r.iloc[0]) else ""
    if stop_keyword in first:
        break
    no = r.iloc[0]
    if not pd.isna(no):
        try:
            cur_no = int(float(no))
        except:
            pass
    twn = r.iloc[1]
    if not pd.isna(twn) and str(twn).strip() not in ('nan',''):
        cur_township = str(twn).strip()
    name = r.iloc[4]
    if pd.isna(name) or str(name).strip() in ('nan',''):
        continue
    # year列
    yr = r.iloc[2]
    try: yr = int(float(yr))
    except: yr = None
    def safe_int2(v):
        if pd.isna(v): return None
        try: return int(float(v))
        except: return None
    def safe_float2(v):
        if pd.isna(v): return None
        try: return float(v)
        except: return None
    rows5.append((
        cur_no, cur_township, yr,
        str(r.iloc[3]).strip() if not pd.isna(r.iloc[3]) else None,
        str(name).strip(),
        safe_int2(r.iloc[5]), safe_float2(r.iloc[6]),
        str(r.iloc[7]).strip() if not pd.isna(r.iloc[7]) else None,
        safe_float2(r.iloc[8]), safe_float2(r.iloc[9]), safe_int2(r.iloc[10]),
        str(r.iloc[11]).strip() if not pd.isna(r.iloc[11]) else None,
        str(r.iloc[12]).strip() if not pd.isna(r.iloc[12]) else None,
        str(r.iloc[13]).strip() if not pd.isna(r.iloc[13]) else None,
    ))

cur.executemany("""
INSERT INTO stations_planned
(plan_no,township,year,scene,station_name,quantity,power_kw,spec,
 land_area,conv_factor,std_piles,tech_mode,equipment,reporter)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
""", rows5)
print(f"[表5] stations_planned 写入 {len(rows5)} 条")

# ─────────────────────────────────────────────────────────
# 表6：加油站详情（2024）
# ─────────────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS gas_stations")
cur.execute("""
CREATE TABLE gas_stations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    county            TEXT,   -- 所属县
    station_name      TEXT,   -- 加油站名称
    address           TEXT,   -- 详细地址
    ownership         TEXT,   -- 所有制（中石化/中石油/民营等）
    operation_type    TEXT,   -- 经营类型
    petrol_sales      REAL,   -- 汽油销量（吨）
    diesel_sales      REAL,   -- 柴油销量（吨）
    total_sales       REAL,   -- 合计销量（吨）
    storage_cap       REAL,   -- 总储油能力（立方）
    has_ev_charger    TEXT,   -- 是否有充电设施
    oil_revenue       REAL,   -- 成品油销售收入（万元）
    non_oil_revenue   REAL,   -- 非油品销售收入（万元）
    location_type     TEXT,   -- 站点属性（城区/省道国道/县乡道等）
    built_year        TEXT,   -- 建站时间
    contact           TEXT    -- 联系电话
)
""")

df6 = pd.read_excel(
    os.path.join(DATA_DIR, "（弋阳县）附表3：2024年度江西省加油站详细情况登记表.xls"),
    header=None, engine="xlrd"
)
rows6_raw = df6.iloc[5:].copy()
all_cols = list(range(38))
rows6_raw.columns = all_cols
rows6_raw = rows6_raw[rows6_raw[2].notna()].copy()  # 加油站名称不为空

def ownership_str(row):
    mapping = {4:'中石化',5:'中石油',6:'中化',7:'中海油',8:'其他国有',9:'民营'}
    parts = [v for k,v in mapping.items() if not pd.isna(row[k]) and str(row[k]).strip() in ('√','✓','是','有')]
    return '/'.join(parts) if parts else '民营'

def loc_type_str(row):
    mapping = {20:'城区',21:'省道国道',22:'县乡道农网',23:'高速公路',24:'水域',25:'其他'}
    parts = [v for k,v in mapping.items() if not pd.isna(row[k]) and str(row[k]).strip() in ('√','✓','是','有')]
    return '/'.join(parts) if parts else None

rows6 = []
for _, r in rows6_raw.iterrows():
    def sf(v):
        if pd.isna(v): return None
        try: return float(v)
        except: return None
    ev = str(r[33]).strip() if not pd.isna(r[33]) else None
    if ev in ('nan', ''): ev = None
    rows6.append((
        str(r[0]).strip() if not pd.isna(r[0]) else '弋阳',
        str(r[2]).strip(),
        str(r[3]).strip() if not pd.isna(r[3]) else None,
        ownership_str(r), 'NaN',
        sf(r[13]), sf(r[14]), sf(r[15]),
        sf(r[31]), ev,
        sf(r[33]) if ev not in ('√','✓','是','否','有') else None,
        sf(r[34]),
        loc_type_str(r),
        str(r[30]).strip() if not pd.isna(r[30]) else None,
        str(r[37]).strip() if not pd.isna(r[37]) else None
    ))

# 修正：成品油销售收入在列33实际是字符√，真实收入在列33应对应重新读
# 重新精确读取
rows6 = []
for _, r in rows6_raw.iterrows():
    def sf(v):
        if pd.isna(v): return None
        try: return float(v)
        except: return None
    # 列索引（0-based，与原始xls对应）:
    # 31=建站时间, 32=总储油能力(m³), 33=是否有充电设施(√/否/NaN)
    # 34=成品油销售收入, 35=非油品业务销售收入, 37=联系电话
    ev_raw = r[33]
    if pd.isna(ev_raw): ev = None
    else:
        s = str(ev_raw).strip()
        ev = s if s not in ('nan','') else None
    rows6.append((
        str(r[0]).strip() if not pd.isna(r[0]) else '弋阳',
        str(r[2]).strip(),
        str(r[3]).strip() if not pd.isna(r[3]) else None,
        ownership_str(r), None,
        sf(r[13]), sf(r[14]), sf(r[15]),
        sf(r[32]), ev,          # storage_cap=r[32], has_ev_charger=ev(r[33])
        sf(r[34]), sf(r[35]),   # oil_revenue=r[34], non_oil=r[35]
        loc_type_str(r),
        str(r[31]).strip() if not pd.isna(r[31]) else None,  # built_year=r[31]
        str(r[37]).strip() if not pd.isna(r[37]) else None   # contact=r[37]
    ))

cur.executemany("""
INSERT INTO gas_stations
(county,station_name,address,ownership,operation_type,
 petrol_sales,diesel_sales,total_sales,storage_cap,has_ev_charger,
 oil_revenue,non_oil_revenue,location_type,built_year,contact)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
""", rows6)
print(f"[表6] gas_stations 写入 {len(rows6)} 条")

# ─────────────────────────────────────────────────────────
# 完成
# ─────────────────────────────────────────────────────────
conn.commit()

# 验证
print("\n── 数据库表行数验证 ──")
for tbl in ["economic_stats","stations_existing_township","stations_status_2025",
            "stations_urban_coords","stations_planned","gas_stations"]:
    cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"  {tbl}: {cnt} 行")

conn.close()
print(f"\n数据库已保存到: {DB_PATH}")
