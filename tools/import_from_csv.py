#!/usr/bin/env python3
"""
CSV 数据导入工具

将 CSV 格式的数据导入 SQLite 数据库
支持导入：现有充电站、规划充电站、加油站、经济统计数据

使用方法:
    python tools/import_from_csv.py --type urban --input data.csv --county jianxin
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="CSV 数据导入工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 导入现有充电站
  python tools/import_from_csv.py --type urban --input urban_stations.csv --county jianxin

  # 导入规划充电站
  python tools/import_from_csv.py --type planned --input planned_stations.csv --county jianxin

  # 导入加油站
  python tools/import_from_csv.py --type gas --input gas_stations.csv --county jianxin

  # 导入经济统计数据
  python tools/import_from_csv.py --type economic --input economic_stats.csv --region jianxin
        """
    )

    parser.add_argument("--type", type=str, required=True,
                        choices=["urban", "planned", "gas", "economic"],
                        help="数据类型：urban=现有充电站，planned=规划充电站，gas=加油站，economic=经济统计")
    parser.add_argument("--input", type=str, required=True, help="输入 CSV 文件路径")
    parser.add_argument("--county", type=str, default=None, help="县名（用于 urban/planned/gas 类型）")
    parser.add_argument("--region", type=str, default=None, help="地区名（用于 economic 类型）")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际写入数据库")
    parser.add_argument("--batch-size", type=int, default=100, help="批量插入数量（默认：100）")

    return parser.parse_args()


def read_csv(filepath):
    """读取 CSV 文件"""
    rows = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def import_urban_stations(conn, rows, county, batch_size=100):
    """导入现有充电站"""
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO stations_urban_coords (station_name, address, longitude, latitude, county)
        VALUES (?, ?, ?, ?, ?)
    """

    count = 0
    batch = []

    for row in rows:
        try:
            station_name = row.get('station_name', '').strip()
            address = row.get('address', '').strip()
            longitude = float(row.get('longitude', 0))
            latitude = float(row.get('latitude', 0))
            county_val = county or row.get('county', '弋阳县').strip()

            if not station_name:
                print(f"  ! 跳过空站名行")
                continue

            batch.append((station_name, address, longitude, latitude, county_val))

            if len(batch) >= batch_size:
                cursor.executemany(insert_sql, batch)
                count += len(batch)
                batch = []

        except (ValueError, KeyError) as e:
            print(f"  ! 数据格式错误：{e}")
            continue

    # 插入剩余数据
    if batch:
        cursor.executemany(insert_sql, batch)
        count += len(batch)

    return count


def import_planned_stations(conn, rows, county, batch_size=100):
    """导入规划充电站"""
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO stations_planned
        (station_name, township, scene, quantity, power_kw, year, longitude, latitude, county)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    count = 0
    batch = []

    for row in rows:
        try:
            station_name = row.get('station_name', '').strip()
            township = row.get('township', '').strip()
            scene = row.get('scene', '').strip()
            quantity = int(row.get('quantity', 0) or 0)
            power_kw = float(row.get('power_kw', 0) or 0)
            year = int(row.get('year', 2026) or 2026)
            longitude = float(row.get('longitude', 0) or 0)
            latitude = float(row.get('latitude', 0) or 0)
            county_val = county or row.get('county', '弋阳县').strip()

            if not station_name:
                print(f"  ! 跳过空站名行")
                continue

            batch.append((station_name, township, scene, quantity, power_kw, year,
                         longitude, latitude, county_val))

            if len(batch) >= batch_size:
                cursor.executemany(insert_sql, batch)
                count += len(batch)
                batch = []

        except (ValueError, KeyError) as e:
            print(f"  ! 数据格式错误：{e}")
            continue

    if batch:
        cursor.executemany(insert_sql, batch)
        count += len(batch)

    return count


def import_gas_stations(conn, rows, county, batch_size=100):
    """导入加油站"""
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO gas_stations (station_name, address, longitude, latitude, county)
        VALUES (?, ?, ?, ?, ?)
    """

    count = 0
    batch = []

    for row in rows:
        try:
            station_name = row.get('station_name', '').strip()
            address = row.get('address', '').strip()
            longitude = float(row.get('longitude', 0))
            latitude = float(row.get('latitude', 0))
            county_val = county or row.get('county', '弋阳县').strip()

            if not station_name:
                print(f"  ! 跳过空站名行")
                continue

            batch.append((station_name, address, longitude, latitude, county_val))

            if len(batch) >= batch_size:
                cursor.executemany(insert_sql, batch)
                count += len(batch)
                batch = []

        except (ValueError, KeyError) as e:
            print(f"  ! 数据格式错误：{e}")
            continue

    if batch:
        cursor.executemany(insert_sql, batch)
        count += len(batch)

    return count


def import_economic_stats(conn, rows, region, batch_size=100):
    """导入经济统计数据"""
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO economic_stats
        (region, year, gdp, population, car_total, nev_total, nev_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    count = 0
    batch = []

    for row in rows:
        try:
            region_val = region or row.get('region', '').strip()
            year = int(row.get('year', 0) or 0)
            gdp = float(row.get('gdp', 0) or 0) if row.get('gdp') else None
            population = float(row.get('population', 0) or 0) if row.get('population') else None
            car_total = float(row.get('car_total', 0) or 0) if row.get('car_total') else None
            nev_total = float(row.get('nev_total', 0) or 0) if row.get('nev_total') else None
            nev_rate = float(row.get('nev_rate', 0) or 0) if row.get('nev_rate') else None

            if not region_val or not year:
                print(f"  ! 跳过无效数据行")
                continue

            batch.append((region_val, year, gdp, population, car_total, nev_total, nev_rate))

            if len(batch) >= batch_size:
                cursor.executemany(insert_sql, batch)
                count += len(batch)
                batch = []

        except (ValueError, KeyError) as e:
            print(f"  ! 数据格式错误：{e}")
            continue

    if batch:
        cursor.executemany(insert_sql, batch)
        count += len(batch)

    return count


def main():
    """主函数"""
    args = parse_args()

    print("\n" + "=" * 60)
    print("  CSV 数据导入工具")
    print("=" * 60 + "\n")

    # 检查输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误：文件不存在：{input_path}")
        sys.exit(1)

    # 读取 CSV
    print(f"读取 CSV 文件：{input_path}")
    rows = read_csv(input_path)
    print(f"  ✓ 读取 {len(rows)} 行数据\n")

    if not rows:
        print("警告：CSV 文件为空")
        return

    # 预览数据
    print("数据预览（前 3 行）:")
    for i, row in enumerate(rows[:3]):
        print(f"  {i+1}. {row}")
    print()

    if args.dry_run:
        print("【预演模式】不写入数据库\n")
        return

    # 连接数据库
    db_path = DATABASE["path"]
    print(f"连接数据库：{db_path}")

    # 备份数据库
    backup_path = str(db_path) + f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(str(db_path), backup_path)
        print(f"  ✓ 数据库已备份：{Path(backup_path).name}")
    except Exception as e:
        print(f"  ! 备份失败：{e}")

    conn = sqlite3.connect(str(db_path))

    try:
        # 导入数据
        print(f"\n开始导入 {args.type} 类型数据...")

        if args.type == "urban":
            count = import_urban_stations(conn, rows, args.county, args.batch_size)
            print(f"  ✓ 导入现有充电站：{count} 座")

        elif args.type == "planned":
            count = import_planned_stations(conn, rows, args.county, args.batch_size)
            print(f"  ✓ 导入规划充电站：{count} 座")

        elif args.type == "gas":
            count = import_gas_stations(conn, rows, args.county, args.batch_size)
            print(f"  ✓ 导入加油站：{count} 座")

        elif args.type == "economic":
            count = import_economic_stats(conn, rows, args.region, args.batch_size)
            print(f"  ✓ 导入经济统计：{count} 条")

        # 提交事务
        conn.commit()
        print(f"\n✓ 数据导入完成!")

        # 验证查询
        cursor = conn.cursor()
        if args.type in ("urban", "planned", "gas"):
            county = args.county or '未知'
            if args.type == "urban":
                cursor.execute("SELECT COUNT(*) FROM stations_urban_coords WHERE county = ?", (county,))
            elif args.type == "planned":
                cursor.execute("SELECT COUNT(*) FROM stations_planned WHERE county = ?", (county,))
            elif args.type == "gas":
                cursor.execute("SELECT COUNT(*) FROM gas_stations WHERE county = ?", (county,))
            result = cursor.fetchone()
            if result:
                print(f"  验证：{county} 县共有 {result[0]} 条记录")

    except Exception as e:
        conn.rollback()
        print(f"\n错误：导入失败：{e}")
        print(f"已回滚事务，数据未修改")
        sys.exit(1)
    finally:
        conn.close()

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
