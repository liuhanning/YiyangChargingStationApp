import sqlite3
import pandas as pd
import json

db_path = r'C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db'
excel_planned = r'C:\Users\lhn\OneDrive\Desktop\江西\上饶电动侧预测\计划规模汇总及统计表（弋阳） 20260306.xlsx'
excel_status = r'C:\Users\lhn\OneDrive\Desktop\江西\上饶电动侧预测\基础数据统计（弋阳）-20260305.xlsx'

# 1. Connect to DB and fetch existing coordinates
conn = sqlite3.connect(db_path)
cur = conn.cursor()

coords_map_urban = {}
for row in cur.execute("SELECT station_name, longitude, latitude FROM stations_urban_coords"):
    name = row[0]
    if name: coords_map_urban[name.strip()] = (row[1], row[2])

coords_map_gas = {}
for row in cur.execute("SELECT station_name, longitude, latitude, geocode_addr FROM gas_stations"):
    name = row[0]
    if name: coords_map_gas[name.strip()] = (row[1], row[2], row[3])

coords_map_planned = {}
for row in cur.execute("SELECT station_name, longitude, latitude, geocode_addr FROM stations_planned"):
    name = row[0]
    if name: coords_map_planned[name.strip()] = (row[1], row[2], row[3])

print(f"Loaded existing coords: urban={len(coords_map_urban)}, gas={len(coords_map_gas)}, planned={len(coords_map_planned)}")

# 2. Re-create tables to flush old data but keep schema
cur.executescript("""
DELETE FROM stations_urban_coords;
DELETE FROM sqlite_sequence WHERE name='stations_urban_coords';
DELETE FROM gas_stations;
DELETE FROM sqlite_sequence WHERE name='gas_stations';
DELETE FROM stations_planned;
DELETE FROM sqlite_sequence WHERE name='stations_planned';
""")

# 3. Process existing urban and gas stations from 基础数据统计（弋阳）-20260305.xlsx -> Sheet "弋阳现状(2025年)"
try:
    df_status_dict = pd.read_excel(excel_status, sheet_name=None, header=None)
    keys = list(df_status_dict.keys())
    df_status = df_status_dict[keys[1]] # 弋阳现状(2025年)
    # The actual data seems to start around row 3
    # Let's find rows where Col 4 is a station name
    urban_list = []
    gas_list = []
    
    for idx, row in df_status.iterrows():
        name = str(row[4]).strip()
        if name in ['nan', '', 'None', '充电站所在位置']: continue
        if pd.isna(name): continue
        if idx < 3: continue  # skip headers
        
        # Col 11 is scene / location type
        scene = str(row[11]).strip()
        address = str(row[15]).strip() if len(row) > 15 and pd.notna(row[15]) else ""
        
        # Parse data depending on if it's fuel or ev
        if "加油站" in scene or "加能站" in name or "加油站" in name:
            # Add to gas_stations
            lng, lat, gc_addr = coords_map_gas.get(name, (None, None, ""))
            has_ev = '✓' if ('充电' in name or '充电' in scene) else ''
            
            cur.execute("""
                INSERT INTO gas_stations 
                (station_name, address, has_ev_charger, location_type, longitude, latitude, geocode_addr)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, address, has_ev, scene, lng, lat, gc_addr))
            gas_list.append(name)
        else:
            # Add to stations_urban_coords
            lng, lat = coords_map_urban.get(name, (None, None))
            # Also check if it might be in planned for coords
            if lng is None:
                lng, lat, _ = coords_map_planned.get(name, (None, None, ""))
            cur.execute("""
                INSERT INTO stations_urban_coords 
                (station_name, address, longitude, latitude)
                VALUES (?, ?, ?, ?)
            """, (name, address, lng, lat))
            urban_list.append(name)

    print(f"Imported {len(urban_list)} urban stations and {len(gas_list)} gas stations.")
except Exception as e:
    print("Error parsing status sheet:", e)


# 4. Process Planned stations from 计划规模汇总及统计表（弋阳） 20260306.xlsx -> Sheet "2026-2028年清单（弋阳）-新"
try:
    df_planned = pd.read_excel(excel_planned, sheet_name='2026-2028年清单（弋阳）-新')
    # Use column names directly if they exist
    # '序号', '所在\n乡镇', '年度', '场景', '站点', '实际桩\n数量\n（台/座）\n', '总功率（kW）', '说明', '占地面积', '折算系数', '标准桩数', '新技术新模式应用', '设备容量', '填报单位', '备注'
    
    # For robust matching:
    cols = df_planned.columns
    col_name = [c for c in cols if '站点' in str(c)][0]
    col_town = [c for c in cols if '乡镇' in str(c)][0]
    col_year = [c for c in cols if '年度' in str(c)][0]
    col_scene = [c for c in cols if '场景' in str(c)][0]
    col_qty = [c for c in cols if '数量' in str(c)][0]
    col_power = [c for c in cols if '功率' in str(c)][0]
    col_equip = [c for c in cols if '说明' in str(c) or '规格' in str(c)][0]
    
    # 填补合并单元格造成的空缺
    df_planned[col_town] = df_planned[col_town].ffill()
    df_planned = df_planned.dropna(subset=[col_name])
    planned_list = []
    
    for idx, row in df_planned.iterrows():
        name = str(row[col_name]).strip()
        # 排除掉Excel中说明性的文本行
        if name in ['nan', '', 'None', '说明', '场景补充说明']: continue
        if any(x in name for x in ['企事业单位', '私家车', '国省道', '基于传统', '工业园区', '1000人以上', '行政村', '其他情况']): continue
        
        town = str(row[col_town]).strip()
        try: year = int(row[col_year])
        except: year = 2026
        scene = str(row[col_scene]).strip()
        try: qty = int(row[col_qty])
        except: qty = 0
        try: power = float(row[col_power])
        except: power = 0.0
        equip = str(row[col_equip]).strip()
        
        # coords
        lng, lat, gc_addr = coords_map_planned.get(name, (None, None, ""))
        
        cur.execute("""
            INSERT INTO stations_planned
            (township, year, scene, station_name, quantity, power_kw, spec, longitude, latitude, geocode_addr)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (town, year, scene, name, qty, power, equip, lng, lat, gc_addr))
        planned_list.append(name)

    print(f"Imported {len(planned_list)} planned stations.")
except Exception as e:
    print("Error parsing planned sheet:", e)

# 5. Commit changes
conn.commit()
conn.close()
print("Database updated with newest data successfully.")
