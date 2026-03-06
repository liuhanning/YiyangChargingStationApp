import sqlite3
import pandas as pd

DB_PATH = r'c:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db'

# 弋阳县经纬度大致范围
MIN_LNG = 117.1
MAX_LNG = 117.7
MIN_LAT = 28.1
MAX_LAT = 28.7

def check_table(conn, table_name, name_col, addr_col=None):
    try:
        query = f"SELECT {name_col}, longitude, latitude"
        if addr_col:
            query += f", {addr_col}"
        query += f" FROM {table_name}"
        
        df = pd.read_sql(query, conn)
        outliers = []
        for _, row in df.iterrows():
            name = row[name_col]
            lng = row['longitude']
            lat = row['latitude']
            
            # Skip empty or missing coordinates
            if pd.isna(lng) or pd.isna(lat) or not lng or not lat:
                continue
            
            lng = float(lng)
            lat = float(lat)
            
            if not (MIN_LNG <= lng <= MAX_LNG and MIN_LAT <= lat <= MAX_LAT):
                outliers.append({
                    'table': table_name,
                    'name': name,
                    'lng': lng,
                    'lat': lat,
                    'addr': row[addr_col] if addr_col else None
                })
        return outliers
    except Exception as e:
        print(f"Error checking {table_name}: {e}")
        return []

def main():
    conn = sqlite3.connect(DB_PATH)
    outliers = []
    
    outliers.extend(check_table(conn, "gas_stations", "station_name", "address"))
    outliers.extend(check_table(conn, "stations_planned", "station_name", "township"))
    outliers.extend(check_table(conn, "stations_existing", "station_name", "address"))
    
    if not outliers:
        print("All points are within Yiyang County bounds!")
    else:
        print(f"Found {len(outliers)} points outside Yiyang County bounds:")
        for o in outliers:
            print(f"[{o['table']}] {o['name']} - Lng: {o['lng']}, Lat: {o['lat']}, Addr/Township: {o['addr']}")

if __name__ == "__main__":
    main()
