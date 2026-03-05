# 数据库字段说明

**文件**：`db/yiyang_ev.db`（SQLite 3）
**字符集**：UTF-8
**连接示例**：
```python
import sqlite3
conn = sqlite3.connect(r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db")
```

---

## 表 1：economic_stats（历年社会经济与汽车数据）

**来源**：`基础数据统计（弋阳）(2).xlsx` → Sheet「基础数据统计」
**说明**：同时包含弋阳县（region='弋阳'）和上饶市（region='上饶'）数据，用于对比分析

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| id | INTEGER | 主键 | 1 |
| region | TEXT | 地区：弋阳 / 上饶 | 弋阳 |
| year | INTEGER | 统计年度 | 2025 |
| car_total | REAL | 汽车保有量（万辆） | 5.986 |
| car_new | REAL | 年度新增汽车（万辆） | 0.1664 |
| nev_total | REAL | 新能源车保有量（万辆） | 0.3225 |
| nev_new | REAL | 年度新增新能源汽车（万辆） | NULL（部分年份缺失） |
| nev_rate | REAL | 新能源渗透率（%） | NULL |
| gdp | REAL | GDP（亿元） | 203.94 |
| fiscal_rev | REAL | 财政收入（亿元） | NULL（2025待公布） |
| population | REAL | 常住人口（万人） | 32.94 |
| remark | TEXT | 备注说明 | NULL |

**常用查询**：
```sql
-- 弋阳近年新能源趋势
SELECT year, nev_total, gdp FROM economic_stats WHERE region='弋阳' ORDER BY year;
```

---

## 表 2：stations_existing_township（各乡镇现有充电桩台账）

**来源**：`各乡镇充电桩数量.xls` → Sheet1
**说明**：截至数据收集时（约 2025 年初）各乡镇充电桩的台账登记，共 14 条记录、44 台合计

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| id | INTEGER | 主键 | 1 |
| seq | INTEGER | 原表序号 | 1 |
| township | TEXT | 乡镇名称 | 南岩镇 |
| location | TEXT | 具体坐落地点 | 弋阳县人民政府后停车场 |
| quantity | INTEGER | 充电桩数量（台） | 18 |
| spec | TEXT | 规格备注 | 20kw单枪 / 120kw双枪 |

**注意**：此表与 `stations_status_2025` 有部分重叠，两表统计口径不同：
- 本表：乡镇台账，字段简单，合计 44 台
- `stations_status_2025`：2025年申报填报表，含功率/场景等，合计 152 台

---

## 表 3：stations_status_2025（2025年充电设施现状）

**来源**：`基础数据统计（弋阳）(2).xlsx` → Sheet「弋阳现状(2025年）」
**说明**：2025年申报时填报的公共充换电设施现状，含详细运营参数，共 33 条记录

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| id | INTEGER | 主键 | 1 |
| township | TEXT | 所属乡镇/街道 | 南岩 / 弋江 / 桃源 |
| station_name | TEXT | 充电站名称 | 弋阳县人民政府后停车场 |
| quantity | INTEGER | 充电桩数量（台） | 18 |
| swap_stations | INTEGER | 换电站数量（座），均为 0 | 0 |
| total_power_kw | REAL | 总功率（kW） | 360.0 |
| power_util_pct | REAL | 功率利用率（%） | 1.0 |
| above_120kw | INTEGER | 120kW 及以上充电桩数量（台） | 0 |
| scene | TEXT | 应用场景 | 单位停车场 / 社会停车场 |
| tech_mode | TEXT | 新技术新模式应用 | NULL（多数未填） |
| build_year | INTEGER | 建设年度 | 2024 / 2025 |
| car_pile_ratio | REAL | 车桩比 | NULL（多数未填） |

**应用场景枚举值**：单位停车场、社会停车场（主要两类）

---

## 表 4：stations_urban_coords（城区充电站坐标）

**来源**：`弋阳县城范围内充电站.xlsx` → Sheet1
**说明**：城区 16 座充电站的高德地图坐标，已验证可直接用于地图打点，坐标系为 GCJ-02

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| id | INTEGER | 主键 | 1 |
| station_name | TEXT | 场站名称 | 弋阳一中充电站 |
| address | TEXT | 详细地址（文字描述） | 江西省上饶市弋阳县弋阳县第一中内学生宿舍旁停车场 |
| longitude | REAL | 高德经度（GCJ-02） | 117.434497 |
| latitude | REAL | 高德纬度（GCJ-02） | 28.4080807 |

**坐标系说明**：GCJ-02（火星坐标系），与高德/腾讯地图直接兼容，
转换为 WGS-84（GPS/谷歌）需偏移修正。

---

## 表 5：stations_planned（2026-2028规划充电站清单）

**来源**：`计划规模汇总及统计表（弋阳）.xlsx` → Sheet「2026-2028年清单（弋阳）」
**说明**：当前申报的规划建设清单，共 34 个站点，**目前仅有 2026 年数据**（2027/2028 待补充）

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| id | INTEGER | 主键 | 1 |
| plan_no | INTEGER | 规划序号（乡镇级） | 1 |
| township | TEXT | 所在乡镇/街道 | 弋江 / 南岩 / 桃源 / 花亭 / 三县岭 |
| year | INTEGER | 计划建设年度 | 2026 |
| scene | TEXT | 应用场景 | 社会停车场 / 单位停车场 / 集聚点 / 产业集聚区 |
| station_name | TEXT | 站点名称/地点描述 | 式平路边停车场（湾里路） |
| quantity | INTEGER | 实际充电桩数量（台） | 2 |
| power_kw | REAL | 总功率（kW） | 240.0 |
| spec | TEXT | 规格说明 | 规格：120kW双枪/台 |
| land_area | REAL | 占地面积（m²）| 2.6（部分填写） |
| conv_factor | REAL | 折算系数 | 1.0 |
| std_piles | INTEGER | 折算标准桩数 | 2 |
| tech_mode | TEXT | 新技术新模式 | NULL |
| equipment | TEXT | 配电设备容量 | 新增一台315KVA箱变 |
| reporter | TEXT | 填报单位 | NULL |
| longitude | REAL | 地理编码经度（GCJ-02）| 浏览器端编码，可能有偏差 |
| latitude | REAL | 地理编码纬度（GCJ-02）| 同上 |
| geocode_addr | TEXT | 编码时使用的地址 | 弋阳县式平路 |

**乡镇分布**：弋江（28台）、南岩（25台）、桃源（10台）、花亭（2台）、三县岭（待定）
**场景分布**：社会停车场（44台）、单位停车场（13台）、集聚点（6台）、产业集聚区（2台）
**总规模**：63台，总功率 7,220 kW

---

## 表 6：gas_stations（2024年加油站详情）

**来源**：`（弋阳县）附表3：2024年度江西省加油站详细情况登记表.xls` → Sheet1
**说明**：全县 26 座加油站详情，是充电桩改造潜力分析的重要数据，5 座已有充电设施

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| id | INTEGER | 主键 | 1 |
| county | TEXT | 所属县 | 弋阳 |
| station_name | TEXT | 加油站名称 | 城南加油站 |
| address | TEXT | 详细地址 | 弋阳县南岩镇志敏大道旁 |
| ownership | TEXT | 所有制性质 | 中石化 / 中石油 / 民营 |
| operation_type | TEXT | 经营类型（暂未解析） | NULL |
| petrol_sales | REAL | 年汽油销量（吨） | 5619.0 |
| diesel_sales | REAL | 年柴油销量（吨） | 301.0 |
| total_sales | REAL | 年合计销量（吨） | 5921.0 |
| storage_cap | REAL | 总储油能力（立方米） | 120.0 |
| has_ev_charger | TEXT | 是否有充电设施：√ / 否 / NULL | √ |
| oil_revenue | REAL | 成品油销售收入（万元） | 6031.0 |
| non_oil_revenue | REAL | 非油品业务销售收入（万元） | 199.0 |
| location_type | TEXT | 站点属性 | 城区 / 省道国道 / 县乡道农网 / 高速公路 |
| built_year | TEXT | 建站时间 | 2000.10.1 |
| contact | TEXT | 法定代表人联系电话 | 13979300128 |
| longitude | REAL | 地理编码经度（GCJ-02）| 浏览器端编码，可能有偏差 |
| latitude | REAL | 地理编码纬度（GCJ-02）| 同上 |
| geocode_addr | TEXT | 编码时使用的地址 | — |

**改造潜力分析**：
- 已有充电设施：5 座（√）
- 明确无充电设施：3 座（否）
- 待核实：18 座（NULL，原表未填）
- 改造优先级参考：城区（3座，年均销量4124吨）> 省道国道（13座）> 县乡道（7座）

---

## 常用分析 SQL

```sql
-- 2026年规划总量
SELECT SUM(quantity) AS total_piles, ROUND(SUM(power_kw),0) AS total_kw
FROM stations_planned WHERE year=2026;
-- 结果：63台，7220kW

-- 各乡镇规划分布
SELECT township, SUM(quantity) AS qty, ROUND(SUM(power_kw),0) AS kw
FROM stations_planned GROUP BY township ORDER BY qty DESC;

-- 现有+规划 合并统计
SELECT '现有(台账)' AS 类型, SUM(quantity) AS 数量 FROM stations_existing_township
UNION
SELECT '现有(2025报表)', SUM(quantity) FROM stations_status_2025
UNION
SELECT '规划2026新增', SUM(quantity) FROM stations_planned WHERE year=2026;

-- 加油站改造优先级（按年销量排序，筛选未有充电设施）
SELECT station_name, address, location_type, total_sales, storage_cap
FROM gas_stations
WHERE has_ev_charger != '√' OR has_ev_charger IS NULL
ORDER BY total_sales DESC NULLS LAST;

-- 新能源车增速
SELECT year, nev_total,
       ROUND((nev_total - LAG(nev_total) OVER (ORDER BY year)) /
              LAG(nev_total) OVER (ORDER BY year) * 100, 1) AS yoy_pct
FROM economic_stats WHERE region='弋阳' AND nev_total IS NOT NULL;
```
