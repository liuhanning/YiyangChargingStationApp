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


# ===== 地图 API 配置 =====
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

    # 基本情况（2025 年）
    "stats": {
        "gdp": 203.94,  # 亿元
        "population": 32.94,  # 万人
        "car_total": 5.986,  # 万辆
        "nev_total": 0.3225,  # 万辆
        "nev_rate": 5.39,  # %
    }
}

# ===== 万年县基本信息 =====
COUNTY_INFO_WANNIAN = {
    "name": "万年县",
    "province": "江西省",
    "city": "上饶市",
    "center": [117.07, 28.69],  # 县城中心坐标
    "adcode": "361129",  # 行政区划代码

    # 基本情况（待补充）
    "stats": {
        "gdp": None,  # 待补充
        "population": None,
        "car_total": None,
        "nev_total": None,
        "nev_rate": None,
    }
}

# ===== 县基本信息统一管理字典 =====
# 格式：{"县 key": COUNTY_INFO_XXX}
ALL_COUNTY_INFO = {
    "yiyang": COUNTY_INFO,
    "wannian": COUNTY_INFO_WANNIAN,
    # 新增县时在此添加：
    # "jian": COUNTY_INFO_JIAN,
    # "suichuan": COUNTY_INFO_SUICHUAN,
    # "xianxian": COUNTY_INFO_XXIAN,
}

# ===== 新增县配置模板 =====
# 复制以下模板配置新县：
"""
# ===== XX 县基本信息 =====
COUNTY_INFO_XXIAN = {
    "name": "XX 县",
    "province": "XX 省",
    "city": "XX 市",
    "center": [经度，纬度],  # 县城中心坐标
    "adcode": "XXXXXX",  # 行政区划代码

    # 基本情况
    "stats": {
        "gdp": None,  # 亿元
        "population": None,  # 万人
        "car_total": None,  # 万辆
        "nev_total": None,  # 万辆
        "nev_rate": None,  # %
    }
}

# 然后在 ALL_COUNTY_INFO 中添加：
# "xianxian": COUNTY_INFO_XXIAN,
"""

# ===== 支持的多县列表 =====
SUPPORTED_COUNTIES = [
    {"name": "弋阳县", "adcode": "361126", "center": [117.44, 28.37],  "key": "yiyang"},
    {"name": "万年县", "adcode": "361129", "center": [117.07, 28.69],  "key": "wannian"},
    {"name": "吉安县", "adcode": "360821", "center": [114.905, 27.040], "key": "jian"},
    {"name": "遂川县", "adcode": "360827", "center": [114.517, 26.324], "key": "suichuan"},
    # 新增县配置模板（复制此行修改）：
    # {"name": "XX 县", "adcode": "XXXXXX", "center": [经度，纬度], "key": "xianxian"},
]


# ===== 县域边界默认坐标 =====
# 如果 API 获取失败，使用此默认边界
COUNTY_BOUNDARY_DEFAULT = [
    [117.25, 28.25], [117.25, 28.50], [117.60, 28.50],
    [117.60, 28.25], [117.25, 28.25]
]


# ===== 视觉样式配置（政务规划风格 - 参考 demo.png）=====
STYLE_CONFIG = {
    # 县域边界样式 - 亮紫色行政边界
    "county_boundary": {
        "stroke_color": "#9333EA",  # 亮紫色，突出行政边界
        "stroke_width": 3,
        "fill_color": "rgba(0,0,0,0)",
        "fill_opacity": 0.0,
    },

    # 聚光灯遮罩样式 - 更浅的灰色，保持底图清晰
    "spotlight_mask": {
        "fill_color": "#6b7280",
        "fill_opacity": 0.25,
    },

    # 现有充电站样式 - 红色圆点（政务规划风格）
    "station_existing": {
        "color": "#DC2626",  # 正红色，醒目
        "icon": "circle",     # 简洁圆点，非 emoji
        "size": 10,
        "label": "现状充电站",
    },

    # 加油站样式 - 橙色圆点
    "gas_station": {
        "color": "#EA580C",
        "icon": "circle",
        "size": 9,
        "label": "加油站",
    },

    # 规划充电站样式 - 蓝色圆点
    "station_planned": {
        "color": "#2563EB",  # 深蓝色
        "icon": "circle",
        "size": 10,
        "label": "规划充电站",
    },

    # 新增：现有车站 5km 服务半径
    "radius_existing": {
        "color": "#DC2626",
        "weight": 1,
        "opacity": 0.4,
        "fill_color": "#DC2626",
        "fill_opacity": 0.10,
        "label": "5 公里服务圈 (现状)",
    },

    # 新增：规划车站 5km 服务半径
    "radius_planned": {
        "color": "#2563EB",
        "weight": 1,
        "opacity": 0.4,
        "fill_color": "#2563EB",
        "fill_opacity": 0.10,
        "dashArray": "5, 5",
        "label": "5 公里服务圈 (规划)",
    },

    # 标注样式 - 黑体，更正式
    "label": {
        "fontsize": 12,
        "color": "#1f2937",  # 深灰色，更正式
        "background": "rgba(255,255,255,0.8)",
        "border": "#d1d5db",
    },
}

# ===== 乡镇标注坐标 =====
# 弋阳县乡镇标注
TOWNSHIP_LABELS = [
    {"name": "桃源街道", "lng": 117.4467, "lat": 28.4155},
    {"name": "曹溪镇", "lng": 117.3075, "lat": 28.7059},
    {"name": "漆工镇", "lng": 117.5261, "lat": 28.6111},
    {"name": "樟树墩镇", "lng": 117.4530, "lat": 28.5455},
    {"name": "南岩镇", "lng": 117.4436, "lat": 28.3419},
    {"name": "朱坑镇", "lng": 117.5150, "lat": 28.3881},
    {"name": "圭峰镇", "lng": 117.3426, "lat": 28.2819},
    {"name": "叠山镇", "lng": 117.4468, "lat": 28.1871},
    {"name": "港口镇", "lng": 117.3459, "lat": 28.1826},
    {"name": "弋江镇", "lng": 117.4165, "lat": 28.4047},
    {"name": "中畈乡", "lng": 117.3490, "lat": 28.5554},
    {"name": "葛溪乡", "lng": 117.4628, "lat": 28.4782},
    {"name": "湾里乡", "lng": 117.3825, "lat": 28.4555},
    {"name": "清湖乡", "lng": 117.3489, "lat": 28.3887},
    {"name": "旭光乡", "lng": 117.4378, "lat": 28.1933},
    {"name": "花亭乡", "lng": 117.4229, "lat": 28.4349},
    {"name": "三县岭乡", "lng": 117.3636, "lat": 28.6510},
]

# ===== 其他县乡镇标注配置 =====
# 万年县乡镇标注
TOWNSHIP_LABELS_WANNIAN = [
    {"name": "陈营镇", "lng": 117.0794, "lat": 28.7081},
    {"name": "石镇镇", "lng": 116.9691, "lat": 28.8016},
    {"name": "梓埠镇", "lng": 116.8857, "lat": 28.8396},
    {"name": "裴梅镇", "lng": 117.1582, "lat": 28.6286},
    {"name": "青云镇", "lng": 116.9248, "lat": 28.6484},
    {"name": "汪家乡", "lng": 116.9660, "lat": 28.7300},
    {"name": "湖云乡", "lng": 116.8448, "lat": 28.7801},
    {"name": "齐埠乡", "lng": 116.8687, "lat": 28.6933},
    {"name": "苏桥乡", "lng": 116.9597, "lat": 28.5686},
    {"name": "大源镇", "lng": 117.1815, "lat": 28.7261},
    {"name": "上坊乡", "lng": 117.0249, "lat": 28.6444},
    {"name": "珠田乡", "lng": 117.0787, "lat": 28.7756},
]

# 吉安县乡镇标注（示例，需补充实际数据）
TOWNSHIP_LABELS_JIAN = [
    # {"name": "XX 镇", "lng": 114.XX, "lat": 27.XX},
]

# 遂川县乡镇标注（示例，需补充实际数据）
TOWNSHIP_LABELS_SUICHUAN = [
    # {"name": "XX 镇", "lng": 114.XX, "lat": 26.XX},
]

# ===== 乡镇标注统一管理字典 =====
# 格式：{"县 key": TOWNSHIP_LABELS_XXX}
ALL_TOWNSHIP_LABELS = {
    "yiyang": TOWNSHIP_LABELS,
    "wannian": TOWNSHIP_LABELS_WANNIAN,
    "jian": TOWNSHIP_LABELS_JIAN,
    "suichuan": TOWNSHIP_LABELS_SUICHUAN,
    # 新增县时在此添加：
    # "xianxian": TOWNSHIP_LABELS_XXIAN,
}


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


# ===== 地图配准配置（控制点校准）=====
# 控制点（GCP - Ground Control Points）：[(底图x, 底图y, 经度, 纬度), ...]
# 用于精确配准底图和地图坐标
MAP_CALIBRATION = {
    "yiyang": {
        "gcps": [
            (1650, 2000, 117.4165, 28.4047),  # 弋江镇
            (1000, 300, 117.3075, 28.7059),  # 曹溪镇
            (2300, 2100, 117.515, 28.3881),  # 朱坑镇
        ],
        "transform_type": "affine",  # 变换类型：affine 或 poly
        "enabled": True,  # 启用控制点配准
    },
    "wannian": {
        "gcps": [
            (1843, 1033, 117.0794, 28.7081),  # 陈营镇
            (1439, 556, 116.9691, 28.8016),   # 石镇镇
            (2174, 1472, 117.1582, 28.6286),  # 裴梅镇
            (1301, 1700, 117.1815, 28.7261),  # 大源镇
            (1301, 1697, 116.9597, 28.5686),  # 苏桥乡
        ],
        "transform_type": "affine",
        "enabled": True,
    }
}

# ===== 显示模式配置 =====
DISPLAY_MODES = {
    "standard": {
        "name": "标准视图",
        "icon": "🗺️",
        "layers": ["boundary"],  # 只显示县域边界和乡镇边界
    },
    "all": {
        "name": "全部显示",
        "icon": "🗺️",
        "layers": ["urban", "gas", "plan", "boundary"],
    },
    "boundary": {
        "name": "仅县域边界",
        "icon": "📍",
        "layers": ["boundary"],
    },
    "current": {
        "name": "现状分析",
        "icon": "⚡",
        "layers": ["urban", "boundary"],
    },
    "planning": {
        "name": "规划视图",
        "icon": "🔋",
        "layers": ["plan", "boundary"],
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
