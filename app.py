"""
弋阳县/万年县充换电设施规划 - Flask 后端
支持两县联合申报
"""
import json
import math
import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request, send_file
from flask_cors import CORS
from data_loader import DataLoader
from config import (
    DATABASE, MAP_API, COUNTY_INFO, COUNTY_INFO_WANNIAN, 
    SUPPORTED_COUNTIES, STYLE_CONFIG, DISPLAY_MODES, 
    STATS_CONFIG, DATA_DIR, TOWNSHIP_LABELS
)

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

BASE_PATH = os.getenv("BASE_PATH", "/charging").strip()
if BASE_PATH == "/":
    BASE_PATH = ""
if BASE_PATH and not BASE_PATH.startswith("/"):
    BASE_PATH = "/" + BASE_PATH
if BASE_PATH.endswith("/"):
    BASE_PATH = BASE_PATH.rstrip("/")


def with_base(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{BASE_PATH}{path}" if BASE_PATH else path


def route(rule: str, **options):
    def decorator(func):
        app.route(rule, **options)(func)
        if BASE_PATH:
            pref_rule = f"{BASE_PATH}/" if rule == "/" else f"{BASE_PATH}{rule}"
            pref_options = dict(options)
            endpoint = pref_options.pop("endpoint", func.__name__)
            app.add_url_rule(pref_rule, endpoint=f"{endpoint}__prefixed", view_func=func, **pref_options)
        return func
    return decorator


def clean_nan(obj):
    """递归清理 NaN/Infinity 为 None，避免 JSON 序列化问题"""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    return obj


def get_loader(county: str = "yiyang"):
    """获取数据加载器"""
    return DataLoader(DATABASE["path"], county)


# ===== 页面路由 =====

@route("/")
def index():
    return send_from_directory("frontend", "index.html")

@route("/dashboard.html")
def dashboard():
    return send_from_directory(".", "dashboard.html")

@route("/calibration")
def calibration():
    return send_from_directory("frontend", "calibration.html")

@route("/geocode_tool")
def geocode_tool():
    return send_from_directory("frontend", "geocode_tool.html")


# ===== API 路由 =====

@route("/api/config")
def api_config():
    """返回前端所需的配置信息"""
    return jsonify({
        "tianditu_key": MAP_API["tianditu"]["key"],
        "center": COUNTY_INFO["center"],
        "county_name": COUNTY_INFO["name"],
        "styles": STYLE_CONFIG,
        "modes": DISPLAY_MODES,
        "township_labels": TOWNSHIP_LABELS,
        "supported_counties": SUPPORTED_COUNTIES,
    })


@route("/api/boundary")
def api_boundary():
    """
    返回县域边界坐标
    支持参数：county=yiyang 或 county=wannian
    """
    county = request.args.get("county", "yiyang")
    
    if county == "wannian":
        # 万年县边界
        geojson_file = DATA_DIR / "wannian_county.geojson"
        if geojson_file.exists():
            try:
                with open(geojson_file, "r", encoding="utf-8") as f:
                    geojson = json.load(f)
                geom = geojson["features"][0]["geometry"]
                
                # 处理 MultiPolygon：合并所有多边形的外环
                if geom["type"] == "MultiPolygon":
                    all_coords = []
                    for polygon in geom["coordinates"]:
                        # 每个 polygon[0] 是外环
                        outer_ring = polygon[0]
                        all_coords.extend(outer_ring)
                    coords = all_coords
                elif geom["type"] == "Polygon":
                    coords = geom["coordinates"][0]  # 外层环
                else:
                    coords = []
                    
                props = geojson["features"][0]["properties"]
                return jsonify({
                    "boundary": coords,
                    "count": len(coords),
                    "source": "GeoJSON",
                    "center": props.get("center"),
                    "name": props.get("name"),
                    "geojson": geojson,
                    "county": "wannian",
                })
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"万年县边界加载失败：{e}")
                pass
        
        # 回退到简化版
        boundary_file = DATA_DIR / "wannian_boundary.json"
        if boundary_file.exists():
            try:
                with open(boundary_file, "r", encoding="utf-8") as f:
                    boundary = json.load(f)
                return jsonify({
                    "boundary": boundary, 
                    "count": len(boundary), 
                    "source": "manual",
                    "county": "wannian",
                })
            except Exception:
                pass
        
        return jsonify({"boundary": [], "count": 0, "error": "万年县边界数据加载失败", "county": "wannian"}), 500
    
    else:
        # 弋阳县边界
        geojson_file = DATA_DIR / "yiyang_county.geojson"
        if geojson_file.exists():
            try:
                with open(geojson_file, "r", encoding="utf-8") as f:
                    geojson = json.load(f)
                coords = geojson["features"][0]["geometry"]["coordinates"][0][0]
                props = geojson["features"][0]["properties"]
                return jsonify({
                    "boundary": coords,
                    "count": len(coords),
                    "source": "DataV GeoAtlas",
                    "center": props.get("center"),
                    "name": props.get("name"),
                    "geojson": geojson,
                    "county": "yiyang",
                })
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"无法读取高精度边界 GeoJSON (弋阳县)：{e}，将尝试回退方案")
                pass

        boundary_file = DATA_DIR / "yiyang_boundary.json"
        try:
            with open(boundary_file, "r", encoding="utf-8") as f:
                boundary = json.load(f)
            return jsonify({"boundary": boundary, "count": len(boundary), "source": "manual", "county": "yiyang"})
        except Exception:
            return jsonify({"boundary": [], "count": 0, "error": "弋阳县边界数据加载失败", "county": "yiyang"}), 500


@route("/api/boundary/all")
def api_all_boundaries():
    """返回所有县的边界（用于联合展示）"""
    result = {}
    
    for county_info in SUPPORTED_COUNTIES:
        county_key = county_info["key"]
        geojson_file = DATA_DIR / f"{county_key}_county.geojson"
        
        if geojson_file.exists():
            try:
                with open(geojson_file, "r", encoding="utf-8") as f:
                    geojson = json.load(f)
                coords = geojson["features"][0]["geometry"]["coordinates"][0][0]
                result[county_key] = {
                    "boundary": coords,
                    "count": len(coords),
                    "center": geojson["features"][0]["properties"].get("center"),
                    "name": geojson["features"][0]["properties"].get("name"),
                }
            except Exception:
                result[county_key] = {"boundary": [], "count": 0, "error": "加载失败"}
        else:
            result[county_key] = {"boundary": [], "count": 0, "error": "文件不存在"}
    
    return jsonify(result)


@route("/api/boundary/townships")
def api_township_boundaries():
    """返回乡镇边界 GeoJSON（支持按县过滤）"""
    county = request.args.get("county", "yiyang")

    if county == "wannian":
        geojson_file = DATA_DIR / "wannian_townships.geojson"
    else:
        geojson_file = DATA_DIR / "yiyang_townships.geojson"

    try:
        with open(geojson_file, "r", encoding="utf-8") as f:
            geojson = json.load(f)
        count = len(geojson.get("features", []))
        townships = []
        for feat in geojson.get("features", []):
            props = feat.get("properties", {})
            name = props.get("DistName") or props.get("NAME") or props.get("name", "")
            geom = feat.get("geometry", {})
            
            # 处理 Point 类型（如南溪乡只有中心点）
            if geom.get("type") == "Point":
                coords = geom.get("coordinates", [])
                if coords and len(coords) >= 2:
                    townships.append({"name": name, "lng": round(coords[0], 4), "lat": round(coords[1], 4)})
                continue
            
            # 处理 Polygon/MultiPolygon 类型
            coords = geom.get("coordinates", [])
            if geom.get("type") == "MultiPolygon" and coords:
                ring = coords[0][0]
            elif geom.get("type") == "Polygon" and coords and len(coords) > 0 and len(coords[0]) > 0:
                ring = coords[0]
            else:
                ring = []
            
            if ring and len(ring) > 0:
                clng = sum(p[0] for p in ring) / len(ring)
                clat = sum(p[1] for p in ring) / len(ring)
                townships.append({"name": name, "lng": round(clng, 4), "lat": round(clat, 4)})
        
        return jsonify({
            "geojson": geojson,
            "count": count,
            "townships": townships,
            "source": "Shapefile",
            "county": county,
        })
    except Exception as e:
        return jsonify({"error": f"乡镇边界数据加载失败：{e}", "count": 0, "county": county}), 500


@route("/api/stations/urban")
def api_urban_stations():
    """现有充电站（支持县别过滤）"""
    county = request.args.get("county", "yiyang")
    
    loader = get_loader()
    stations = clean_nan(loader.load_urban_stations(county_filter=county))
    return jsonify({"stations": stations, "count": len(stations), "county": county})


@route("/api/stations/gas")
def api_gas_stations():
    """加油站（支持县别过滤）"""
    county = request.args.get("county", "yiyang")
    
    loader = get_loader()
    stations = clean_nan(loader.load_gas_stations(county_filter=county))
    return jsonify({"stations": stations, "count": len(stations), "county": county})


@route("/api/stations/planned")
def api_planned_stations():
    """
    规划充电站
    支持参数：county=yiyang 或 county=wannian 或 county=all
    """
    county = request.args.get("county", "yiyang")

    if county == "wannian":
        # 万年县暂无数据
        return jsonify({"stations": [], "count": 0, "county": "wannian", "note": "数据收集中"})

    loader = get_loader()

    # 区分单县还是联合视图 (all)
    filter_val = None if county == "all" else "弋阳" if county == "yiyang" else county

    stations = loader.load_planned_stations(county_filter=filter_val)
    stations = clean_nan(stations)
    return jsonify({"stations": stations, "count": len(stations), "county": county})


@route("/api/stations/planned/edit-list")
def api_planned_stations_edit_list():
    """
    规划充电站编辑列表（支持分页和过滤）
    支持参数：
        - county: 县（yiyang/wannian/all）
        - year: 年份（all 或具体年份）
        - township: 乡镇
        - keyword: 关键词
        - limit: 每页数量 (默认 100)
        - offset: 偏移量
    """
    county = request.args.get("county", "yiyang")
    year = request.args.get("year", "all")
    township = request.args.get("township", "")
    keyword = request.args.get("keyword", "")

    try:
        limit = int(request.args.get("limit", "100"))
    except (ValueError, TypeError):
        limit = 100

    try:
        offset = int(request.args.get("offset", "0"))
    except (ValueError, TypeError):
        offset = 0

    # 限制最大返回数量
    if limit > 300:
        limit = 300
    if limit < 1:
        limit = 100

    loader = get_loader()
    result = loader.get_planned_stations_edit_list(
        county=county,
        year=year,
        township=township,
        keyword=keyword,
        limit=limit,
        offset=offset
    )
    result = clean_nan(result)
    return jsonify(result)


@route("/api/stations/planned/batch-update", methods=["POST"])
def api_planned_stations_batch_update():
    """
    批量更新规划充电站数据
    请求体：
    {
        "county": "yiyang",
        "updates": [
            {"id": 1, "fields": {"name": "新站名", "qty": 10, ...}},
            ...
        ]
    }
    """
    import shutil
    from datetime import datetime

    try:
        data = request.json
        if not data:
            return jsonify({"error": "请求体为空", "success": False}), 400

        updates = data.get("updates", [])
        county = data.get("county", "yiyang")

        if not updates:
            return jsonify({"error": "更新数据为空", "success": False}), 400

        # 备份数据库
        db_path = DATABASE["path"]
        backup_path = str(db_path) + ".bak." + datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            shutil.copy2(str(db_path), backup_path)
            backup_file = Path(backup_path).name
        except Exception as e:
            logger.warning(f"数据库备份失败：{e}")
            backup_file = None

        # 批量更新
        if not loader.conn:
            loader.connect()

        updated_count = 0
        failed_count = 0
        errors = []

        cursor = loader.conn.cursor()

        for update in updates:
            try:
                station_id = update.get("id")
                fields = update.get("fields", {})

                if not station_id:
                    failed_count += 1
                    errors.append({"id": None, "error": "缺少 ID"})
                    continue

                # 构建更新 SQL
                allowed_fields = {
                    "name": "station_name",
                    "township": "township",
                    "scene": "scene",
                    "qty": "quantity",
                    "power": "power_kw",
                    "year": "year",
                    "equip": "equipment",
                    "lng": "longitude",
                    "lat": "latitude",
                    "category": "category",
                    "category_code": "category_code",
                    "county": "county",
                }

                update_fields = []
                params = []

                for key, value in fields.items():
                    if key in allowed_fields:
                        update_fields.append(f"{allowed_fields[key]} = ?")
                        params.append(value)

                if not update_fields:
                    failed_count += 1
                    errors.append({"id": station_id, "error": "无有效字段"})
                    continue

                params.append(station_id)
                sql = f"UPDATE stations_planned SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(sql, params)

                if cursor.rowcount > 0:
                    updated_count += 1
                else:
                    failed_count += 1
                    errors.append({"id": station_id, "error": "未找到记录"})

            except Exception as e:
                failed_count += 1
                errors.append({"id": update.get("id"), "error": str(e)})
                logger.error(f"更新失败 ID={update.get('id')}: {e}")

        # 提交事务
        loader.conn.commit()

        return jsonify({
            "success": True,
            "updated_count": updated_count,
            "failed_count": failed_count,
            "errors": errors[:10],  # 最多返回 10 条错误
            "backup_file": backup_file,
        })

    except Exception as e:
        logger.error(f"批量更新失败：{e}")
        return jsonify({"error": str(e), "success": False}), 500


@route("/api/stats")
def api_stats():
    """
    统计摘要
    支持参数：county=yiyang 或 county=wannian 或 county=all
    """
    county = request.args.get("county", "yiyang")
    
    if county == "wannian":
        # 万年县暂无数据
        return jsonify({
            "county": "wannian",
            "existing_stations": 0,
            "gas_stations": 0,
            "planned_stations_count": 0,
            "planned_piles_total": 0,
            "planned_power_total": 0,
            "note": "数据收集中"
        })
    
    loader = get_loader()
    stats = loader.get_statistics()
    stats = clean_nan(stats)
    stats["county"] = county
    return jsonify(stats)


@route("/api/economic")
def api_economic():
    """
    经济数据
    支持参数：region=弋阳 或 region=万年
    """
    region = request.args.get("region", "弋阳")
    loader = get_loader()
    df = loader.load_economic_stats(region)
    if df is not None and not df.empty:
        records = clean_nan(df.to_dict(orient="records"))
        return jsonify({"data": records, "count": len(records), "region": region})
    return jsonify({"data": [], "count": 0, "region": region})


@route("/api/townships")
def api_townships():
    """返回乡镇标注数据"""
    county = request.args.get("county", "yiyang")
    
    # 根据县返回不同的乡镇标注
    if county == "wannian":
        # 万年县乡镇标注（修正后坐标）
        wannian_townships = [
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
        return jsonify({"townships": wannian_townships, "count": len(wannian_townships), "county": "wannian"})
    else:
        return jsonify({"townships": TOWNSHIP_LABELS, "count": len(TOWNSHIP_LABELS), "county": "yiyang"})


@route("/api/counties")
def api_counties():
    """返回支持的县列表"""
    return jsonify({"counties": SUPPORTED_COUNTIES})


@route("/api/generate-dynamic-map", methods=["POST"])
def api_generate_dynamic_map():
    """
    根据前端发送的点位数据生成动态规划图
    点位数据格式：[{"name": "名称", "lng": 经度, "lat": 纬度, "type": "类型"}]
    """
    from generate_dynamic_map import draw_dynamic_map

    try:
        data = request.json

        if not data or "points" not in data:
            return jsonify({"error": "缺少必要参数", "success": False}), 400

        points = data.get("points", [])
        county = data.get("county", "yiyang")

        if not points:
            return jsonify({"error": "点位数据不能为空", "success": False}), 400

        # 生成地图
        png_path, pdf_path = draw_dynamic_map(points, county)

        if not png_path:
            return jsonify({"error": "地图生成失败", "success": False}), 500

        return jsonify({
            "success": True,
            "message": f"成功生成包含 {len(points)} 个规划点的地图",
            "png_file": Path(png_path).name,
            "pdf_file": Path(pdf_path).name,
            "preview_url": with_base(f"/api/dynamic-map/{Path(png_path).name}"),
            "points_count": len(points)
        })

    except Exception as e:
        print(f"地图生成失败: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@route("/api/dynamic-map/<filename>")
def api_dynamic_map_file(filename):
    """获取动态生成的地图文件"""
    from generate_dynamic_map import OUTPUT_DIR

    file_path = OUTPUT_DIR / filename

    if not file_path.exists():
        return jsonify({"error": "文件不存在"}), 404

    return send_file(file_path)


@route("/api/dynamic-map-list")
def api_dynamic_map_list():
    """获取动态地图文件列表"""
    from generate_dynamic_map import OUTPUT_DIR

    files = []
    for f in OUTPUT_DIR.glob("*.png"):
        files.append({
            "filename": f.name,
            "size": f.stat().st_size,
            "created": f.stat().st_mtime,
            "url": with_base(f"/api/dynamic-map/{f.name}")
        })

    return jsonify({
        "files": sorted(files, key=lambda x: x["created"], reverse=True),
        "count": len(files)
    })


if __name__ == "__main__":
    run_host = os.getenv("HOST", "0.0.0.0")
    run_port = int(os.getenv("PORT", "5000"))
    run_debug = os.getenv("FLASK_DEBUG", "0") == "1"

    print("=" * 60)
    print("  弋阳县/万年县充换电设施规划系统（联合申报版）")
    print(f"  http://localhost:{run_port}")
    if BASE_PATH:
        print(f"  BASE_PATH: {BASE_PATH}")
        print(f"  prefixed home: http://localhost:{run_port}{BASE_PATH}/")
    print("  支持：弋阳县、万年县")
    print("  API: /api/config, /api/boundary?county=yiyang|wannian")
    print("       /api/stations/planned?county=yiyang|wannian|all")
    print("       /api/stats?county=yiyang|wannian|all")
    print("=" * 60)
    app.run(debug=run_debug, host=run_host, port=run_port)
