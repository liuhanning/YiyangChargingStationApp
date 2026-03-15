"""
数据加载模块
负责从数据库加载充电桩、加油站等数据
支持弋阳县和万年县
"""
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from config import DATABASE, COUNTY_INFO, COUNTY_INFO_WANNIAN, SUPPORTED_COUNTIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """数据加载器"""

    def __init__(self, db_path: Optional[Path] = None, county: str = "yiyang"):
        """
        初始化数据加载器

        Args:
            db_path: 数据库路径，默认使用配置文件中的路径
            county: 县名标识，支持 "yiyang"（弋阳）和 "wannian"（万年）
        """
        self.db_path = db_path or DATABASE["path"]
        self.county = county
        self.conn = None

    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            logger.info(f"✓ 连接数据库：{self.db_path} ({self.county})")
        except Exception as e:
            logger.error(f"✗ 数据库连接失败：{e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("✓ 关闭数据库连接")

    def load_urban_stations(self, county_filter: Optional[str] = None) -> List[Dict]:
        """加载城区现有充电站数据"""
        if not self.conn:
            self.connect()

        try:
            # 根据县别过滤数据
            if county_filter == "wannian":
                # 万年县现有充电站数据 —— 从 stations_urban_coords 取（county='万年'）
                query = """
                    SELECT station_name, address, longitude, latitude
                    FROM stations_urban_coords
                    WHERE county = '万年' AND longitude IS NOT NULL AND latitude IS NOT NULL
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
            elif county_filter == "yiyang":
                # 弋阳县现有充电站数据
                query = """
                    SELECT station_name, address, longitude, latitude
                    FROM stations_urban_coords
                    WHERE county = '弋阳县' AND longitude IS NOT NULL AND latitude IS NOT NULL
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
            elif county_filter in ("jian", "suichuan"):
                # 吉安县 / 遂川县
                _cn_map = {"jian": "吉安县", "suichuan": "遂川县"}
                county_db = _cn_map[county_filter]
                query = """
                    SELECT station_name, address, longitude, latitude
                    FROM stations_urban_coords
                    WHERE county = ? AND longitude IS NOT NULL AND latitude IS NOT NULL
                """
                df = pd.read_sql(query, self.conn, params=(county_db,))
                stations = []
                for _, row in df.iterrows():
                    stations.append({
                        "name": row["station_name"],
                        "addr": row["address"] or "",
                        "lng": float(row["longitude"]),
                        "lat": float(row["latitude"]),
                    })
            else:
                # 联合视图：加载弋阳县和万年县的所有数据
                # 先加载弋阳县数据
                query1 = """
                    SELECT station_name, address, longitude, latitude
                    FROM stations_urban_coords
                    WHERE county = '弋阳县' AND longitude IS NOT NULL AND latitude IS NOT NULL
                """
                df1 = pd.read_sql(query1, self.conn)

                stations = []
                for _, row in df1.iterrows():
                    stations.append({
                        "name": row["station_name"],
                        "addr": row["address"] or "",
                        "lng": float(row["longitude"]),
                        "lat": float(row["latitude"]),
                    })

                # 再加载万年县数据
                query2 = """
                    SELECT station_name, address, longitude, latitude
                    FROM stations_urban_coords
                    WHERE county = '万年' AND longitude IS NOT NULL AND latitude IS NOT NULL
                """
                df2 = pd.read_sql(query2, self.conn)

                for _, row in df2.iterrows():
                    stations.append({
                        "name": row["station_name"],
                        "addr": row["address"] or "",
                        "lng": float(row["longitude"]),
                        "lat": float(row["latitude"]),
                    })

            logger.info(f"✓ 加载城区充电站：{len(stations)} 座")
            return stations

        except Exception as e:
            logger.error(f"✗ 加载城区充电站失败：{e}")
            return []

    def load_gas_stations(self, county_filter: Optional[str] = None) -> List[Dict]:
        """加载加油站数据"""
        if not self.conn:
            self.connect()

        try:
            # 根据县别过滤数据
            if county_filter == "wannian":
                # 万年县加油站数据
                query = """
                    SELECT station_name, address, has_ev_charger,
                           total_sales, oil_revenue, longitude, latitude
                    FROM gas_stations
                    WHERE county = '万年县'
                """
                df = pd.read_sql(query, self.conn)
            elif county_filter == "yiyang":
                # 弋阳县加油站数据
                query = """
                    SELECT station_name, address, has_ev_charger,
                           total_sales, oil_revenue, longitude, latitude
                    FROM gas_stations
                    WHERE county = '弋阳县'
                """
                df = pd.read_sql(query, self.conn)
            else:
                # 联合视图：加载弋阳县和万年县的所有数据
                query = """
                    SELECT station_name, address, has_ev_charger,
                           total_sales, oil_revenue, longitude, latitude, county
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

                # 判断是否有EV充电设施
                has_ev = False
                if "has_ev_charger" in row:
                    has_ev = row["has_ev_charger"] in ("√", "✓", "是", "有")

                stations.append({
                    "name": row["station_name"],
                    "addr": row["address"] or "",
                    "has_ev": has_ev,
                    "sales": float(row["total_sales"]) if pd.notna(row["total_sales"]) else 0,
                    "revenue": float(row["oil_revenue"]) if pd.notna(row["oil_revenue"]) else 0,
                    "lng": lng,
                    "lat": lat,
                })

            logger.info(f"✓ 加载加油站：{len(stations)} 座")
            return stations

        except Exception as e:
            logger.error(f"✗ 加载加油站失败：{e}")
            return []

    def load_planned_stations(self, county_filter: Optional[str] = None) -> List[Dict]:
        """
        加载规划充电站数据

        Args:
            county_filter: 可选的县过滤条件（'弋阳' 或 '万年'）
        """
        if not self.conn:
            self.connect()

        try:
            # 注意：当前数据库表中没有 county 字段，所有数据都视为弋阳县数据
            # 未来添加万年县数据时需要添加 county 字段
            query = """
                SELECT station_name, township, scene, quantity,
                       power_kw, year, equipment, longitude, latitude,
                       category, category_code, county
                FROM stations_planned
                WHERE station_name IS NOT NULL
            """
            
            # 增加对 county 字段过滤的支持，确保联合视图与单县统计拆分准确
            if county_filter:
                # 处理 "弋阳" 匹配 "弋阳县"，"万年" 匹配 "万年县"
                if county_filter == "弋阳":
                    query += " AND (county = ? OR county LIKE ?)"
                    df = pd.read_sql(query, self.conn, params=("弋阳县", "弋阳"))
                elif county_filter == "万年":
                    query += " AND (county = ? OR county LIKE ?)"
                    df = pd.read_sql(query, self.conn, params=("万年县", "万年"))
                else:
                    query += " AND (county = ?)"
                    df = pd.read_sql(query, self.conn, params=(county_filter,))
            else:
                df = pd.read_sql(query, self.conn)

            stations = []
            for _, row in df.iterrows():
                try:
                    qty = int(row["quantity"]) if pd.notna(row["quantity"]) else 0
                    power = int(row["power_kw"]) if pd.notna(row["power_kw"]) else 0
                    year = int(row["year"]) if pd.notna(row["year"]) else None
                except (ValueError, TypeError):
                    qty = 0
                    power = 0
                    year = None

                try:
                    lng = float(row["longitude"]) if pd.notna(row["longitude"]) else None
                    lat = float(row["latitude"]) if pd.notna(row["latitude"]) else None
                except:
                    lng, lat = None, None

                stations.append({
                    "name": row["station_name"],
                    "township": row["township"] if pd.notna(row["township"]) else "",
                    "scene": row["scene"] if pd.notna(row["scene"]) else "",
                    "category": row["category"] if pd.notna(row["category"]) else "",
                    "category_code": int(row["category_code"]) if pd.notna(row["category_code"]) else 1,
                    "qty": qty,
                    "power": power,
                    "year": year,
                    "equip": row["equipment"] if pd.notna(row["equipment"]) else "",
                    "lng": lng,
                    "lat": lat,
                    "county": row["county"] if "county" in row and pd.notna(row["county"]) else "弋阳",
                })

            logger.info(f"✓ 加载规划充电站：{len(stations)} 站")
            return stations

        except Exception as e:
            logger.error(f"✗ 加载规划充电站失败：{e}")
            return []

    def load_economic_stats(self, region: str = "弋阳") -> pd.DataFrame:
        """加载经济统计数据"""
        if not self.conn:
            self.connect()

        try:
            query = """
                SELECT region, year, car_total, car_new, nev_total,
                       nev_new, nev_rate, gdp, fiscal_rev, population
                FROM economic_stats
                WHERE region = ?
                ORDER BY year
            """
            df = pd.read_sql(query, self.conn, params=(region,))
            logger.info(f"✓ 加载经济统计数据：{len(df)} 条记录 ({region})")
            return df

        except Exception as e:
            logger.error(f"✗ 加载经济统计数据失败：{e}")
            return pd.DataFrame()

    def load_all_data(self, county_filter: Optional[str] = None) -> Dict:
        """加载所有数据"""
        self.connect()

        data = {
            "urban_stations": self.load_urban_stations(),
            "gas_stations": self.load_gas_stations(),
            "planned_stations": self.load_planned_stations(county_filter),
            "economic_stats": self.load_economic_stats(county_filter) if county_filter else self.load_economic_stats(),
        }

        self.close()

        logger.info("✓ 所有数据加载完成")
        return data

    def get_statistics(self, county_filter: Optional[str] = None) -> Dict:
        """获取统计摘要"""
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

            # 规划充电站统计（支持按县过滤）
            if county_filter:
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(quantity), 0), COALESCE(SUM(power_kw), 0) 
                    FROM stations_planned 
                    WHERE county = ?
                """, (county_filter,))
            else:
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(quantity), 0), COALESCE(SUM(power_kw), 0) FROM stations_planned")
            
            result = cursor.fetchone()
            stats["planned_stations_count"] = result[0]
            stats["planned_piles_total"] = result[1]
            stats["planned_power_total"] = result[2]

            # 最新经济数据（支持按县查询）
            region = "弋阳" if not county_filter else county_filter
            cursor.execute("""
                SELECT year, nev_total, car_total, gdp, population
                FROM economic_stats
                WHERE region = ?
                ORDER BY year DESC
                LIMIT 1
            """, (region,))
            result = cursor.fetchone()
            if result:
                stats["latest_year"] = result[0]
                stats["nev_total"] = result[1]
                stats["car_total"] = result[2]
                stats["gdp"] = result[3]
                stats["population"] = result[4]

            logger.info(f"✓ 统计数据获取完成 ({county_filter or '全部'})")
            return stats

        except Exception as e:
            logger.error(f"✗ 获取统计数据失败：{e}")
            return {}

    def get_planned_stations_edit_list(self, county=None, year=None, township=None,
                                        keyword=None, limit=100, offset=0):
        """
        获取规划充电站编辑列表（支持分页和过滤）

        Args:
            county: 县过滤（'弋阳'/'万年'/'all'）
            year: 年份过滤（'all' 或具体年份）
            township: 乡镇过滤
            keyword: 关键词搜索（站名或场景）
            limit: 每页数量
            offset: 偏移量
        """
        if not self.conn:
            self.connect()

        try:
            # 基础查询
            base_query = """
                SELECT id, station_name, township, scene, quantity,
                       power_kw, year, equipment, longitude, latitude,
                       category, category_code, county
                FROM stations_planned
                WHERE 1=1
            """
            params = []

            # 县过滤
            if county and county != 'all':
                if county == 'yiyang':
                    base_query += " AND (county = ? OR county LIKE ?)"
                    params.extend(['弋阳县', '弋阳%'])
                elif county == 'wannian':
                    base_query += " AND (county = ? OR county LIKE ?)"
                    params.extend(['万年县', '万年%'])
                else:
                    base_query += " AND county = ?"
                    params.append(county)

            # 年份过滤
            if year and year != 'all':
                try:
                    year_val = int(year)
                    base_query += " AND year = ?"
                    params.append(year_val)
                except (ValueError, TypeError):
                    pass

            # 乡镇过滤
            if township:
                base_query += " AND township LIKE ?"
                params.append(f'%{township}%')

            # 关键词搜索（站名或场景）
            if keyword:
                base_query += " AND (station_name LIKE ? OR scene LIKE ?)"
                params.extend([f'%{keyword}%', f'%{keyword}%'])

            # 获取总数
            count_query = f"SELECT COUNT(*) FROM ({base_query}) AS t"
            cursor = self.conn.cursor()
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # 添加分页和排序
            base_query += " ORDER BY year DESC, id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            # 执行查询
            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            # 转换为字典列表
            items = []
            for row in rows:
                try:
                    qty = int(row[3]) if row[3] is not None else 0
                    power = int(row[4]) if row[4] is not None else 0
                    year_val = int(row[5]) if row[5] is not None else None
                except (ValueError, TypeError):
                    qty = 0
                    power = 0
                    year_val = None

                try:
                    lng = float(row[8]) if row[8] is not None else None
                    lat = float(row[9]) if row[9] is not None else None
                except:
                    lng, lat = None, None

                items.append({
                    "id": row[0],
                    "name": row[1] or "",
                    "township": row[2] or "",
                    "scene": row[3] or "",
                    "qty": qty,
                    "power": power,
                    "year": year_val,
                    "equip": row[6] or "",
                    "lng": lng,
                    "lat": lat,
                    "category": row[10] or "",
                    "category_code": int(row[11]) if row[11] is not None else 1,
                    "county": row[12] or "弋阳",
                })

            logger.info(f"✓ 获取规划站点编辑列表：{len(items)} 条 / 总计 {total} 条")
            return {
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(f"✗ 获取规划站点编辑列表失败：{e}")
            return {"items": [], "total": 0, "limit": limit, "offset": offset}


# 测试代码
if __name__ == "__main__":
    loader = DataLoader()

    # 测试加载所有数据
    data = loader.load_all_data()

    print("\n===== 数据加载测试 =====")
    print(f"城区充电站：{len(data['urban_stations'])} 座")
    print(f"加油站：{len(data['gas_stations'])} 座")
    print(f"规划充电站：{len(data['planned_stations'])} 站")
    print(f"经济数据：{len(data['economic_stats'])} 条记录")

    # 测试统计数据
    loader.connect()
    stats = loader.get_statistics()
    loader.close()

    print("\n===== 统计摘要 =====")
    for key, value in stats.items():
        print(f"{key}: {value}")
