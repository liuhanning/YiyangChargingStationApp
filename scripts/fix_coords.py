import sqlite3
import random

DB = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db"
conn = sqlite3.connect(DB)

TOWNSHIP_LABELS = {
    "弋江镇": (117.434, 28.402),
    "南岩镇": (117.455, 28.370),
    "桃源街道": (117.458, 28.420),
    "花亭乡": (117.395, 28.447),
    "圭峰镇": (117.405, 28.310),
    "叠山镇": (117.335, 28.360),
    "漆工镇": (117.350, 28.460),
    "湾里乡": (117.503, 28.490),
    "葛溪乡": (117.540, 28.560),
    "中畈乡": (117.490, 28.215),
    "港口镇": (117.310, 28.290),
    "清湖乡": (117.538, 28.430),
    "旭光乡": (117.310, 28.530),
    "樟树墩镇": (117.290, 28.615),
    "曹溪镇": (117.460, 28.155),
    "三县岭镇": (117.555, 28.660),
    # Aliases
    "弋江街道": (117.434, 28.402),
    "南岩街道": (117.455, 28.370),
    "樟树墩": (117.290, 28.615),
    "三县岭": (117.555, 28.660),
    "漆工": (117.350, 28.460),
    "曹溪": (117.460, 28.155),
    "圭峰": (117.405, 28.310),
}
# assign fake coordinates for stations missing coords
rows = conn.execute("SELECT id, township, station_name FROM stations_planned WHERE longitude IS NULL OR longitude = ''").fetchall()
count = 0
for rid, town, name in rows:
    # try to match township
    town_key = None
    if town:
        for k in TOWNSHIP_LABELS.keys():
            if k in town: town_key = k; break
    if not town_key and name:
        for k in TOWNSHIP_LABELS.keys():
            if k in name: town_key = k; break
    
    if town_key:
        base_lng, base_lat = TOWNSHIP_LABELS[town_key]
        # add tiny random offset so they don't overlap completely
        lng = base_lng + random.uniform(-0.02, 0.02)
        lat = base_lat + random.uniform(-0.02, 0.02)
        conn.execute("UPDATE stations_planned SET longitude=?, latitude=? WHERE id=?", (lng, lat, rid))
        count += 1
    else:
        # Default to Yiyang center
        lng = 117.44 + random.uniform(-0.03, 0.03)
        lat = 28.37 + random.uniform(-0.03, 0.03)
        conn.execute("UPDATE stations_planned SET longitude=?, latitude=? WHERE id=?", (lng, lat, rid))
        count += 1

rows2 = conn.execute("SELECT id, station_name FROM stations_urban_coords WHERE longitude IS NULL OR longitude = ''").fetchall()
for rid, name in rows2:
    town_key = None
    if name:
        for k in TOWNSHIP_LABELS.keys():
            if k in name: town_key = k; break
    
    if town_key:
        base_lng, base_lat = TOWNSHIP_LABELS[town_key]
        lng = base_lng + random.uniform(-0.01, 0.01)
        lat = base_lat + random.uniform(-0.01, 0.01)
        conn.execute("UPDATE stations_urban_coords SET longitude=?, latitude=? WHERE id=?", (lng, lat, rid))
    else:
        lng = 117.44 + random.uniform(-0.02, 0.02)
        lat = 28.37 + random.uniform(-0.02, 0.02)
        conn.execute("UPDATE stations_urban_coords SET longitude=?, latitude=? WHERE id=?", (lng, lat, rid))

conn.commit()
print(f"Assigned fallback coordinates to {count} planned stations and {len(rows2)} urban stations.")
