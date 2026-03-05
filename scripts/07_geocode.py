# -*- coding: utf-8 -*-
"""
高德地理编码：为加油站 & 规划充电站获取坐标
"""
import sqlite3, sys, time, json
import urllib.request, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')

AMAP_KEY = "63012397200899138fc66edc8f54a72a"
DB = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db"
conn = sqlite3.connect(DB)

def geocode(address, city="弋阳"):
    """调用高德正向地理编码"""
    params = urllib.parse.urlencode({
        "address": address,
        "city": city,
        "key": AMAP_KEY,
        "output": "json"
    })
    url = f"https://restapi.amap.com/v3/geocode/geo?{params}"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode('utf-8'))
        if data.get("status") == "1" and data["geocodes"]:
            loc = data["geocodes"][0]["location"]  # "lng,lat"
            lng, lat = loc.split(",")
            formatted = data["geocodes"][0].get("formatted_address","")
            return float(lng), float(lat), formatted
    except Exception as e:
        print(f"  [ERR] {address}: {e}")
    return None, None, None

# ── 新增坐标列（如果没有）──────────────────────────────
for tbl, col_check in [("gas_stations","longitude"), ("stations_planned","longitude")]:
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({tbl})").fetchall()]
    if "longitude" not in cols:
        conn.execute(f"ALTER TABLE {tbl} ADD COLUMN longitude REAL")
        conn.execute(f"ALTER TABLE {tbl} ADD COLUMN latitude REAL")
        conn.execute(f"ALTER TABLE {tbl} ADD COLUMN geocode_addr TEXT")
        conn.commit()
        print(f"[DB] {tbl} 新增 longitude/latitude/geocode_addr 列")

# ── 1. 加油站编码 ─────────────────────────────────────
print("\n=== 加油站地理编码 ===")
rows = conn.execute(
    "SELECT id, station_name, address FROM gas_stations WHERE longitude IS NULL"
).fetchall()

for rid, name, addr in rows:
    if not addr:
        print(f"  [SKIP] {name} 无地址")
        continue
    # 拼接更完整的地址
    full_addr = addr if "弋阳" in addr else f"弋阳县{addr}"
    lng, lat, fmt = geocode(full_addr)
    if lng:
        conn.execute(
            "UPDATE gas_stations SET longitude=?,latitude=?,geocode_addr=? WHERE id=?",
            (lng, lat, fmt, rid)
        )
        print(f"  ✓ {name}  ({lng},{lat})")
    else:
        print(f"  ✗ {name}  编码失败")
    time.sleep(0.1)  # 控制频率

conn.commit()

# ── 2. 规划充电站编码 ─────────────────────────────────
print("\n=== 规划充电站地理编码 ===")
rows = conn.execute(
    "SELECT id, station_name, township FROM stations_planned WHERE longitude IS NULL AND station_name IS NOT NULL"
).fetchall()

# 地址映射：站点名称 → 搜索地址（模糊名称补全）
name_hint = {
    "***县***镇小康路，行政服务中心": "弋阳县行政服务中心",
    "西街停车场一": "弋阳县西街",
    "西街停车场二": "弋阳县西街",
    "西街停车场三": "弋阳县西街",
    "大桥洞以北两侧": "弋阳县大桥",
    "乐江首府以北": "弋阳县乐江首府",
    "东鑫公馆以东": "弋阳县东鑫公馆",
    "式平路边停车场（湾里路）": "弋阳县式平路",
    "老财政局平面停车场": "弋阳县财政局",
    "老社保局平面停车场（方格尔停车场）": "弋阳县人力资源和社会保障局",
    "长卿路北街社区旁（方格尔停车场）": "弋阳县长卿路",
    "杨桥路方格尔停车场（中国银行对面）": "弋阳县中国银行",
    "滨江公园洲上公园平面停车场": "弋阳县滨江公园",
    "府前社区方志敏公园（广和明月苑）": "弋阳县方志敏公园",
    "建岭社区菜场小区": "弋阳县建岭社区",
    "桃源街道淝塘岗小区": "弋阳县桃源街道",
    "桃源街道双停社区": "弋阳县桃源街道",
    "桃源街道居委会": "弋阳县桃源街道居委会",
    "新材料产业园内": "弋阳县三县岭新材料产业园",
}

for rid, name, township in rows:
    search_addr = name_hint.get(name, f"弋阳县{township or ''}{name}")
    lng, lat, fmt = geocode(search_addr)
    if lng:
        conn.execute(
            "UPDATE stations_planned SET longitude=?,latitude=?,geocode_addr=? WHERE id=?",
            (lng, lat, fmt, rid)
        )
        print(f"  ✓ {name}  ({lng:.4f},{lat:.4f})")
    else:
        print(f"  ✗ {name}  编码失败")
    time.sleep(0.1)

conn.commit()

# ── 验证 ──────────────────────────────────────────────
print("\n=== 编码结果统计 ===")
g_total = conn.execute("SELECT COUNT(*) FROM gas_stations").fetchone()[0]
g_ok    = conn.execute("SELECT COUNT(*) FROM gas_stations WHERE longitude IS NOT NULL").fetchone()[0]
p_total = conn.execute("SELECT COUNT(*) FROM stations_planned WHERE station_name IS NOT NULL").fetchone()[0]
p_ok    = conn.execute("SELECT COUNT(*) FROM stations_planned WHERE longitude IS NOT NULL").fetchone()[0]
print(f"加油站:     {g_ok}/{g_total} 获得坐标")
print(f"规划站点:   {p_ok}/{p_total} 获得坐标")
conn.close()
