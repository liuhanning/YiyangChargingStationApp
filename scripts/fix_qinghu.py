import sqlite3
import random

DB = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db"

# The center of Qinghu township in yiyang is approx 117.5385, 28.4300 based on the town boundary/map lookup
base_lng = 117.5385
base_lat = 28.4300

conn = sqlite3.connect(DB)
# Check all rows that have '清湖' in their name
rows = conn.execute("SELECT id, station_name, township, longitude, latitude FROM stations_planned WHERE station_name LIKE '%清湖%' OR township LIKE '%清湖%';").fetchall()

for row in rows:
    rid, name, town, lng, lat = row
    
    # We will adjust them tightly around base_lat, base_lng
    # if it's "清湖乡人民政府"
    if "人民政府" in name or "政府" in name or "政务服务" in name:
        new_lng = 117.5385
        new_lat = 28.4310
    else:
        new_lng = base_lng + random.uniform(-0.005, 0.005)
        new_lat = base_lat + random.uniform(-0.005, 0.005)

    conn.execute("UPDATE stations_planned SET longitude=?, latitude=? WHERE id=?", (new_lng, new_lat, rid))
    print(f"Updated {name} to {new_lng}, {new_lat}")

conn.commit()
conn.close()
