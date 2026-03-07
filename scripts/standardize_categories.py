"""
按国家标准对充电设施场景进行标准化分类
公共充电设施 / 专用充电设施 / 农村普惠设施 / 旅游景区设施
并在数据库中新增 category 和 category_code 字段
"""
import sqlite3

DB = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1. 如果不存在 category 列，则新增
cols = [c[1] for c in cur.execute("PRAGMA table_info(stations_planned)").fetchall()]
if "category" not in cols:
    cur.execute("ALTER TABLE stations_planned ADD COLUMN category TEXT")
    cur.execute("ALTER TABLE stations_planned ADD COLUMN category_code INTEGER")
    print("已新增 category / category_code 列")

# 2. 场景 -> 国家标准分类 映射规则
# category_code: 1=公共充电设施, 2=专用充电设施, 3=农村普惠设施, 4=旅游景区设施
SCENE_MAP = {
    "社会停车场":           ("公共充电设施", 1),
    "单位停车场（对外开放）": ("公共充电设施", 1),
    "集聚点":               ("专用充电设施", 2),
    "产业集聚区":           ("专用充电设施", 2),
    "农村客货站点":         ("农村普惠设施", 3),
    "3A级及以下旅游景区":   ("旅游景区设施", 4),
}

# 3. 逐条更新
rows = cur.execute("SELECT id, scene FROM stations_planned").fetchall()
updated = {}
for rid, scene in rows:
    scene = (scene or "").strip()
    cat, code = SCENE_MAP.get(scene, ("公共充电设施", 1))  # 默认归为公共
    cur.execute("UPDATE stations_planned SET category=?, category_code=? WHERE id=?", (cat, code, rid))
    updated[cat] = updated.get(cat, 0) + 1

conn.commit()
conn.close()

print("\n=== 标准化分类结果 ===")
for cat, cnt in sorted(updated.items()):
    print(f"  {cat}: {cnt} 个站点")
print("完成！")
