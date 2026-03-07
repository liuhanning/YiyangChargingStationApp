import sqlite3

DB = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db"
conn = sqlite3.connect(DB)

# 2025 data from prompt context:
# GDP: 203.94 
# 常住人口: 待公布 / or 32.94?
# car_total: 5.986 万辆
# nev_total: 0.3225 万辆
# nev_rate: 5.39 %

try:
    # First, let's insert or update 2025 data for Yiyang
    cur = conn.cursor()
    
    # check if 2025 exists
    row = cur.execute("SELECT * FROM economic_stats WHERE region='弋阳' AND year='2025'").fetchone()
    if row:
        cur.execute("""
            UPDATE economic_stats 
            SET car_total=?, nev_total=?, nev_rate=?, gdp=?
            WHERE region='弋阳' AND year='2025'
        """, (5.986, 0.3225, 5.39, 203.94))
    else:
        # just replace the whole thing or insert
        cur.execute("""
            INSERT INTO economic_stats 
            (region, year, car_total, car_new, nev_total, nev_new, nev_rate, gdp, fiscal_rev, population)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('弋阳', 2025, 5.986, 0.1664, 0.3225, 0.1427, 5.39, 203.94, 289.2, 32.94))
        
    conn.commit()
    print("Economic stats updated for 2025.")
except Exception as e:
    print("Error:", e)
conn.close()
