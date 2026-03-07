"""
数据加载模块
负责从数据库加载充电桩、加油站等数据
"""
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from config import DATABASE, COUNTY_INFO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """数据加载器"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化数据加载器

        Args:
            db_path: 数据库路径，默认使用配置文件中的路径
        """
        self.db_path = db_path or DATABASE["path"]
        self.conn = None

    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            logger.info(f"✓ 连接数据库: {self.db_path}")
        except Exception as e:
            logger.error(f"✗ 数据库连接失败: {e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("✓ 关闭数据库连接")

    def load_urban_stations(self) -> List[Dict]:
        """
        加载城区现有充电站数据

        Returns:
            充电站列表，每个元素包含 name, addr, lng, lat
        """
        if not self.conn:
            self.connect()

        try:
            query = """
                SELECT station_name, address, longitude, latitude
                FROM stations_urban_coords
                WHERE longitude IS NOT NULL AND latitude IS NOT NULL
            """
            df = pd.read_sql(query, self.conn)

            stations = []
            for _, row in df.iterrows():
                stations.append({
                    "name": row["station_name"],
                    "addr": row["address"] or "",
                    "lng": float(row["longitude"]),
                    "lat": float(row["latitude"]),
                })

            logger.info(f"✓ 加载城区充电站: {len(stations)} 座")
            return stations

        except Exception as e:
            logger.error(f"✗ 加载城区充电站失败: {e}")
            return []

    def load_gas_stations(self) -> List[Dict]:
        """
        加载加油站数据

        Returns:
            加油站列表，每个元素包含 name, addr, has_ev, sales, revenue
        """
        if not self.conn:
            self.connect()

        try:
            query = """
                SELECT station_name, address, has_ev_charger,
                       total_sales, oil_revenue, longitude, latitude
                FROM gas_stations
            """
            df = pd.read_sql(query, self.conn)

            stations = []
            for _, row in df.iterrows():
                try:
                    lng = float(row["longitude"]) if pd.notna(row["longitude"]) else None
                    lat = float(row["latitude"]) if pd.notna(row["latitude"]) else None
                except:
                    lng, lat = None, None

                stations.append({
                    "name": row["station_name"],
                    "addr": row["address"] or "",
                    "has_ev": row["has_ev_charger"] in ("√", "✓", "是", "有"),
                    "sales": float(row["total_sales"]) if row["total_sales"] else 0,
                    "revenue": float(row["oil_revenue"]) if row["oil_revenue"] else 0,
                    "lng": lng,
                    "lat": lat,
                })

            logger.info(f"✓ 加载加油站: {len(stations)} 座")
            return stations

        except Exception as e:
            logger.error(f"✗ 加载加油站失败: {e}")
            return []

    def load_planned_stations(self) -> List[Dict]:
        """
        加载规划充电站数据

        Returns:
            规划站列表，每个元素包含 name, township, scene, qty, power, year, equip
        """
        if not self.conn:
            self.connect()

        try:
            query = """
                SELECT station_name, township, scene, quantity,
                       power_kw, year, equipment, longitude, latitude,
                       category, category_code
                FROM stations_planned
                WHERE station_name IS NOT NULL
            """
            df = pd.read_sql(query, self.conn)

            stations = []
            for _, row in df.iterrows():
                # 安全处理可能的NaN值
                try:
                    qty = int(row["quantity"]) if pd.notna(row["quantity"]) else 0
                    power = int(row["power_kw"]) if pd.notna(row["power_kw"]) else 0
                    year = int(row["year"]) if pd.notna(row["year"]) else 2026
                except (ValueError, TypeError):
                    qty = 0
                    power = 0
                    year = 2026

                try:
                    lng = float(row["longitude"]) if pd.notna(row["longitude"]) else None
                    lat = float(row["latitude"]) if pd.notna(row["latitude"]) else None
                except:
                    lng, lat = None, None

                stations.append({
                    "name": row["station_name"],
                    "township": row["township"] if pd.notna(row["township"]) else "",
                    "scene": row["scene"] if pd.notna(row["scene"]) else "",
                    "category": row["category"] if pd.notna(row["category"]) else "公共充电设施",
                    "category_code": int(row["category_code"]) if pd.notna(row["category_code"]) else 1,
                    "qty": qty,
                    "power": power,
                    "year": year,
                    "equip": row["equipment"] if pd.notna(row["equipment"]) else "",
                    "lng": lng,
                    "lat": lat,
                })

            logger.info(f"✓ 加载规划充电站: {len(stations)} 站")
            return stations

        except Exception as e:
            logger.error(f"✗ 加载规划充电站失败: {e}")
            return []

    def load_economic_stats(self) -> pd.DataFrame:
        """
        加载经济统计数据

        Returns:
            经济数据 DataFrame
        """
        if not self.conn:
            self.connect()

        try:
            query = """
                SELECT region, year, car_total, car_new, nev_total,
                       nev_new, nev_rate, gdp, fiscal_rev, population
                FROM economic_stats
                WHERE region = '弋阳'
                ORDER BY year
            """
            df = pd.read_sql(query, self.conn)
            logger.info(f"✓ 加载经济统计数据: {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"✗ 加载经济统计数据失败: {e}")
            return pd.DataFrame()

    def load_all_data(self) -> Dict:
        """
        加载所有数据

        Returns:
            包含所有数据的字典
        """
        self.connect()

        data = {
            "urban_stations": self.load_urban_stations(),
            "gas_stations": self.load_gas_stations(),
            "planned_stations": self.load_planned_stations(),
            "economic_stats": self.load_economic_stats(),
        }

        self.close()

        logger.info("✓ 所有数据加载完成")
        return data

    def get_statistics(self) -> Dict:
        """
        获取统计摘要

        Returns:
            统计数据字典
        """
        if not self.conn:
            self.connect()

        try:
            stats = {}

            # 现有充电站统计
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stations_urban_coords WHERE longitude IS NOT NULL")
            stats["existing_stations"] = cursor.fetchone()[0]

            # 加油站统计
            cursor.execute("SELECT COUNT(*) FROM gas_stations")
            stats["gas_stations"] = cursor.fetchone()[0]

            # 规划充电站统计
            cursor.execute("SELECT COUNT(*), SUM(quantity), SUM(power_kw) FROM stations_planned")
            result = cursor.fetchone()
            stats["planned_stations_count"] = result[0]
            stats["planned_piles_total"] = result[1] or 0
            stats["planned_power_total"] = result[2] or 0

            # 最新经济数据
            cursor.execute("""
                SELECT year, nev_total, car_total, gdp, population
                FROM economic_stats
                WHERE region = '弋阳'
                ORDER BY year DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                stats["latest_year"] = result[0]
                stats["nev_total"] = result[1]
                stats["car_total"] = result[2]
                stats["gdp"] = result[3]
                stats["population"] = result[4]

            logger.info("✓ 统计数据获取完成")
            return stats

        except Exception as e:
            logger.error(f"✗ 获取统计数据失败: {e}")
            return {}


# 测试代码
if __name__ == "__main__":
    loader = DataLoader()

    # 测试加载所有数据
    data = loader.load_all_data()

    print("\n===== 数据加载测试 =====")
    print(f"城区充电站: {len(data['urban_stations'])} 座")
    print(f"加油站: {len(data['gas_stations'])} 座")
    print(f"规划充电站: {len(data['planned_stations'])} 站")
    print(f"经济数据: {len(data['economic_stats'])} 条记录")

    # 测试统计数据
    loader.connect()
    stats = loader.get_statistics()
    loader.close()

    print("\n===== 统计摘要 =====")
    for key, value in stats.items():
        print(f"{key}: {value}")
