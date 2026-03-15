# 新增地区配置工具

此目录包含用于快速新增地区的自动化工具脚本。

## 工具脚本

### 1. `add_county.py` - 新增县配置工具

自动生成新增县所需的配置文件模板、SQL 导入模板、CSV 数据模板等。

**使用方法**:

```bash
# 基本用法
python tools/add_county.py --name 新建县 --key jianxin --adcode 360821 --center 115.5,27.5

# 交互式输入（省略参数将提示输入）
python tools/add_county.py

# 仅生成模板，不自动更新配置文件
python tools/add_county.py --name 新建县 --key jianxin --template-only
```

**输出内容**:
- 配置代码片段（用于添加到 `config.py`）
- SQL 导入模板
- CSV 数据模板（现有充电站、规划充电站、加油站）
- 边界占位文件
- 配置指南 README

### 2. `import_from_csv.py` - CSV 数据导入工具

从 CSV 文件批量导入数据到 SQLite 数据库。

**使用方法**:

```bash
# 导入现有充电站
python tools/import_from_csv.py --type urban --input urban_stations.csv --county jianxin

# 导入规划充电站
python tools/import_from_csv.py --type planned --input planned_stations.csv --county jianxin

# 导入加油站
python tools/import_from_csv.py --type gas --input gas_stations.csv --county jianxin

# 导入经济统计数据
python tools/import_from_csv.py --type economic --input economic_stats.csv --region jianxin

# 预演模式（仅预览，不实际写入）
python tools/import_from_csv.py --type urban --input urban_stations.csv --county jianxin --dry-run
```

**支持的数据类型**:
- `urban`: 现有充电站（`stations_urban_coords` 表）
- `planned`: 规划充电站（`stations_planned` 表）
- `gas`: 加油站（`gas_stations` 表）
- `economic`: 经济统计数据（`economic_stats` 表）

## 快速开始

### 场景：为新建县配置充换电设施规划系统

**步骤 1**: 运行配置工具

```bash
python tools/add_county.py --name 新建县 --key jianxin --adcode 360821 --center 115.5,27.5
```

**步骤 2**: 按照工具输出的 README 指南操作

**步骤 3**: 验证配置

```bash
curl http://localhost:5000/api/config
curl http://localhost:5000/api/boundary?county=jianxin
```

## 输出目录结构

运行 `add_county.py` 后，会在 `tools/county_setup_output/{key}/` 目录生成以下文件：

```
tools/county_setup_output/jianxin/
├── jianxin_config_snippet.txt    # 配置代码片段
├── jianxin_data_import.sql       # SQL 导入模板
├── README.md                     # 配置指南
├── jianxin_boundary_downloaded.json (如果下载成功)
└── csv_templates/
    ├── urban_stations_template.csv
    ├── planned_stations_template.csv
    └── gas_stations_template.csv
```

## 依赖

- Python 3.7+
- SQLite3
- 可选：`requests` 库（用于下载边界数据）

## 注意事项

1. **数据库备份**: `import_from_csv.py` 会在导入前自动备份数据库
2. **坐标格式**: 所有坐标使用 WGS84 坐标系（经纬度）
3. **县名一致性**: 确保 CSV 数据中的县名与数据库查询一致
4. **边界数据**: 建议从 DataV.GeoAtlas 获取准确的边界数据

## 相关文档

- 详细配置指南：`docs/ADD_COUNTY_GUIDE.md`
- 快速参考卡：`docs/QUICK_REFERENCE.md`
- 实施报告：`docs/IMPLEMENTATION_REPORT.md`

## 故障排除

### 问题：工具运行报错

**解决**:
1. 确保在 `yiyang_wannian_chongdian` 目录下运行
2. 确保 Python 环境已安装依赖
3. 使用 `--help` 查看参数说明

### 问题：CSV 导入失败

**解决**:
1. 检查 CSV 文件编码（应为 UTF-8 with BOM）
2. 检查 CSV 表头是否与模板一致
3. 使用 `--dry-run` 预览数据

### 问题：边界数据下载失败

**解决**:
1. DataV 接口可能临时不可用
2. 手动从 DataV 网站下载 GeoJSON
3. 使用工具生成的占位文件，后续替换

## 技术支持

如有问题，请查阅：
- `docs/ADD_COUNTY_GUIDE.md` - 完整配置指南
- `docs/QUICK_REFERENCE.md` - 快速参考卡
