"""
弋阳县充换电设施规划图 - 政务风格导出脚本
生成类似 demo.png 风格的专业规划图
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import sqlite3
from pathlib import Path
from datetime import datetime

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "db" / "yiyang_ev.db"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)


def load_db_data():
    """从数据库加载数据"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 加载城区现有充电站
    cursor.execute("""
        SELECT station_name, address, longitude, latitude 
        FROM stations_urban_coords 
        WHERE longitude IS NOT NULL AND latitude IS NOT NULL
    """)
    urban_stations = [dict(row) for row in cursor.fetchall()]
    
    # 加载加油站
    cursor.execute("""
        SELECT station_name, address, has_ev_charger, total_sales, longitude, latitude 
        FROM gas_stations
    """)
    gas_stations = [dict(row) for row in cursor.fetchall()]
    
    # 加载规划充电站
    cursor.execute("""
        SELECT station_name, township, scene, quantity, power_kw, year, 
               longitude, latitude, category, category_code
        FROM stations_planned
        WHERE station_name IS NOT NULL
    """)
    planned_stations = [dict(row) for row in cursor.fetchall()]
    
    # 加载县域边界
    boundary_file = BASE_DIR / "data" / "yiyang_county.geojson"
    if boundary_file.exists():
        with open(boundary_file, "r", encoding="utf-8") as f:
            geojson = json.load(f)
        boundary = geojson["features"][0]["geometry"]["coordinates"][0][0]
    else:
        boundary = []
    
    # 加载乡镇边界
    township_file = BASE_DIR / "data" / "yiyang_townships.geojson"
    if township_file.exists():
        with open(township_file, "r", encoding="utf-8") as f:
            township_geojson = json.load(f)
    else:
        township_geojson = None
    
    conn.close()
    
    return {
        "urban_stations": urban_stations,
        "gas_stations": gas_stations,
        "planned_stations": planned_stations,
        "boundary": boundary,
        "township_geojson": township_geojson,
    }


def generate_planning_map_html(data):
    """生成政务风格规划图 HTML"""
    
    # 统计各乡镇数据
    township_stats = {}
    for station in data["planned_stations"]:
        township = station.get("township", "未知")
        if township not in township_stats:
            township_stats[township] = {"count": 0, "piles": 0, "power": 0}
        township_stats[township]["count"] += 1
        township_stats[township]["piles"] += station.get("quantity", 0) or 0
        township_stats[township]["power"] += station.get("power_kw", 0) or 0
    
    # 生成统计表格 HTML
    table_rows = ""
    total_piles = 0
    total_power = 0
    for township, stats in sorted(township_stats.items()):
        table_rows += f"""
        <tr>
            <td>{township}</td>
            <td>{stats['count']}</td>
            <td>{stats['piles']}</td>
            <td>{stats['power']}</td>
        </tr>"""
        total_piles += stats["piles"]
        total_power += stats["power"]
    
    table_rows += f"""
        <tr style="font-weight:bold;background:#f3f4f6">
            <td>合计</td>
            <td>{len(data['planned_stations'])}</td>
            <td>{total_piles}</td>
            <td>{total_power}</td>
        </tr>"""
    
    # 边界坐标 JSON
    boundary_json = json.dumps(data["boundary"]) if data["boundary"] else "[]"
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>弋阳县新能源汽车充换电基础设施发展规划图</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
            background: #f5f5f5;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}
        
        /* 左侧地图区域 */
        #map-container {{
            flex: 1;
            position: relative;
            background: #e8ece9;
        }}
        
        #map {{
            width: 100%;
            height: 100%;
        }}
        
        /* 标题栏 */
        #title-bar {{
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            background: rgba(255,255,255,0.95);
            padding: 12px 40px;
            border-radius: 4px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.15);
            text-align: center;
        }}
        
        #title-bar h1 {{
            font-size: 22px;
            color: #1f2937;
            font-weight: 700;
            letter-spacing: 2px;
        }}
        
        #title-bar .subtitle {{
            font-size: 12px;
            color: #6b7280;
            margin-top: 4px;
        }}
        
        /* 右侧统计表格 */
        #stats-panel {{
            width: 320px;
            background: #fff;
            border-left: 2px solid #e5e7eb;
            padding: 20px;
            overflow-y: auto;
            box-shadow: -2px 0 8px rgba(0,0,0,0.05);
        }}
        
        .stats-title {{
            font-size: 16px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 2px solid #9333EA;
        }}
        
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-bottom: 20px;
        }}
        
        .stats-table th {{
            background: #f3f4f6;
            padding: 10px 8px;
            text-align: center;
            font-weight: 600;
            color: #374151;
            border: 1px solid #d1d5db;
        }}
        
        .stats-table td {{
            padding: 8px;
            text-align: center;
            border: 1px solid #e5e7eb;
            color: #4b5563;
        }}
        
        .stats-table tr:nth-child(even) {{
            background: #f9fafb;
        }}
        
        .stats-table tr:hover {{
            background: #f3f4f6;
        }}
        
        /* 图例 */
        .legend {{
            margin-top: 20px;
            padding: 15px;
            background: #f9fafb;
            border-radius: 6px;
            border: 1px solid #e5e7eb;
        }}
        
        .legend-title {{
            font-size: 13px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 10px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 8px 0;
            font-size: 12px;
            color: #4b5563;
        }}
        
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
            flex-shrink: 0;
        }}
        
        .legend-dot.red {{ background: #DC2626; }}
        .legend-dot.blue {{ background: #2563EB; }}
        .legend-dot.orange {{ background: #EA580C; }}
        
        .legend-line {{
            width: 20px;
            height: 3px;
            margin-right: 10px;
            flex-shrink: 0;
        }}
        
        .legend-line.purple {{ background: #9333EA; }}
        
        /* 比例尺 */
        #scale-bar {{
            position: absolute;
            bottom: 30px;
            left: 20px;
            z-index: 1000;
            background: rgba(255,255,255,0.9);
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 11px;
            color: #374151;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        /* 指北针 */
        #compass {{
            position: absolute;
            bottom: 30px;
            right: 20px;
            z-index: 1000;
            width: 40px;
            height: 40px;
            background: rgba(255,255,255,0.9);
            border-radius: 50%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: 900;
            color: #1f2937;
        }}
        
        /* 数据来源 */
        #data-source {{
            position: absolute;
            top: 10px;
            left: 10px;
            z-index: 1000;
            font-size: 10px;
            color: #6b7280;
            background: rgba(255,255,255,0.8);
            padding: 4px 8px;
            border-radius: 4px;
        }}
        
        /* 导出按钮 */
        #export-btn {{
            position: absolute;
            top: 80px;
            right: 340px;
            z-index: 1000;
            background: #9333EA;
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        #export-btn:hover {{
            background: #7c3aed;
        }}
    </style>
</head>
<body>
    <div id="map-container">
        <div id="map"></div>
        
        <div id="title-bar">
            <h1>弋阳县新能源汽车充换电基础设施发展规划图（2026 年）</h1>
            <div class="subtitle">江西省上饶市弋阳县 · 政务规划专题地图</div>
        </div>
        
        <button id="export-btn" onclick="exportMap()">📷 导出规划图</button>
        
        <div id="data-source">数据来源：弋阳县充换电设施规划数据库</div>
        
        <div id="scale-bar">
            <div style="display:flex;align-items:center;gap:8px">
                <div style="width:100px;height:2px;background:#374151"></div>
                <span>5 km</span>
            </div>
        </div>
        
        <div id="compass">N</div>
    </div>
    
    <div id="stats-panel">
        <div class="stats-title">📊 2026 年规划充电站统计表</div>
        <table class="stats-table">
            <thead>
                <tr>
                    <th>乡镇/街道</th>
                    <th>站点数</th>
                    <th>充电桩 (台)</th>
                    <th>总功率 (kW)</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        
        <div class="legend">
            <div class="legend-title">图例</div>
            <div class="legend-item">
                <div class="legend-line purple"></div>
                <span>县域行政边界</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot red"></div>
                <span>现状充电站 ({len(data['urban_stations'])} 座)</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot blue"></div>
                <span>规划充电站 ({len(data['planned_stations'])} 座)</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot orange"></div>
                <span>加油站 ({len(data['gas_stations'])} 座)</span>
            </div>
        </div>
        
        <div style="margin-top:20px;padding:12px;background:#fef3c7;border-radius:6px;font-size:11px;color:#92400e">
            <strong>说明：</strong><br>
            1. 本图为 2026 年度规划建设方案<br>
            2. 坐标系统：GCJ-02 火星坐标系<br>
            3. 数据截止：2025 年 12 月<br>
            4. 比例尺：1:140000
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
    <script>
        // 县域边界坐标
        const BOUNDARY = {boundary_json};
        
        // 站点数据
        const urbanStations = {json.dumps(data['urban_stations'], ensure_ascii=False)};
        const gasStations = {json.dumps(data['gas_stations'], ensure_ascii=False)};
        const plannedStations = {json.dumps(data['planned_stations'], ensure_ascii=False)};
        
        // 初始化地图 - 使用地形底图
        const map = L.map('map', {{
            center: [28.37, 117.44],
            zoom: 11,
            zoomControl: false,
        }});
        
        // 添加地形底图（天地图地形）
        const tiandituKey = '36c2c7b1a00180d86e97fa8ca2cd3bf2';
        
        // 地形底图
        L.tileLayer(`https://t{{s}}.tianditu.gov.cn/ter_w/wmts?tk=${{tiandituKey}}&SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ter&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}`, {{
            subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'],
            maxZoom: 18,
            attribution: '天地图地形'
        }}).addTo(map);
        
        // 添加县域边界（紫色）
        if (BOUNDARY.length > 0) {{
            const boundaryLatLng = BOUNDARY.map(p => [p[1], p[0]]);
            L.polygon(boundaryLatLng, {{
                color: '#9333EA',
                weight: 3,
                opacity: 1,
                fill: false
            }}).addTo(map);
        }}
        
        // 添加现有充电站（红色圆点）
        urbanStations.forEach(s => {{
            if (s.longitude && s.latitude) {{
                L.circleMarker([s.latitude, s.longitude], {{
                    radius: 6,
                    color: '#DC2626',
                    fillColor: '#DC2626',
                    fillOpacity: 1,
                    weight: 2
                }}).bindPopup(`<b>现状充电站</b><br>${{s.station_name}}<br>${{s.address || ''}}`);
            }}
        }});
        
        // 添加规划充电站（蓝色圆点）
        plannedStations.forEach(s => {{
            if (s.longitude && s.latitude) {{
                L.circleMarker([s.latitude, s.longitude], {{
                    radius: 7,
                    color: '#2563EB',
                    fillColor: '#2563EB',
                    fillOpacity: 1,
                    weight: 2
                }}).bindPopup(`<b>规划充电站（2026）</b><br>${{s.station_name}}<br>乡镇：${{s.township}}<br>充电桩：${{s.quantity || 0}}台<br>功率：${{s.power_kw || 0}}kW`);
            }}
        }});
        
        // 添加加油站（橙色圆点）
        gasStations.forEach(s => {{
            if (s.longitude && s.latitude) {{
                L.circleMarker([s.latitude, s.longitude], {{
                    radius: 5,
                    color: '#EA580C',
                    fillColor: '#EA580C',
                    fillOpacity: 1,
                    weight: 2
                }}).bindPopup(`<b>加油站</b><br>${{s.station_name}}<br>${{s.address || ''}}<br>年销量：${{s.total_sales || 0}}吨`);
            }}
        }});
        
        // 导出功能
        function exportMap() {{
            const container = document.getElementById('map-container');
            const btn = document.getElementById('export-btn');
            btn.style.display = 'none';
            
            html2canvas(container, {{
                useCORS: true,
                scale: 2,
                backgroundColor: '#ffffff'
            }}).then(canvas => {{
                const link = document.createElement('a');
                link.download = '弋阳县充换电设施规划图_' + new Date().getTime() + '.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
                btn.style.display = 'block';
            }}).catch(err => {{
                alert('导出失败：' + err.message);
                btn.style.display = 'block';
            }});
        }}
    </script>
</body>
</html>
'''
    return html


def main():
    print("=" * 60)
    print("弋阳县充换电设施规划图 - 政务风格导出")
    print("=" * 60)
    
    print("\n[1/3] 加载数据库数据...")
    data = load_db_data()
    print(f"  - 城区充电站：{len(data['urban_stations'])} 座")
    print(f"  - 加油站：{len(data['gas_stations'])} 座")
    print(f"  - 规划充电站：{len(data['planned_stations'])} 座")
    print(f"  - 县域边界点数：{len(data['boundary'])}")
    
    print("\n[2/3] 生成政务风格规划图...")
    html = generate_planning_map_html(data)
    
    output_file = OUTPUT_DIR / "planning_map.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ 规划图已保存：{output_file}")
    
    print("\n[3/3] 完成！")
    print(f"\n📌 操作提示：")
    print(f"   1. 用浏览器打开：{output_file}")
    print(f"   2. 点击「导出规划图」按钮生成 PNG 图片")
    print(f"   3. 生成的图片可在 PPT 或规划报告中使用")
    
    print("\n🎨 风格特征：")
    print("   - 地形晕渲底图（浅灰绿色调）")
    print("   - 亮紫色县域行政边界")
    print("   - 红色圆点 = 现状充电站")
    print("   - 蓝色圆点 = 规划充电站")
    print("   - 橙色圆点 = 加油站")
    print("   - 右侧统计表格（左图右表布局）")


if __name__ == "__main__":
    main()
