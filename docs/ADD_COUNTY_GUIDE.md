# 新增地区快速部署指南

## 概述

本文档说明如何在充换电设施规划系统中**快速新增一个地区**并标注点位。

当前系统架构已完全支持多县，新增地区只需**数据配置**，无需修改代码。

---

## 快速开始（5 分钟完成）

### 方法一：使用自动化工具（推荐）

```bash
# 进入项目目录
cd yiyang_wannian_chongdian

# 运行新增县工具
python tools/add_county.py --name 新建县 --key jianxin --adcode 360821 --center 115.5,27.5
```

工具会自动生成：
- 配置文件模板
- SQL 导入模板
- CSV 数据模板
- 边界占位文件
- 配置指南 README

### 方法二：手动配置

按照以下步骤手动配置：

---

## 完整配置步骤

### 步骤 1：准备县基本信息

收集以下信息：
| 项目 | 说明 | 示例 |
|------|------|------|
| 县名 | 全称 | `新建县` |
| 标识 key | 用于代码引用 | `jianxin` |
| 行政区划代码 | 6 位数字 | `360821` |
| 县城中心坐标 | [经度，纬度] | `[115.5, 27.5]` |
| 所属省市 | - | `江西省 XX 市` |

---

### 步骤 2：修改 `config.py`

#### 2.1 添加县配置

在 `SUPPORTED_COUNTIES` 列表中添加：

```python
{"name": "新建县", "adcode": "360821", "center": [115.5, 27.5], "key": "jianxin"},
```

#### 2.2 添加县详细信息（可选）

```python
COUNTY_INFO_JIANXIN = {
    "name": "新建县",
    "province": "江西省",
    "city": "XX 市",
    "center": [115.5, 27.5],
    "adcode": "360821",
    "stats": {
        "gdp": None,
        "population": None,
        "car_total": None,
        "nev_total": None,
        "nev_rate": None,
    }
}
```

然后在 `ALL_COUNTY_INFO` 中注册：

```python
ALL_COUNTY_INFO = {
    "yiyang": COUNTY_INFO,
    "wannian": COUNTY_INFO_WANNIAN,
    "jianxin": COUNTY_INFO_JIANXIN,  # 新增
}
```

#### 2.3 添加乡镇标注

```python
TOWNSHIP_LABELS_JIANXIN = [
    {"name": "XX 镇", "lng": 115.XX, "lat": 27.XX},
    # ... 更多乡镇
]

ALL_TOWNSHIP_LABELS = {
    "yiyang": TOWNSHIP_LABELS,
    "wannian": TOWNSHIP_LABELS_WANNIAN,
    "jianxin": TOWNSHIP_LABELS_JIANXIN,  # 新增
}
```

---

### 步骤 3：准备边界数据

#### 3.1 GeoJSON 格式（推荐）

创建文件 `data/jianxin_county.geojson`：

```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "properties": {
      "name": "新建县",
      "center": [115.5, 27.5],
      "adcode": "360821"
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[115.3, 27.3], [115.7, 27.3], [115.7, 27.7], [115.3, 27.7], [115.3, 27.3]]]
    }
  }]
}
```

#### 3.2 获取边界数据的来源

1. **DataV.GeoAtlas**（推荐）
   - 访问：https://datav.aliyun.com/portal/school/atlas/area_selector
   - 选择对应县区，下载 GeoJSON

2. **天地图 API**
   - 使用行政区划查询接口

3. **高德地图 API**
   - 使用行政区划查询接口

#### 3.3 简化版 JSON（备选）

创建文件 `data/jianxin_boundary.json`，只包含坐标数组：

```json
[[115.3, 27.3], [115.7, 27.3], [115.7, 27.7], [115.3, 27.7], [115.3, 27.3]]
```

---

### 步骤 4：导入点位数据

#### 方法 A：使用 SQL 直接导入

创建 SQL 文件 `data/jianxin_import.sql`：

```sql
-- 导入现有充电站
INSERT INTO stations_urban_coords (station_name, address, longitude, latitude, county)
VALUES
    ('新建充电站 1', '新建区大道 1 号', 115.51, 27.51, '新建县'),
    ('新建充电站 2', '新建区大道 2 号', 115.52, 27.52, '新建县');

-- 导入规划充电站
INSERT INTO stations_planned (station_name, township, scene, quantity, power_kw, year, longitude, latitude, county)
VALUES
    ('新建规划站 1', 'XX 镇', '城市广场', 10, 1000, 2026, 115.53, 27.53, '新建县');

-- 导入加油站
INSERT INTO gas_stations (station_name, address, longitude, latitude, county)
VALUES
    ('新建加油站 1', '新建区路 1 号', 115.54, 27.54, '新建县');
```

执行导入：

```bash
sqlite3 db/yiyang_ev.db < data/jianxin_import.sql
```

#### 方法 B：使用 CSV 导入工具

1. 填写 CSV 模板（由 `add_county.py` 生成）

2. 运行导入命令：

```bash
# 导入现有充电站
python tools/import_from_csv.py --type urban --input csv/jianxin_urban.csv --county jianxin

# 导入规划充电站
python tools/import_from_csv.py --type planned --input csv/jianxin_planned.csv --county jianxin

# 导入加油站
python tools/import_from_csv.py --type gas --input csv/jianxin_gas.csv --county jianxin
```

---

### 步骤 5：更新前端

在 `frontend/index.html` 中找到县域选择器：

```html
<select id="county-selector" onchange="switchCounty(this.value)">
  <option value="yiyang">弋阳县</option>
  <option value="wannian">万年县</option>
  <!-- 新增此行 -->
  <option value="jianxin">新建县</option>
  <option value="all">多县联合</option>
</select>
```

---

### 步骤 6：验证配置

启动应用后，访问以下 API 验证：

```bash
# 1. 检查县配置
curl http://localhost:5000/api/config

# 2. 检查边界数据
curl http://localhost:5000/api/boundary?county=jianxin

# 3. 检查乡镇标注
curl http://localhost:5000/api/townships?county=jianxin

# 4. 检查现有充电站
curl http://localhost:5000/api/stations/urban?county=jianxin

# 5. 检查规划充电站
curl http://localhost:5000/api/stations/planned?county=jianxin

# 6. 检查统计数据
curl http://localhost:5000/api/stats?county=jianxin
```

---

## 验证清单

新增县后，请验证以下功能：

- [ ] 县级边界正确显示
- [ ] 乡镇标注正确显示
- [ ] 现有充电站正确显示
- [ ] 规划充电站正确显示
- [ ] 加油站正确显示
- [ ] 统计数据正确计算
- [ ] 县切换功能正常
- [ ] 联合视图正常（如适用）

---

## 文件结构

新增县后，项目文件结构如下：

```
yiyang_wannian_chongdian/
├── config.py                  # 配置文件（已更新）
├── frontend/
│   └── index.html             # 前端页面（已添加选项）
├── data/
│   ├── jianxin_county.geojson # 新建县边界
│   ├── jianxin_townships.geojson  # 乡镇边界（可选）
│   └── ...
├── db/
│   └── yiyang_ev.db           # 数据库（已导入数据）
└── tools/
    ├── add_county.py          # 新增县工具
    └── import_from_csv.py     # CSV 导入工具
```

---

## 常见问题

### Q1: 边界显示不正确？

**检查**：
1. GeoJSON 文件格式是否正确
2. 坐标是否为 WGS84 坐标系（经纬度）
3. 文件路径是否为 `data/{key}_county.geojson`

### Q2: 乡镇标注不显示？

**检查**：
1. `ALL_TOWNSHIP_LABELS` 字典中是否已注册
2. 坐标格式是否正确（lng, lat）
3. 前端请求的 county 参数是否与 key 匹配

### Q3: 数据查询为空？

**检查**：
1. 数据库中 `county` 字段值是否与查询一致
2. SQL 导入时县名是否正确（如'新建县'而非'新建'）

### Q4: 如何获取县边界 GeoJSON？

**方法**：
1. 访问 DataV.GeoAtlas：https://datav.aliyun.com/portal/school/atlas/area_selector
2. 在地图上选择对应县区
3. 下载 GeoJSON 文件
4. 复制到 `data/{key}_county.geojson`

---

## 架构说明

### 数据库结构

所有核心表都包含 `county` 字段：

| 表名 | county 字段 | 说明 |
|------|-----------|------|
| `stations_urban_coords` | TEXT | 现有充电站 |
| `stations_planned` | TEXT | 规划充电站 |
| `gas_stations` | TEXT | 加油站 |
| `economic_stats` | TEXT | 经济统计 |

### 后端 API

所有 API 都支持 `county` 参数：

- `/api/boundary?county=<key>` - 县域边界
- `/api/stations/urban?county=<key>` - 现有充电站
- `/api/stations/planned?county=<key>` - 规划充电站
- `/api/stations/gas?county=<key>` - 加油站
- `/api/townships?county=<key>` - 乡镇标注
- `/api/stats?county=<key>` - 统计数据

### 前端逻辑

- `CURRENT_COUNTY` 变量跟踪当前选择的县
- `switchCounty()` 函数触发数据重新加载
- API 调用自动带上 `county` 参数

---

## 工具脚本

### `tools/add_county.py` - 新增县配置工具

自动生成配置文件模板、SQL 模板、CSV 模板。

```bash
python tools/add_county.py --name 新建县 --key jianxin --adcode 360821 --center 115.5,27.5
```

### `tools/import_from_csv.py` - CSV 数据导入工具

支持批量导入各类数据。

```bash
python tools/import_from_csv.py --type urban --input stations.csv --county jianxin
```

---

## 附录：配置示例

### 完整配置示例（吉安县）

```python
# 1. SUPPORTED_COUNTIES 中添加
{"name": "吉安县", "adcode": "360821", "center": [114.905, 27.040], "key": "jian"},

# 2. 添加县信息
COUNTY_INFO_JIAN = {
    "name": "吉安县",
    "province": "江西省",
    "city": "吉安市",
    "center": [114.905, 27.040],
    "adcode": "360821",
    "stats": {
        "gdp": None,
        "population": None,
        "car_total": None,
        "nev_total": None,
        "nev_rate": None,
    }
}

# 3. ALL_COUNTY_INFO 中注册
ALL_COUNTY_INFO = {
    "yiyang": COUNTY_INFO,
    "wannian": COUNTY_INFO_WANNIAN,
    "jian": COUNTY_INFO_JIAN,
}

# 4. 添加乡镇标注
TOWNSHIP_LABELS_JIAN = [
    {"name": "敦厚镇", "lng": 114.905, "lat": 27.040},
    {"name": "永阳镇", "lng": 114.850, "lat": 27.100},
    # ... 更多乡镇
]

# 5. ALL_TOWNSHIP_LABELS 中注册
ALL_TOWNSHIP_LABELS = {
    "yiyang": TOWNSHIP_LABELS,
    "wannian": TOWNSHIP_LABELS_WANNIAN,
    "jian": TOWNSHIP_LABELS_JIAN,
}
```

---

## 更新日志

- **2026-03-16**: 初始版本，支持快速新增县配置
- 支持多县联合视图
- 自动化工具链：`add_county.py` + `import_from_csv.py`
