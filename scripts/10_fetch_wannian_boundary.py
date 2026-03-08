"""
获取万年县县域边界数据
尝试从多个数据源获取精确边界
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import urllib.request
import urllib.error
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# 万年县行政区划代码
ADCODE_WANNIAN = "361129"

# 数据源列表
SOURCES = [
    {
        "name": "DataV GeoAtlas (主)",
        "url": f"https://geo.datav.aliyun.com/areas_v3/bound/{ADCODE_WANNIAN}_full.json",
    },
    {
        "name": "DataV GeoAtlas (简化)",
        "url": f"https://geo.datav.aliyun.com/areas_v3/bound/{ADCODE_WANNIAN}.json",
    },
    {
        "name": "高德地图 API",
        "url": f"https://restapi.amap.com/v3/config/district?keywords=万年县&subdistrict=0&key=YOUR_KEY",
        "note": "需要 API Key"
    }
]


def fetch_with_timeout(url, timeout=10):
    """带超时的请求"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"  URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"  错误：{e}")
        return None


def save_geojson(geojson, filename):
    """保存 GeoJSON 文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 已保存：{filename}")


def extract_coords(geojson):
    """从 GeoJSON 提取坐标"""
    if not geojson or "features" not in geojson:
        return None, None
    
    feature = geojson["features"][0]
    geom = feature["geometry"]
    props = feature.get("properties", {})
    
    if geom["type"] == "Polygon":
        coords = geom["coordinates"][0]  # 外环
    elif geom["type"] == "MultiPolygon":
        coords = geom["coordinates"][0][0]  # 第一个多边形的外环
    else:
        coords = []
    
    return coords, props


def main():
    print("=" * 60)
    print("获取万年县县域边界")
    print("=" * 60)
    
    for source in SOURCES:
        print(f"\n尝试数据源：{source['name']}")
        if "note" in source:
            print(f"  注：{source['note']}")
        
        if "YOUR_KEY" in source["url"]:
            print("  ⏭️  跳过（需要 API Key）")
            continue
        
        geojson = fetch_with_timeout(source["url"])
        
        if geojson:
            coords, props = extract_coords(geojson)
            if coords and len(coords) > 10:
                print(f"  ✓ 获取成功！")
                print(f"    县名：{props.get('name', '未知')}")
                print(f"    边界点数：{len(coords)}")
                print(f"    中心点：{props.get('center', 'N/A')}")
                
                # 保存文件
                county_key = "wannian"
                save_geojson(geojson, DATA_DIR / f"{county_key}_county.geojson")
                
                # 同时保存简化版 JSON
                with open(DATA_DIR / f"{county_key}_boundary.json", "w", encoding="utf-8") as f:
                    json.dump(coords, f, ensure_ascii=False)
                print(f"  ✓ 已保存简化版：{county_key}_boundary.json")
                
                print("\n" + "=" * 60)
                print("✅ 万年县边界数据获取完成！")
                print("=" * 60)
                return
        
        print("  尝试下一个数据源...")
    
    # 所有源都失败，使用近似坐标
    print("\n⚠️  所有数据源获取失败，使用近似边界坐标")
    
    # 基于地理范围的近似边界（用于临时展示）
    approx_boundary = [
        [116.8892, 28.4521], [116.9012, 28.4612], [116.9234, 28.4756],
        [116.9456, 28.4889], [116.9678, 28.5012], [116.9901, 28.5134],
        [117.0123, 28.5256], [117.0345, 28.5378], [117.0567, 28.5501],
        [117.0789, 28.5623], [117.1012, 28.5745], [117.1234, 28.5867],
        [117.1456, 28.5989], [117.1678, 28.6112], [117.1901, 28.6234],
        [117.2123, 28.6356], [117.2345, 28.6478], [117.2567, 28.6601],
        [117.2789, 28.6723], [117.2901, 28.6845], [117.2978, 28.6967],
        [117.3012, 28.7089], [117.3001, 28.7212], [117.2956, 28.7334],
        [117.2878, 28.7456], [117.2767, 28.7578], [117.2623, 28.7701],
        [117.2445, 28.7823], [117.2234, 28.7945], [117.1989, 28.8067],
        [117.1712, 28.8156], [117.1412, 28.8212], [117.1089, 28.8234],
        [117.0745, 28.8223], [117.0378, 28.8178], [117.0012, 28.8101],
        [116.9645, 28.7989], [116.9278, 28.7845], [116.8934, 28.7678],
        [116.8612, 28.7489], [116.8312, 28.7278], [116.8045, 28.7045],
        [116.7812, 28.6789], [116.7623, 28.6512], [116.7478, 28.6212],
        [116.7389, 28.5889], [116.7356, 28.5545], [116.7378, 28.5189],
        [116.7456, 28.4834], [116.7589, 28.4512], [116.7778, 28.4234],
        [116.8012, 28.4012], [116.8289, 28.3856], [116.8589, 28.3778],
        [116.8812, 28.4123], [116.8892, 28.4521],
    ]
    
    # 创建 GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {
                "name": "万年县",
                "adcode": "361129",
                "center": [117.07, 28.69],
                "level": "county",
                "source": "approximate"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [approx_boundary]
            }
        }]
    }
    
    county_key = "wannian"
    save_geojson(geojson, DATA_DIR / f"{county_key}_county.geojson")
    
    with open(DATA_DIR / f"{county_key}_boundary.json", "w", encoding="utf-8") as f:
        json.dump(approx_boundary, f, ensure_ascii=False)
    
    print(f"\n  边界点数：{len(approx_boundary)}")
    print(f"  中心点：[117.07, 28.69]")
    print(f"\n⚠️  注：当前使用近似边界，精确数据需从测绘部门获取")
    print("=" * 60)


if __name__ == "__main__":
    main()
