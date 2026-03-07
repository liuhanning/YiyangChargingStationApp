"""
弋阳县充换电设施规划 - Flask 后端
"""
import json
import math
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from data_loader import DataLoader
from config import (
    DATABASE, MAP_API, COUNTY_INFO, STYLE_CONFIG,
    DISPLAY_MODES, STATS_CONFIG, DATA_DIR, TOWNSHIP_LABELS
)

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)


def clean_nan(obj):
    """递归清理 NaN/Infinity 为 None，避免 JSON 序列化问题"""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    return obj

# 单例数据加载器
_loader = None

def get_loader():
    global _loader
    if _loader is None:
        _loader = DataLoader()
        _loader.connect()
    return _loader


# ===== 页面路由 =====

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

@app.route("/dashboard.html")
def dashboard():
    return send_from_directory(".", "dashboard.html")


# ===== API 路由 =====

@app.route("/api/config")
def api_config():
    """返回前端所需的配置信息"""
    return jsonify({
        "tianditu_key": MAP_API["tianditu"]["key"],
        "center": COUNTY_INFO["center"],
        "county_name": COUNTY_INFO["name"],
        "styles": STYLE_CONFIG,
        "modes": DISPLAY_MODES,
        "township_labels": TOWNSHIP_LABELS,
    })


@app.route("/api/boundary")
def api_boundary():
    """返回县域边界坐标（优先使用DataV精确边界，回退为手工坐标）"""
    # 优先读取DataV的精确GeoJSON边界 (790个点)
    geojson_file = DATA_DIR / "yiyang_county.geojson"
    if geojson_file.exists():
        try:
            with open(geojson_file, "r", encoding="utf-8") as f:
                geojson = json.load(f)
            # 提取坐标组
            coords = geojson["features"][0]["geometry"]["coordinates"][0][0]
            props = geojson["features"][0]["properties"]
            return jsonify({
                "boundary": coords,
                "count": len(coords),
                "source": "DataV GeoAtlas",
                "center": props.get("center"),
                "name": props.get("name"),
                "geojson": geojson,
            })
        except Exception as e:
            pass  # 回退到旧数据

    # 回退：读取手工的边界文件 (109个点)
    boundary_file = DATA_DIR / "yiyang_boundary.json"
    try:
        with open(boundary_file, "r", encoding="utf-8") as f:
            boundary = json.load(f)
        return jsonify({"boundary": boundary, "count": len(boundary), "source": "manual"})
    except Exception:
        return jsonify({"boundary": [], "count": 0, "error": "边界数据加载失败"}), 500


@app.route("/api/boundary/townships")
def api_township_boundaries():
    """返回乡镇边界 GeoJSON（来自 Shapefile 转换）"""
    geojson_file = DATA_DIR / "yiyang_townships.geojson"
    try:
        with open(geojson_file, "r", encoding="utf-8") as f:
            geojson = json.load(f)
        count = len(geojson.get("features", []))
        # 提取乡镇名称和中心点列表
        townships = []
        for feat in geojson.get("features", []):
            props = feat.get("properties", {})
            name = props.get("DistName") or props.get("NAME") or props.get("name", "")
            # 计算中心点（简化版：用第一个坐标组的平均值）
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [])
            if geom.get("type") == "MultiPolygon" and coords:
                ring = coords[0][0]
            elif geom.get("type") == "Polygon" and coords:
                ring = coords[0]
            else:
                ring = []
            if ring:
                clng = sum(p[0] for p in ring) / len(ring)
                clat = sum(p[1] for p in ring) / len(ring)
            else:
                clng, clat = 0, 0
            townships.append({"name": name, "lng": round(clng, 4), "lat": round(clat, 4)})
        return jsonify({
            "geojson": geojson,
            "count": count,
            "townships": townships,
            "source": "Shapefile",
        })
    except Exception as e:
        return jsonify({"error": f"乡镇边界数据加载失败: {e}", "count": 0}), 500


@app.route("/api/stations/urban")
def api_urban_stations():
    """现有充电站"""
    loader = get_loader()
    stations = clean_nan(loader.load_urban_stations())
    return jsonify({"stations": stations, "count": len(stations)})


@app.route("/api/stations/gas")
def api_gas_stations():
    """加油站"""
    loader = get_loader()
    stations = clean_nan(loader.load_gas_stations())
    return jsonify({"stations": stations, "count": len(stations)})


@app.route("/api/stations/planned")
def api_planned_stations():
    """规划充电站"""
    loader = get_loader()
    stations = clean_nan(loader.load_planned_stations())
    return jsonify({"stations": stations, "count": len(stations)})


@app.route("/api/stats")
def api_stats():
    """统计摘要"""
    loader = get_loader()
    stats = clean_nan(loader.get_statistics())
    return jsonify(stats)


@app.route("/api/economic")
def api_economic():
    """经济数据"""
    loader = get_loader()
    df = loader.load_economic_stats()
    if df is not None and not df.empty:
        records = clean_nan(df.to_dict(orient="records"))
        return jsonify({"data": records, "count": len(records)})
    return jsonify({"data": [], "count": 0})


@app.route("/api/townships")
def api_townships():
    """返回乡镇标注数据"""
    return jsonify({"townships": TOWNSHIP_LABELS, "count": len(TOWNSHIP_LABELS)})


if __name__ == "__main__":
    print("=" * 50)
    print("  弋阳县充换电设施规划系统（动态版）")
    print("  http://localhost:5000")
    print("  API: /api/config, /api/boundary, /api/stations/urban")
    print("       /api/stations/gas, /api/stations/planned")
    print("       /api/stats, /api/economic, /api/townships")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
