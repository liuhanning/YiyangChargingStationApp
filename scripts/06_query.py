# -*- coding: utf-8 -*-
"""
弋阳县充电桩规划 - 快速数据查询 & 统计计算
"""
import sqlite3, sys
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

DB = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db"
conn = sqlite3.connect(DB)

def q(sql, title="", rename=None):
    df = pd.read_sql(sql, conn)
    if rename:
        df.columns = rename
    if title:
        print(f"\n{'─'*60}")
        print(f"【{title}】")
        print('─'*60)
    print(df.to_string(index=False))
    return df

print("=" * 60)
print("  弋阳县充电桩规划 · 数据统计摘要")
print("=" * 60)

# 1. 各乡镇现有充电桩汇总
q("SELECT township,SUM(quantity) as qty,COUNT(*) as cnt FROM stations_existing_township GROUP BY township ORDER BY qty DESC",
  "各乡镇现有充电桩汇总",
  rename=["乡镇", "充电桩数量(台)", "站点数"])

# 2. 2025年充电设施现状按乡镇
q("""SELECT township,COUNT(*) as cnt,SUM(quantity) as qty,
          SUM(total_power_kw) as power,SUM(above_120kw) as fast
   FROM stations_status_2025 WHERE station_name IS NOT NULL
   GROUP BY township ORDER BY qty DESC""",
  "2025年充电设施现状（按乡镇）",
  rename=["乡镇","站点数","充电桩(台)","总功率(kW)","120kW以上(台)"])

# 3. 规划清单按年度汇总
q("""SELECT year,COUNT(*) as cnt,SUM(quantity) as qty,ROUND(SUM(power_kw),0) as power
   FROM stations_planned WHERE year IS NOT NULL AND station_name IS NOT NULL
   GROUP BY year ORDER BY year""",
  "2026-2028规划充电桩按年度汇总",
  rename=["规划年度","站点数","规划桩数(台)","总功率(kW)"])

# 4. 规划清单按场景汇总
q("""SELECT scene,COUNT(*) as cnt,SUM(quantity) as qty
   FROM stations_planned WHERE scene IS NOT NULL AND station_name IS NOT NULL
   GROUP BY scene ORDER BY qty DESC""",
  "规划充电桩按应用场景汇总",
  rename=["应用场景","站点数","规划桩数(台)"])

# 5. 规划按乡镇汇总
q("""SELECT township,SUM(quantity) as qty,ROUND(SUM(power_kw),0) as power
   FROM stations_planned WHERE township IS NOT NULL AND station_name IS NOT NULL
   GROUP BY township ORDER BY qty DESC""",
  "规划充电桩按乡镇汇总",
  rename=["乡镇","规划桩数(台)","总功率(kW)"])

# 6. 加油站改造潜力
q("SELECT has_ev_charger,COUNT(*) as cnt FROM gas_stations GROUP BY has_ev_charger",
  "加油站充电设施改造潜力",
  rename=["是否有充电设施","加油站数量"])

# 7. 加油站按位置类型
q("""SELECT location_type,COUNT(*) as cnt,
          ROUND(AVG(total_sales),0) as avg_sales,
          ROUND(SUM(oil_revenue),0) as total_rev
   FROM gas_stations WHERE location_type IS NOT NULL
   GROUP BY location_type ORDER BY cnt DESC""",
  "加油站按位置类型分析（改造优先级参考）",
  rename=["位置类型","数量","平均年销量(吨)","合计油品收入(万元)"])

# 8. 弋阳历年新能源车数据
q("""SELECT year,car_total,nev_total,
          ROUND(nev_total*100.0/car_total,2) as nev_pct,
          gdp,population
   FROM economic_stats WHERE region='弋阳' AND year>=2020 ORDER BY year""",
  "弋阳县近年汽车 & 新能源数据",
  rename=["年份","汽车保有量(万辆)","新能源车(万辆)","新能源占比(%)","GDP(亿元)","常住人口(万人)"])

# 9. 总体规模测算
print(f"\n{'─'*60}")
print("【总体规模测算】")
print('─'*60)
rows = conn.execute("""
SELECT
  (SELECT SUM(quantity) FROM stations_existing_township),
  (SELECT SUM(quantity) FROM stations_status_2025 WHERE quantity IS NOT NULL),
  (SELECT SUM(quantity) FROM stations_planned WHERE year=2026),
  (SELECT SUM(quantity) FROM stations_planned WHERE year=2027),
  (SELECT SUM(quantity) FROM stations_planned WHERE year=2028),
  (SELECT ROUND(SUM(power_kw),0) FROM stations_planned),
  (SELECT COUNT(*) FROM gas_stations),
  (SELECT COUNT(*) FROM gas_stations WHERE has_ev_charger IN ('√','是','有'))
""").fetchone()
labels = [
    "现有充电桩（各乡镇台账）",
    "现状充电桩（2025年报表统计）",
    "2026年规划新增（台）",
    "2027年规划新增（台）",
    "2028年规划新增（台）",
    "规划充电站总功率（kW）",
    "加油站总数（座）",
    "已有充电设施加油站（座）",
]
for lbl, val in zip(labels, rows):
    print(f"  {lbl:<30} {val}")

conn.close()
print(f"\n数据库路径: {DB}")
