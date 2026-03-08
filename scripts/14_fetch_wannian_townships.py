"""
从 OpenStreetMap 获取万年县乡镇边界数据
使用 Overpass API 查询真实的行政区划边界
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import urllib.request
import urllib.parse
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Overpass API 查询万年县乡镇边界
# 查询条件：boundary=administrative + admin_level=8（乡镇级）
overpass_query = """
[out:json][timeout:60];
// 查询万年县范围内的乡镇级行政区划
area["name"="万年县"]["boundary"="administrative"]->.searchArea;
(
  relation["boundary"="administrative"]["admin_level"="8"](area.searchArea);
);
out body;
>;
out skel qt;
"""

# 编码查询
encoded_query = urllib.parse.quote(overpass_query)
overpass_url = f"https://overpass-api.de/api/interpreter?data={encoded_query}"

print("=" * 60)
print("从 OpenStreetMap 获取万年县乡镇边界")
print("=" * 60)
print("\n查询 Overpass API...")

try:
    req = urllib.request.Request(overpass_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    with urllib.request.urlopen(req, timeout=90) as response:
        osm_data = json.loads(response.read().decode('utf-8'))
    
    print(f"✓ 获取成功！")
    print(f"  元素数量：{len(osm_data.get('elements', []))}")
    
    # 转换为 GeoJSON 格式
    features = []
    for element in osm_data.get('elements', []):
        if element.get('type') == 'relation' and 'tags' in element:
            tags = element['tags']
            name = tags.get('name', tags.get('name:zh', '未知'))
            
            # 检查是否是乡镇级行政区
            if tags.get('boundary') == 'administrative' and tags.get('admin_level') == '8':
                # 提取边界节点
                nodes = element.get('members', [])
                boundary_nodes = [n for n in nodes if n.get('role') == 'outer' and n.get('type') == 'way']
                
                # 简单处理：如果有节点数据，提取坐标
                if boundary_nodes:
                    # 这里需要更复杂的处理来重建多边形
                    # 暂时跳过，因为需要递归获取 way 的节点坐标
                    pass
    
    # 由于 Overpass 返回的数据结构复杂，使用简化方案
    # 从 Nominatim 获取万年县各乡镇的中心点和边界
    print("\n尝试从 Nominatim 获取各乡镇边界...")
    
    wannian_townships = [
        "陈营镇", "石镇镇", "梓埠镇", "裴梅镇",
        "青云镇", "汪家乡", "南溪乡", "湖云乡",
        "齐埠乡", "苏桥乡", "大源镇", "上坊乡"
    ]
    
    features = []
    for town in wannian_townships:
        query = f"{town},万年县，江西省，中国"
        encoded = urllib.parse.quote(query)
        nominatim_url = f"https://nominatim.openstreetmap.org/search?format=json&q={encoded}&polygon_geojson=1"
        
        try:
            req = urllib.request.Request(nominatim_url, headers={
                "User-Agent": "YiyangEVProject/1.0"
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                results = json.loads(response.read().decode('utf-8'))
            
            if results:
                result = results[0]
                name = result.get('display_name', town)
                
                # 提取 GeoJSON 边界
                if 'geojson' in result:
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "DistName": town,
                            "NAME": town,
                            "name": town,
                            "osm_id": result.get('osm_id'),
                        },
                        "geometry": result['geojson']
                    }
                    features.append(feature)
                    print(f"  ✓ {town}: 获取到边界")
                else:
                    # 只有中心点
                    lat = float(result.get('lat', 0))
                    lon = float(result.get('lon', 0))
                    print(f"  ⚠ {town}: 只有中心点 [{lon}, {lat}]")
            else:
                print(f"  ✗ {town}: 未找到")
        except Exception as e:
            print(f"  ✗ {town}: {e}")
    
    # 保存结果
    if features:
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        output_file = DATA_DIR / "wannian_townships.geojson"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 已保存：{output_file}")
        print(f"  乡镇数量：{len(features)}")
    else:
        print("\n✗ 未能获取到任何乡镇边界数据")
        print("  建议：使用高德地图 API 或联系当地民政部门获取")

except Exception as e:
    print(f"✗ 请求失败：{e}")
    print("\n建议方案：")
    print("1. 高德地图 API：https://lbs.amap.com/api/webservice/guide/api/config")
    print("2. 联系万年县民政局获取官方乡镇勘界数据")
    print("3. 从江西省自然资源厅申请地理信息数据")
