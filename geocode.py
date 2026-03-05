import sqlite3
import urllib.request
import urllib.parse
import json
import ssl
import time
from pathlib import Path

# Add project root to sys path to import config
import sys
sys.path.append(r'c:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目')
from config import MAP_API

TK = MAP_API['tianditu']['key']
DB_PATH = r'c:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db'

def geocode(address):
    # Base URL for TianDiTu Geocoding API
    base_url = "http://api.tianditu.gov.cn/geocoder"
    
    # If the address doesn't start with province/city, add it to improve accuracy
    full_address = address
    if "江西" not in full_address and "弋阳" not in full_address:
        full_address = "江西省上饶市弋阳县" + address
    elif "弋阳" not in full_address:
        full_address = "弋阳县" + address
        
    ds = json.dumps({"keyWord": full_address})
    url = f"{base_url}?ds={urllib.parse.quote(ds)}&tk={TK}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        data = json.loads(response)
        
        if data.get("msg") == "ok" and data.get("location"):
            loc = data["location"]
            return loc["lon"], loc["lat"]
        else:
            # Fallback to a looser search if strict search fails
            if full_address != address:
                ds = json.dumps({"keyWord": "弋阳县" + address[:6]}) 
                url = f"{base_url}?ds={urllib.parse.quote(ds)}&tk={TK}"
                response = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
                data = json.loads(response)
                if data.get("msg") == "ok" and data.get("location"):
                    loc = data["location"]
                    return loc["lon"], loc["lat"]
            return None, None
    except Exception as e:
        print(f"Error geocoding {address}: {e}")
        return None, None

def update_gas_stations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, station_name, address FROM gas_stations WHERE longitude IS NULL OR latitude IS NULL")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} gas stations needing geocoding.")
    updated = 0
    
    for row in rows:
        sid, name, addr = row
        search_addr = addr if addr else name
        
        lon, lat = geocode(search_addr)
        if lon and lat:
            print(f"Found: {name} ({addr}) -> {lon}, {lat}")
            cursor.execute("UPDATE gas_stations SET longitude = ?, latitude = ? WHERE id = ?", (lon, lat, sid))
            updated += 1
        else:
            print(f"Not found: {name} ({addr})")
        time.sleep(0.5) # respectful delay
        
    conn.commit()
    conn.close()
    print(f"Updated {updated} gas stations.")

def update_planned_stations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, station_name, township FROM stations_planned WHERE longitude IS NULL OR latitude IS NULL")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} planned stations needing geocoding.")
    updated = 0
    
    for row in rows:
        sid, name, township = row
        search_addr = f"{township}{name}" if township else name
        
        lon, lat = geocode(search_addr)
        if lon and lat:
            print(f"Found: {name} ({township}) -> {lon}, {lat}")
            cursor.execute("UPDATE stations_planned SET longitude = ?, latitude = ? WHERE id = ?", (lon, lat, sid))
            updated += 1
        else:
            print(f"Not found: {name} ({township})")
        time.sleep(0.5)
        
    conn.commit()
    conn.close()
    print(f"Updated {updated} planned stations.")

if __name__ == '__main__':
    update_gas_stations()
    update_planned_stations()
