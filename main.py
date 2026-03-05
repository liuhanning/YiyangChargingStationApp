"""
主程序入口
弋阳县充换电设施规划地图生成系统
"""
import logging
import subprocess
import shutil
from pathlib import Path

from config import LOGGING_CONFIG, COUNTY_INFO, OUTPUT_DIR, BASE_DIR
from data_loader import DataLoader

# 配置日志
logging.basicConfig(
    level=LOGGING_CONFIG["level"],
    format=LOGGING_CONFIG["format"],
    datefmt=LOGGING_CONFIG["date_format"]
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info(f"{COUNTY_INFO['name']}充换电设施规划地图生成系统")
    logger.info("=" * 60)

    try:
        # 1. 加载数据
        logger.info("\n[1/3] 加载数据...")
        loader = DataLoader()
        data = loader.load_all_data()

        # 显示统计信息
        logger.info("\n数据统计:")
        logger.info(f"  - 现有充电站: {len(data['urban_stations'])} 座")
        logger.info(f"  - 加油站: {len(data['gas_stations'])} 座")
        logger.info(f"  - 规划充电站: {len(data['planned_stations'])} 站")
        logger.info(f"  - 经济数据: {len(data['economic_stats'])} 条记录")

        # 2. 渲染地图（使用旧版脚本）
        logger.info("\n[2/3] 渲染地图...")

        # 调用旧版脚本生成地图
        old_script = BASE_DIR / "scripts" / "08_map_tianditu.py"
        result = subprocess.run(
            ["python", str(old_script)],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )

        if result.returncode == 0:
            logger.info("✓ 地图生成成功（使用天地图脚本）")

            # 复制到 output 目录
            src_map = BASE_DIR / "map.html"
            dst_map = OUTPUT_DIR / "map.html"
            if src_map.exists():
                shutil.copy(src_map, dst_map)
                map_path = dst_map
                logger.info(f"✓ 地图已复制到: {dst_map}")
            else:
                map_path = src_map
        else:
            logger.error(f"✗ 地图生成失败: {result.stderr}")
            return False

        # 3. 完成
        logger.info("\n[3/3] 完成!")
        logger.info("=" * 60)
        logger.info("输出文件:")
        logger.info(f"  - 地图: {map_path}")
        logger.info("=" * 60)
        logger.info("\n提示: 请在浏览器中打开 output/map.html 查看地图")

        return True

    except Exception as e:
        logger.error(f"\n✗ 程序执行失败: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
