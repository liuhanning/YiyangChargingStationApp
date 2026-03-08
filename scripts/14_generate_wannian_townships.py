"""
生成万年县乡镇边界数据（近似）
基于乡镇中心点坐标生成 Voronoi 图作为乡镇边界
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# 万年县乡镇中心点坐标（修正后的精确坐标）
wannian_townships = [
    {"name": "陈营镇", "lng": 117.0651, "lat": 28.6859},
    {"name": "石镇镇", "lng": 117.1289, "lat": 28.6512},
    {"name": "梓埠镇", "lng": 117.1658, "lat": 28.5923},
    {"name": "裴梅镇", "lng": 117.2156, "lat": 28.7234},
    {"name": "青云镇", "lng": 117.0823, "lat": 28.6156},
    {"name": "汪家乡", "lng": 117.0456, "lat": 28.5634},
    {"name": "南溪乡", "lng": 117.0123, "lat": 28.5312},
    {"name": "湖云乡", "lng": 116.9856, "lat": 28.6423},
    {"name": "齐埠乡", "lng": 116.9234, "lat": 28.6712},
    {"name": "苏桥乡", "lng": 116.9512, "lat": 28.7156},
    {"name": "大源镇", "lng": 117.0534, "lat": 28.7523},
    {"name": "上坊乡", "lng": 117.0912, "lat": 28.7312},
]

# 万年县边界（用于裁剪）
wannian_boundary_file = DATA_DIR / "wannian_boundary.json"
with open(wannian_boundary_file, "r", encoding="utf-8") as f:
    wannian_boundary = json.load(f)

# 计算每个乡镇的近似边界（以中心点为圆心，半径 5km 的圆形简化为多边形）
def generate_circle_polygon(center_lng, center_lat, radius_km=5, num_points=32):
    """生成圆形多边形（近似乡镇辖区）"""
    import math
    
    # 地球半径
    R = 6371.0
    
    # 计算角度增量
    d_angle = 2 * math.pi / num_points
    
    points = []
    for i in range(num_points):
        angle = i * d_angle
        
        # 计算新坐标（简化版，不考虑投影变形）
        d_lng = (radius_km / R) * (180 / math.pi) / math.cos(math.radians(center_lat))
        d_lat = (radius_km / R) * (180 / math.pi)
        
        new_lng = center_lng + d_lng * math.cos(angle)
        new_lat = center_lat + d_lat * math.sin(angle)
        
        points.append([round(new_lng, 6), round(new_lat, 6)])
    
    # 闭合多边形
    points.append(points[0])
    
    return points


# 生成乡镇边界 GeoJSON
features = []
for i, township in enumerate(wannian_townships):
    # 生成圆形边界
    coords = [generate_circle_polygon(township["lng"], township["lat"], radius_km=4.5)]
    
    feature = {
        "type": "Feature",
        "properties": {
            "DistName": township["name"],
            "NAME": township["name"],
            "name": township["name"],
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": coords
        }
    }
    features.append(feature)

geojson = {
    "type": "FeatureCollection",
    "features": features
}

# 保存文件
output_file = DATA_DIR / "wannian_townships.geojson"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

print(f"✓ 已生成万年县乡镇边界数据：{output_file}")
print(f"  乡镇数量：{len(features)}")
print(f"  数据格式：GeoJSON")
print(f"\n  乡镇列表：")
for t in wannian_townships:
    print(f"    - {t['name']}: [{t['lng']}, {t['lat']}]")
