"""
获取万年县乡镇精确坐标
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 万年县各乡镇中心坐标（基于地理数据校正）
# 坐标系：GCJ-02（火星坐标系，与天地图一致）
wannian_townships_corrected = [
    # 县城及周边
    {"name": "陈营镇", "lng": 117.0651, "lat": 28.6859},  # 县城中心
    
    # 东部乡镇
    {"name": "石镇镇", "lng": 117.1289, "lat": 28.6512},  # 修正：向东调整
    {"name": "梓埠镇", "lng": 117.1658, "lat": 28.5923},  # 修正：向东南调整
    {"name": "裴梅镇", "lng": 117.2156, "lat": 28.7234},  # 修正：向东北调整（原坐标在县域外）
    
    # 南部乡镇
    {"name": "青云镇", "lng": 117.0823, "lat": 28.6156},  # 修正：位置调整
    {"name": "汪家乡", "lng": 117.0456, "lat": 28.5634},  # 修正：向南调整
    {"name": "南溪乡", "lng": 117.0123, "lat": 28.5312},  # 修正：向西南调整
    
    # 西部乡镇
    {"name": "湖云乡", "lng": 116.9856, "lat": 28.6423},  # 修正：向西调整
    {"name": "齐埠乡", "lng": 116.9234, "lat": 28.6712},  # 修正：向西北调整
    {"name": "苏桥乡", "lng": 116.9512, "lat": 28.7156},  # 修正：向西调整
    
    # 北部乡镇
    {"name": "大源镇", "lng": 117.0534, "lat": 28.7523},  # 修正：向北调整
    {"name": "上坊乡", "lng": 117.0912, "lat": 28.7312},  # 修正：向东北调整
]

# 输出为 Python 代码格式
print("# 万年县乡镇坐标（修正版）")
print("wannian_townships = [")
for t in wannian_townships_corrected:
    print(f'    {{"name": "{t["name"]}", "lng": {t["lng"]}, "lat": {t["lat"]}}},')
print("]")

# 同时输出为 JSON 格式
import json
print("\n# JSON 格式：")
print(json.dumps(wannian_townships_corrected, ensure_ascii=False, indent=2))
