"""
配置文件
存储项目全局配置、数据路径、样式参数等
"""
from pathlib import Path

# ===== 项目路径配置 =====
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
DB_DIR = BASE_DIR / "db"

# 数据子目录
RAW_DATA_DIR = Path(r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳县充换电申报材料\充换电申报材料\data")
DOCS_DIR = BASE_DIR / "docs"

# 确保目录存在
for dir_path in [DATA_DIR, OUTPUT_DIR, DB_DIR, DOCS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


# ===== 数据库配置 =====
DATABASE = {
    "path": DB_DIR / "yiyang_ev.db",
    "encoding": "utf-8",
}


# ===== 地图API配置 =====
MAP_API = {
    "tianditu": {
        "key": "36c2c7b1a00180d86e97fa8ca2cd3bf2",
        "version": "4.0",
    },
    "amap": {
        "key": "63012397200899138fc66edc8f54a72a",  # 已废弃
        "version": "2.0",
    }
}


# ===== 坐标系配置 =====
CRS_CODE = "EPSG:4326"  # WGS84 / GCJ-02 (火星坐标系)


# ===== 弋阳县基本信息 =====
COUNTY_INFO = {
    "name": "弋阳县",
    "province": "江西省",
    "city": "上饶市",
    "center": [117.44, 28.37],  # 县城中心坐标
    "adcode": "361126",  # 行政区划代码

    # 基本情况（2025年）
    "stats": {
        "gdp": 203.94,  # 亿元
        "population": 32.94,  # 万人
        "car_total": 5.986,  # 万辆
        "nev_total": 0.3225,  # 万辆
        "nev_rate": 5.39,  # %
    }
}


# ===== 县域边界默认坐标 =====
# 如果API获取失败，使用此默认边界
COUNTY_BOUNDARY_DEFAULT = [
    [117.25, 28.25], [117.25, 28.50], [117.60, 28.50],
    [117.60, 28.25], [117.25, 28.25]
]


# ===== 视觉样式配置（浅色主题 - 参考001截图风格）=====
STYLE_CONFIG = {
    # 县域边界样式 - 专业规划蓝边界
    "county_boundary": {
        "stroke_color": "#1E88E5",  # 从红色 #cc3333 改为专业蓝色
        "stroke_width": 3,
        "fill_color": "#fffff0",
        "fill_opacity": 0.45,
    },

    # 聚光灯遮罩样式 - 柔和灰色
    "spotlight_mask": {
        "fill_color": "#8a8a8a",
        "fill_opacity": 0.35,
    },

    # 现有充电站样式
    "station_existing": {
        "color": "#2ecc40",
        "icon": "⚡",
        "size": 24,
        "label": "现有充电站",
    },

    # 加油站样式
    "gas_station": {
        "color": "#e67e22",
        "icon": "⛽",
        "size": 22,
        "label": "加油站",
    },

    # 规划充电站样式
    "station_planned": {
        "color": "#3498db",
        "icon": "🔋",
        "size": 22,
        "label": "规划充电站",
    },

    # 新增：现有车站5km服务半径
    "radius_existing": {
        "color": "#2ecc40",
        "weight": 1,
        "opacity": 0.5,
        "fill_color": "#2ecc40",
        "fill_opacity": 0.15,
        "label": "5公里服务圈(现有)",
    },

    # 新增：规划车站5km服务半径
    "radius_planned": {
        "color": "#3498db",
        "weight": 1,
        "opacity": 0.5,
        "fill_color": "#3498db",
        "fill_opacity": 0.15,
        "dashArray": "5, 5",
        "label": "5公里服务圈(规划)",
    },

    # 标注样式
    "label": {
        "fontsize": 13,
        "color": "#1a3a5c",
        "background": "transparent",
        "border": "transparent",
    },
}

# ===== 乡镇标注坐标 =====
TOWNSHIP_LABELS = [
    {"name": "弋江镇", "lng": 117.434, "lat": 28.402},
    {"name": "南岩镇", "lng": 117.455, "lat": 28.370},
    {"name": "桃源街道", "lng": 117.458, "lat": 28.420},
    {"name": "花亭乡", "lng": 117.395, "lat": 28.447},
    {"name": "圭峰镇", "lng": 117.405, "lat": 28.310},
    {"name": "叠山镇", "lng": 117.335, "lat": 28.360},
    {"name": "漆工镇", "lng": 117.350, "lat": 28.460},
    {"name": "湾里乡", "lng": 117.503, "lat": 28.490},
    {"name": "葛溪乡", "lng": 117.540, "lat": 28.560},
    {"name": "中畈乡", "lng": 117.490, "lat": 28.215},
    {"name": "港口镇", "lng": 117.310, "lat": 28.290},
    {"name": "清湖乡", "lng": 117.538, "lat": 28.430},
    {"name": "旭光乡", "lng": 117.310, "lat": 28.530},
    {"name": "樟树墩镇", "lng": 117.290, "lat": 28.615},
    {"name": "曹溪镇", "lng": 117.460, "lat": 28.155},
    {"name": "三县岭镇", "lng": 117.555, "lat": 28.660},
]


# ===== 地图导出配置 =====
EXPORT_CONFIG = {
    "html": {
        "enabled": True,
        "filename": "map.html",
        "title": "弋阳县充换电设施规划地图",
    },
    "dashboard": {
        "enabled": True,
        "filename": "dashboard.html",
        "title": "弋阳县充换电设施数据仪表盘",
    }
}


# ===== 显示模式配置 =====
DISPLAY_MODES = {
    "all": {
        "name": "全部显示",
        "icon": "🗺️",
        "layers": ["urban", "gas", "plan", "boundary", "radius_existing", "radius_planned"],
    },
    "boundary": {
        "name": "仅县域边界",
        "icon": "📍",
        "layers": ["boundary"],
    },
    "current": {
        "name": "现状分析",
        "icon": "⚡",
        "layers": ["urban", "boundary", "radius_existing"],
    },
    "planning": {
        "name": "规划视图",
        "icon": "🔋",
        "layers": ["plan", "boundary", "radius_planned"],
    },
    "gas": {
        "name": "加油站分布",
        "icon": "⛽",
        "layers": ["gas", "boundary"],
    },
}


# ===== 数据统计配置 =====
STATS_CONFIG = {
    "existing_stations": 16,  # 现有充电站数量
    "gas_stations": 26,  # 加油站数量
    "planned_stations": 34,  # 规划充电站数量
    "planned_year": 2026,  # 规划年度
}


# ===== 日志配置 =====
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
}
