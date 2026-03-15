#!/usr/bin/env python3
"""
新增县快速配置工具

使用此脚本快速新增一个县的配置，包括：
1. 生成县配置文件模板
2. 生成乡镇坐标导入模板（Excel/CSV）
3. 生成数据导入 SQL 模板
4. 自动下载县域边界 GeoJSON（可选）

使用方法:
    python tools/add_county.py --name 新建县 --key jianxin --adcode 360821 --center 115.5,27.5
"""

import argparse
import csv
import json
import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, DB_DIR, SUPPORTED_COUNTIES


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="新增县快速配置工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python tools/add_county.py --name 新建县 --key jianxin --adcode 360821 --center 115.5,27.5

  # 交互式输入（省略参数将提示输入）
  python tools/add_county.py

  # 仅生成配置模板
  python tools/add_county.py --name 新建县 --key jianxin --template-only
        """
    )

    parser.add_argument("--name", type=str, help="县名（如：新建县）")
    parser.add_argument("--key", type=str, help="县标识 key（如：jianxin，用于文件名和代码引用）")
    parser.add_argument("--adcode", type=str, help="行政区划代码（6 位数字，如：360821）")
    parser.add_argument("--center", type=str, help="县城中心坐标（格式：经度，纬度，如：115.5,27.5）")
    parser.add_argument("--province", type=str, default="江西省", help="所属省份（默认：江西省）")
    parser.add_argument("--city", type=str, default="XX 市", help="所属市（默认：XX 市）")
    parser.add_argument("--template-only", action="store_true", help="仅生成配置模板，不修改配置文件")

    return parser.parse_args()


def get_input(prompt, default=None, required=True):
    """获取用户输入"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    while True:
        value = input(prompt).strip()
        if not value and default:
            return default
        if not value and required:
            print("  ! 此项为必填，请重新输入")
            continue
        return value


def parse_center(center_str):
    """解析坐标字符串"""
    try:
        parts = center_str.replace("，", ",").split(",")
        if len(parts) != 2:
            return None
        lng = float(parts[0].strip())
        lat = float(parts[1].strip())
        if not (-180 <= lng <= 180) or not (-90 <= lat <= 90):
            return None
        return [lng, lat]
    except (ValueError, IndexError):
        return None


def validate_adcode(adcode):
    """验证行政区划代码"""
    if not adcode or len(adcode) != 6:
        return False
    try:
        int(adcode)
        return True
    except ValueError:
        return False


def generate_county_config(name, key, adcode, center, province, city):
    """生成县配置代码片段"""
    config = f"""
# ===== {name}基本信息 =====
COUNTY_INFO_{key.upper()} = {{
    "name": "{name}",
    "province": "{province}",
    "city": "{city}",
    "center": {center},  # 县城中心坐标
    "adcode": "{adcode}",  # 行政区划代码

    # 基本情况
    "stats": {{
        "gdp": None,  # 亿元
        "population": None,  # 万人
        "car_total": None,  # 万辆
        "nev_total": None,  # 万辆
        "nev_rate": None,  # %
    }}
}}
"""
    return config


def generate_township_labels_template(key):
    """生成乡镇标注配置模板"""
    template = f"""
# {key}乡镇标注（请补充实际数据）
TOWNSHIP_LABELS_{key.upper()} = [
    # 格式：{{"name": "乡镇名", "lng": 经度， "lat": 纬度}},
    # 示例：
    # {{"name": "XX 镇", "lng": 115.XX, "lat": 27.XX}},
]
"""
    return template


def generate_sql_template(county_name):
    """生成 SQL 导入模板"""
    sql = f"""
-- ========================================
-- {county_name}数据导入模板
-- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ========================================

-- 1. 导入现有充电站
-- 表结构：stations_urban_coords
-- 字段：station_name, address, longitude, latitude, county
INSERT INTO stations_urban_coords (station_name, address, longitude, latitude, county)
VALUES
    ('示例充电站 1', '示例地址 1', 115.XX, 27.XX, '{county_name}'),
    ('示例充电站 2', '示例地址 2', 115.XX, 27.XX, '{county_name}');
    -- 请复制上行添加更多数据

-- 2. 导入规划充电站
-- 表结构：stations_planned
-- 字段：station_name, township, scene, quantity, power_kw, year, longitude, latitude, county
INSERT INTO stations_planned (station_name, township, scene, quantity, power_kw, year, longitude, latitude, county)
VALUES
    ('示例规划站 1', 'XX 镇', '场景描述', 10, 1000, 2026, 115.XX, 27.XX, '{county_name}'),
    ('示例规划站 2', 'XX 镇', '场景描述', 8, 800, 2026, 115.XX, 27.XX, '{county_name}');
    -- 请复制上行添加更多数据

-- 3. 导入加油站
-- 表结构：gas_stations
-- 字段：station_name, address, longitude, latitude, county
INSERT INTO gas_stations (station_name, address, longitude, latitude, county)
VALUES
    ('示例加油站 1', '示例地址 1', 115.XX, 27.XX, '{county_name}'),
    ('示例加油站 2', '示例地址 2', 115.XX, 27.XX, '{county_name}');
    -- 请复制上行添加更多数据

-- 4. 导入经济统计数据（可选）
-- 表结构：economic_stats
-- 字段：region, year, gdp, population, ...
INSERT INTO economic_stats (region, year, gdp, population)
VALUES
    ('{county_name}', 2025, NULL, NULL);

-- ========================================
-- 验证查询
-- ========================================
-- 检查现有充电站
SELECT COUNT(*) FROM stations_urban_coords WHERE county = '{county_name}';

-- 检查规划充电站
SELECT COUNT(*) FROM stations_planned WHERE county = '{county_name}';

-- 检查加油站
SELECT COUNT(*) FROM gas_stations WHERE county = '{county_name}';
"""
    return sql


def generate_csv_template(filepath, fields):
    """生成 CSV 模板文件"""
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        # 添加示例行
        if 'station_name' in fields:
            writer.writerow(['示例站名', '示例地址', 115.5, 27.5, '示例县'])


def download_boundary_geojson(adcode, output_path):
    """
    尝试从 DataV 下载县域边界 GeoJSON

    注意：DataV 目前已不再提供直接下载，此功能作为备选
    """
    # DataV GeoAtlas API（已限制访问，作为备选）
    url = f"https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json"

    try:
        import requests
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            geojson = response.json()
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, ensure_ascii=False, indent=2)
            return True, output_path
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


def generate_boundary_placeholder(key, center, output_path):
    """生成占位边界文件"""
    # 创建一个简单的矩形边界作为占位
    lng, lat = center
    delta = 0.2  # 约 20km 范围

    boundary = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {
                "name": f"{key}_county",
                "center": center,
                "adcode": None
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lng - delta, lat - delta],
                    [lng + delta, lat - delta],
                    [lng + delta, lat + delta],
                    [lng - delta, lat + delta],
                    [lng - delta, lat - delta]
                ]]
            }
        }]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(boundary, f, ensure_ascii=False, indent=2)

    return output_path


def update_config_files(key, name, adcode, center):
    """更新配置文件（可选自动更新）"""
    config_path = Path(__file__).parent.parent / "config.py"

    # 读取当前配置
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已存在
    if f'"key": "{key}"' in content:
        print(f"  ! 县配置 '{key}' 已存在，跳过自动更新")
        return False

    # 添加到 SUPPORTED_COUNTIES
    counties_marker = "# ===== 支持的多县列表 ====="
    if counties_marker in content:
        # 在 SUPPORTED_COUNTIES 列表中添加新县
        new_entry = f'    {{"name": "{name}", "adcode": "{adcode}", "center": {center}, "key": "{key}"}},'

        # 找到 SUPPORTED_COUNTIES 的结束位置
        import re
        match = re.search(r'(SUPPORTED_COUNTIES\s*=\s*\[)([\s\S]*?)(\])', content)
        if match:
            before_list = content[:match.start(3)]
            after_list = content[match.end(3):]
            # 在最后一个元素后添加逗号和新元素
            content = before_list.rstrip() + "\n" + new_entry + "\n" + after_list

    # 写回配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✓ 已自动更新 config.py")
    return True


def init_database_tables(db_path, county_name):
    """初始化数据库表结构（如果不存在）"""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 检查表是否存在
    tables = {
        "stations_urban_coords": """
            CREATE TABLE IF NOT EXISTS stations_urban_coords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_name TEXT NOT NULL,
                address TEXT,
                longitude REAL NOT NULL,
                latitude REAL NOT NULL,
                county TEXT NOT NULL DEFAULT '弋阳县',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "stations_planned": """
            CREATE TABLE IF NOT EXISTS stations_planned (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_name TEXT NOT NULL,
                township TEXT,
                scene TEXT,
                quantity INTEGER DEFAULT 0,
                power_kw REAL DEFAULT 0,
                year INTEGER DEFAULT 2026,
                longitude REAL,
                latitude REAL,
                county TEXT NOT NULL DEFAULT '弋阳县',
                category TEXT,
                category_code TEXT,
                equipment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "gas_stations": """
            CREATE TABLE IF NOT EXISTS gas_stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_name TEXT NOT NULL,
                address TEXT,
                longitude REAL NOT NULL,
                latitude REAL NOT NULL,
                county TEXT NOT NULL DEFAULT '弋阳县',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "economic_stats": """
            CREATE TABLE IF NOT EXISTS economic_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                year INTEGER NOT NULL,
                gdp REAL,
                population REAL,
                car_total REAL,
                nev_total REAL,
                nev_rate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    }

    for table_name, create_sql in tables.items():
        cursor.execute(create_sql)
        print(f"  ✓ 表 '{table_name}' 已就绪")

    conn.commit()
    conn.close()
    print(f"  ✓ 数据库表结构检查完成")


def main():
    """主函数"""
    args = parse_args()

    print("\n" + "=" * 60)
    print("  新增县快速配置工具")
    print("=" * 60 + "\n")

    # 获取县信息
    if not args.name:
        print("请输入新县的基本信息：\n")
        name = get_input("县名（如：新建县）")
        key = get_input("县标识 key（如：jianxin，用于文件名和代码引用）")
        adcode = get_input("行政区划代码（6 位数字）")
        while not validate_adcode(adcode):
            print("  ! 无效的行政区划代码，请输入 6 位数字")
            adcode = get_input("行政区划代码（6 位数字）")
        center_str = get_input("县城中心坐标（格式：经度，纬度）")
        center = parse_center(center_str)
        while not center:
            print("  ! 无效的坐标格式，请使用：经度，纬度")
            center_str = get_input("县城中心坐标（格式：经度，纬度）")
            center = parse_center(center_str)
        province = get_input("所属省份", default="江西省")
        city = get_input("所属市")
    else:
        name = args.name
        key = args.key
        adcode = args.adcode
        center = parse_center(args.center) if args.center else None
        province = args.province
        city = args.city

        # 验证输入
        if not key:
            print("错误：--key 参数必填")
            sys.exit(1)
        if not validate_adcode(adcode):
            print("错误：无效的行政区划代码")
            sys.exit(1)
        if not center:
            print("错误：无效的坐标格式")
            sys.exit(1)

    print(f"\n✓ 县信息确认:")
    print(f"  县名：{name}")
    print(f"  标识：{key}")
    print(f"  区划代码：{adcode}")
    print(f"  中心坐标：{center}")
    print(f"  所属省市：{province} {city}")

    # 创建输出目录
    tools_dir = Path(__file__).parent
    output_dir = tools_dir / "county_setup_output" / key
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n✓ 生成配置文件...")

    # 1. 生成县配置代码片段
    config_code = generate_county_config(name, key, adcode, center, province, city)
    township_template = generate_township_labels_template(key)

    config_file = output_dir / f"{key}_config_snippet.txt"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write("# 将此配置添加到 config.py\n\n")
        f.write(config_code)
        f.write(township_template)
        f.write(f"\n# 在 ALL_COUNTY_INFO 中添加:\n# \"{key}\": COUNTY_INFO_{key.upper()},\n")
        f.write(f"\n# 在 ALL_TOWNSHIP_LABELS 中添加:\n# \"{key}\": TOWNSHIP_LABELS_{key.upper()},\n")
    print(f"  ✓ 配置代码片段：{config_file}")

    # 2. 生成 SQL 导入模板
    sql_template = generate_sql_template(name)
    sql_file = output_dir / f"{key}_data_import.sql"
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(sql_template)
    print(f"  ✓ SQL 导入模板：{sql_file}")

    # 3. 生成 CSV 数据导入模板
    csv_dir = output_dir / "csv_templates"
    csv_dir.mkdir(parents=True, exist_ok=True)

    # 现有充电站 CSV 模板
    urban_csv = csv_dir / "urban_stations_template.csv"
    generate_csv_template(
        urban_csv,
        ['station_name', 'address', 'longitude', 'latitude', 'county']
    )
    print(f"  ✓ 现有充电站 CSV 模板：{urban_csv}")

    # 规划充电站 CSV 模板
    planned_csv = csv_dir / "planned_stations_template.csv"
    generate_csv_template(
        planned_csv,
        ['station_name', 'township', 'scene', 'quantity', 'power_kw', 'year', 'longitude', 'latitude', 'county']
    )
    print(f"  ✓ 规划充电站 CSV 模板：{planned_csv}")

    # 加油站 CSV 模板
    gas_csv = csv_dir / "gas_stations_template.csv"
    generate_csv_template(
        gas_csv,
        ['station_name', 'address', 'longitude', 'latitude', 'county']
    )
    print(f"  ✓ 加油站 CSV 模板：{gas_csv}")

    # 4. 生成边界文件占位符
    boundary_file = DATA_DIR / f"{key}_county.geojson"
    if not boundary_file.exists():
        generate_boundary_placeholder(key, center, boundary_file)
        print(f"  ✓ 边界占位文件：{boundary_file}")
        print(f"     提示：请替换为真实的 GeoJSON 边界数据")
    else:
        print(f"  ! 边界文件已存在：{boundary_file}")

    # 5. 尝试下载真实边界数据（可选）
    print(f"\n✓ 尝试下载县域边界数据...")
    boundary_download_path = output_dir / f"{key}_boundary_downloaded.json"
    success, result = download_boundary_geojson(adcode, boundary_download_path)
    if success:
        print(f"  ✓ 边界数据下载成功：{result}")
        print(f"     请检查数据准确性后复制到 data/{key}_county.geojson")
    else:
        print(f"  ! 边界数据下载失败：{result}")
        print(f"     请手动准备 GeoJSON 边界文件")

    # 6. 初始化数据库表
    print(f"\n✓ 初始化数据库表结构...")
    db_path = DB_DIR / "yiyang_ev.db"
    init_database_tables(db_path, name)

    # 7. 生成 README
    readme = output_dir / "README.md"
    readme_content = f"""# {name}配置指南

## 快速开始

### 1. 更新配置文件

将 `{config_file.name}` 中的配置代码复制到 `config.py`:

1. 在 `ALL_COUNTY_INFO` 字典中添加县信息
2. 在 `ALL_TOWNSHIP_LABELS` 字典中添加乡镇标注
3. 在 `SUPPORTED_COUNTIES` 列表中添加县配置

### 2. 准备边界数据

- 占位文件：`data/{key}_county.geojson`
- 下载文件：`{key}_boundary_downloaded.json`（如果下载成功）

请从以下来源获取准确的边界数据：
- DataV.GeoAtlas: https://datav.aliyun.com/portal/school/atlas/area_selector
- 天地图 API
- 高德地图 API

### 3. 导入数据

#### 方法一：使用 SQL（推荐批量导入）

```bash
sqlite3 db/yiyang_ev.db < {sql_file.name}
```

#### 方法二：使用 CSV + Python 脚本

1. 将数据填入 CSV 模板文件
2. 运行导入脚本：

```bash
python tools/import_data_from_csv.py --county {key} --input csv_templates/
```

### 4. 更新前端

在 `frontend/index.html` 的 `<select id="county-selector">` 中添加:

```html
<option value="{key}">{name}</option>
```

### 5. 验证

启动应用后，访问以下 API 验证:

- `/api/config` - 检查县配置
- `/api/boundary?county={key}` - 检查边界数据
- `/api/stations/urban?county={key}` - 检查现有充电站
- `/api/townships?county={key}` - 检查乡镇标注

## 配置清单

- [ ] config.py 配置完成
- [ ] 边界文件准备完成
- [ ] 乡镇坐标录入完成
- [ ] 数据导入完成
- [ ] 前端选项添加完成
- [ ] API 验证通过

## 文件结构

```
{output_dir}/
├── {config_file.name}          # 配置代码片段
├── {sql_file.name}             # SQL 导入模板
├── {readme.name}               # 本文件
├── csv_templates/              # CSV 数据模板
│   ├── urban_stations_template.csv
│   ├── planned_stations_template.csv
│   └── gas_stations_template.csv
└── {key}_boundary_downloaded.json (如果下载成功)
```

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    with open(readme, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"  ✓ 配置指南：{readme}")

    # 询问是否自动更新配置文件
    if not args.template_only:
        print(f"\n✓ 是否自动更新 config.py? (y/n): ", end="")
        choice = input().strip().lower()
        if choice == 'y':
            update_config_files(key, name, adcode, center)

    print("\n" + "=" * 60)
    print(f"  ✓ {name}配置生成完成!")
    print(f"  输出目录：{output_dir}")
    print(f"  请阅读 {readme.name} 了解后续步骤")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
