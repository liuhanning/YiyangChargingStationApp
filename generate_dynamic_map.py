"""
动态地图生成器 - 根据前端发送的点位数据生成规划图
使用与 generate_wannian_official.py 相同的技术路线
"""
import os
import io
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, RegularPolygon
import matplotlib.image as mpimg
import numpy as np
from flask import jsonify, send_file
from config import DATABASE, MAP_API


# 获取项目根目录
BASE_DIR = Path(__file__).parent
# 输出目录
OUTPUT_DIR = BASE_DIR / "output_dynamic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== 基础地图配置 ==========
# 地图底图
YIYANG_MAP = BASE_DIR / "弋阳县地图 .jpg"
WANNAN_MAP = BASE_DIR / "联合地图.jpg"

# 弋阳县边界
yiyang_bounds = {
    "north": 28.50,
    "south": 28.25,
    "east": 117.60,
    "west": 117.25,
}

# 万年县边界
wannian_bounds = {
    "north": 28.95,
    "south": 28.40,
    "east": 117.50,
    "west": 116.60,
}


def get_bounds(county):
    """获取指定县的边界"""
    if county == "wannian":
        return wannian_bounds
    return yiyang_bounds


def get_base_map(county):
    """获取基础地图"""
    if county == "wannian":
        map_file = WANNAN_MAP
    else:
        map_file = YIYANG_MAP

    if not map_file.exists():
        raise FileNotFoundError(f"地图文件不存在: {map_file}")

    return mpimg.imread(str(map_file))


def coord_to_pixel(lon, lat, bounds, img_size):
    """将经纬度转换为像素坐标"""
    width, height = img_size
    x_ratio = (lon - bounds["west"]) / (bounds["east"] - bounds["west"])
    y_ratio = (bounds["north"] - lat) / (bounds["north"] - bounds["south"])
    x = x_ratio * width
    y = y_ratio * height
    return x, y


def draw_dynamic_map(points_data, county="yiyang"):
    """
    绘制动态规划图
    :param points_data: 前端发送的点位数据，格式为 [{'name': '名称', 'lng': 经度, 'lat': 纬度}]
    :param county: 县域，yiyang 或 wannian
    """
    bounds = get_bounds(county)

    try:
        img = get_base_map(county)
    except Exception as e:
        print(f"地图加载失败: {e}")
        return None, f"地图加载失败: {e}"

    height, width = img.shape[:2]

    # 创建图形
    fig, ax = plt.subplots(figsize=(20, 14), dpi=150)
    ax.imshow(img)
    ax.axis("off")

    # 绘制点位
    for i, point in enumerate(points_data):
        lon = point["lng"]
        lat = point["lat"]
        name = point.get("name", f"规划站-{i+1}")

        x, y = coord_to_pixel(lon, lat, bounds, (width, height))

        if 0 <= x <= width and 0 <= y <= height:
            # 使用蓝色圆点表示规划点位
            circle = Circle((x, y), radius=12, color="#2563EB", alpha=0.95, zorder=5)
            ax.add_patch(circle)
            circle_border = Circle((x, y), radius=12, color="white", fill=False, linewidth=2, zorder=6)
            ax.add_patch(circle_border)

            # 添加名称标签
            ax.text(x, y + 20, name, fontsize=8, ha="center", va="bottom", color="#1a3a5c", weight="bold")

    # 图例
    legend_elements = [
        mpatches.Patch(color="#2563EB", label=f"规划充电站 ({len(points_data)}个)")
    ]

    ax.legend(
        handles=legend_elements,
        loc="lower right",
        framealpha=0.95,
        fontsize=12,
        edgecolor="black",
        facecolor="white"
    )

    # 标题
    county_name = "弋阳县" if county == "yiyang" else "万年县"
    plt.suptitle(f"{county_name}新能源汽车充换电基础设施发展规划图",
                 fontsize=18, fontweight="bold", y=0.98)

    # 保存为临时文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{county}_dynamic_plan_{timestamp}"
    output_path = OUTPUT_DIR / f"{output_filename}.png"

    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"[OK] 动态规划图已保存：{output_path}")

    # 保存为 PDF
    pdf_path = OUTPUT_DIR / f"{output_filename}.pdf"
    plt.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    print(f"[OK] PDF 已保存：{pdf_path}")

    plt.close()

    return str(output_path), str(pdf_path)


# ========== API 接口 ==========

def api_generate_dynamic_map():
    """
    后端 API 接口，用于接收前端发送的点位数据并返回生成的规划图
    """
    # 由于这是 Flask 应用，我们需要使用 request 对象获取前端数据
    from flask import request

    if request.method == "POST":
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
                "png_file": os.path.basename(png_path),
                "pdf_file": os.path.basename(pdf_path),
                "output_dir": str(OUTPUT_DIR),
                "points_count": len(points)
            })

        except Exception as e:
            print(f"地图生成失败: {e}")
            return jsonify({"error": str(e), "success": False}), 500
    else:
        return jsonify({"error": "只支持 POST 请求", "success": False}), 405


# ========== 运行示例 ==========

if __name__ == "__main__":
    # 示例数据 - 弋阳县中心区域的几个点
    test_points = [
        {"name": "弋阳县中心站", "lng": 117.45, "lat": 28.37},
        {"name": "弋阳县东站", "lng": 117.52, "lat": 28.38},
        {"name": "弋阳县西站", "lng": 117.38, "lat": 28.36},
        {"name": "弋阳县北站", "lng": 117.44, "lat": 28.42},
    ]

    print("=" * 60)
    print("动态规划图生成器（示例）")
    print("=" * 60)

    print(f"\n测试数据点数: {len(test_points)}")

    # 生成弋阳县规划图
    print("\n生成弋阳县动态规划图...")
    png_path, pdf_path = draw_dynamic_map(test_points, county="yiyang")

    print(f"\n输出文件:")
    if png_path:
        print(f"  PNG: {png_path}")
    if pdf_path:
        print(f"  PDF: {pdf_path}")

    print("\n测试完成！")
