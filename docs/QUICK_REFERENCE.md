# 新增地区快速参考卡

## 一句话说清楚

**系统已完全支持多县，新增地区只需配置数据，无需修改代码。**

---

## 3 分钟快速配置流程

### 1️⃣ 运行工具（30 秒）

```bash
cd yiyang_wannian_chongdian
python tools/add_county.py --name XX 县 --key xianxian --adcode 36XXXX --center 115.X,27.X
```

### 2️⃣ 修改 config.py（1 分钟）

复制工具生成的配置代码，粘贴到 `config.py` 对应位置。

### 3️⃣ 准备边界文件（1 分钟）

从 DataV 下载 GeoJSON → 保存为 `data/xianxian_county.geojson`

> DataV 地址：https://datav.aliyun.com/portal/school/atlas/area_selector

### 4️⃣ 导入数据（1 分钟）

```bash
# 方式 A：SQL 导入
sqlite3 db/yiyang_ev.db < tools/county_setup_output/xianxian/xxx_data_import.sql

# 方式 B：CSV 导入
python tools/import_from_csv.py --type urban --input data.csv --county xianxian
```

### 5️⃣ 更新前端（30 秒）

在 `frontend/index.html` 的 `<select id="county-selector">` 中添加：

```html
<option value="xianxian">XX 县</option>
```

---

## 配置文件速查

### SUPPORTED_COUNTIES

```python
{"name": "XX 县", "adcode": "36XXXX", "center": [经度，纬度], "key": "xianxian"},
```

### 县信息

```python
COUNTY_INFO_XXIAN = {
    "name": "XX 县",
    "center": [经度，纬度],
    "adcode": "36XXXX",
    "stats": {"gdp": None, "population": None, ...}
}
```

### 乡镇标注

```python
TOWNSHIP_LABELS_XXIAN = [
    {"name": "XX 镇", "lng": 115.XX, "lat": 27.XX},
]
```

### 注册字典

```python
ALL_COUNTY_INFO = {"xianxian": COUNTY_INFO_XXIAN, ...}
ALL_TOWNSHIP_LABELS = {"xianxian": TOWNSHIP_LABELS_XXIAN, ...}
```

---

## 验证命令

```bash
# 边界
curl http://localhost:5000/api/boundary?county=xianxian

# 乡镇
curl http://localhost:5000/api/townships?county=xianxian

# 充电站
curl http://localhost:5000/api/stations/urban?county=xianxian
```

---

## 文件命名规范

| 文件类型 | 命名格式 | 示例 |
|---------|---------|------|
| 县边界 | `{key}_county.geojson` | `xianxian_county.geojson` |
| 乡镇边界 | `{key}_townships.geojson` | `xianxian_townships.geojson` |

---

## 数据库表字段

所有表都有 `county` 字段，插入数据时指定县名：

```sql
INSERT INTO stations_urban_coords (..., county)
VALUES (..., 'XX 县');
```

---

## 工具命令速查

| 工具 | 用途 | 命令 |
|------|------|------|
| `add_county.py` | 生成配置模板 | `python tools/add_county.py --name XX 县 --key xianxian ...` |
| `import_from_csv.py` | CSV 导入数据 | `python tools/import_from_csv.py --type urban --input xxx.csv --county xianxian` |

---

## 常见问题

| 问题 | 检查项 |
|------|--------|
| 边界不显示 | `data/{key}_county.geojson` 是否存在 |
| 乡镇不显示 | `ALL_TOWNSHIP_LABELS` 是否注册 |
| 数据为空 | 数据库 `county` 字段值是否匹配 |

---

## 需要帮助？

详细文档：`docs/ADD_COUNTY_GUIDE.md`
