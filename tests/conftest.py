"""
测试配置文件 - pytest fixtures

提供数据库、客户端、测试数据等共享夹具
"""

import pytest
import os
import sys
import sqlite3
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量（影响 app.py 中的 BASE_PATH）
os.environ['TESTING'] = 'true'

# 导入服务类（这些是纯 Python 类，不依赖 Flask 应用）
from admin.services.region_service import RegionService
from admin.services.layer_service import LayerService
from admin.services.point_service import PointService
from admin.services.viz_service import VizService

# Flask 应用和 routes 模块在 app fixture 中动态导入和重新加载


@pytest.fixture(scope='session')
def app_config():
    """应用配置夹具"""
    return {
        'TESTING': True,
        'DATABASE_PATH': str(project_root / 'data' / 'test_yiyang_ev.db'),
        'GEOJSON_PATH': str(project_root / 'data'),
    }


@pytest.fixture(scope='session')
def test_db_path(app_config):
    """测试数据库路径"""
    return app_config['DATABASE_PATH']


@pytest.fixture(scope='session')
def setup_test_database(test_db_path):
    """
    创建测试数据库并初始化表结构
    在会话开始时执行一次
    """
    # 确保数据目录存在
    os.makedirs(os.path.dirname(test_db_path), exist_ok=True)

    # 如果测试数据库已存在，先删除
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    try:
        # 启用外键约束
        cursor.execute('PRAGMA foreign_keys = ON')

        # 1. 创建地区表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                key TEXT NOT NULL UNIQUE,
                adcode TEXT,
                center TEXT,
                province TEXT,
                city TEXT,
                boundary_geojson TEXT,
                config TEXT,
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. 创建点位图层类型表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_layer_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_key TEXT NOT NULL UNIQUE,
                type_name TEXT NOT NULL,
                description TEXT,
                icon TEXT DEFAULT 'circle',
                color TEXT DEFAULT '#2563EB',
                is_active INTEGER DEFAULT 1,
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 3. 创建点位字段定义表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_field_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_type_id INTEGER NOT NULL,
                field_key TEXT NOT NULL,
                field_name TEXT NOT NULL,
                field_type TEXT DEFAULT 'text',
                field_unit TEXT,
                field_options TEXT,
                is_required INTEGER DEFAULT 0,
                is_display_field INTEGER DEFAULT 1,
                is_visual_field INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 10,
                FOREIGN KEY (layer_type_id) REFERENCES point_layer_types(id) ON DELETE CASCADE,
                UNIQUE(layer_type_id, field_key)
            )
        ''')

        # 4. 创建点位数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_type_id INTEGER NOT NULL,
                point_name TEXT,
                county TEXT,
                township TEXT,
                longitude REAL,
                latitude REAL,
                attributes TEXT,
                custom_style TEXT,
                memo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                FOREIGN KEY (layer_type_id) REFERENCES point_layer_types(id) ON DELETE CASCADE
            )
        ''')

        # 5. 创建可视化规则表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_visualization_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_type_id INTEGER NOT NULL,
                rule_name TEXT NOT NULL,
                field_key TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                config TEXT,
                priority INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (layer_type_id) REFERENCES point_layer_types(id) ON DELETE CASCADE
            )
        ''')

        # 6. 创建数据导入历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_import_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_type_id INTEGER NOT NULL,
                filename TEXT,
                import_count INTEGER,
                import_status TEXT,
                error_log TEXT,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                imported_by TEXT,
                FOREIGN KEY (layer_type_id) REFERENCES point_layer_types(id) ON DELETE CASCADE
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_point_data_layer ON point_data(layer_type_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_point_data_county ON point_data(county)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_point_data_location ON point_data(longitude, latitude)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_point_field_layer ON point_field_definitions(layer_type_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_point_viz_layer ON point_visualization_rules(layer_type_id)')

        # 插入测试数据 - 地区
        cursor.execute('''
            INSERT INTO regions (name, key, adcode, center, province, city) VALUES
            ('弋阳县', 'yiyang', '361126', '[117.4436,28.3419]', '江西省', '上饶市'),
            ('万年县', 'wannian', '361129', '[117.0639,28.6969]', '江西省', '上饶市'),
            ('吉安县', 'jian', '360821', '[114.9169,27.0369]', '江西省', '吉安市'),
            ('遂川县', 'suichuan', '360827', '[114.5269,26.3219]', '江西省', '吉安市')
        ''')

        # 插入测试数据 - 图层类型
        cursor.execute('''
            INSERT INTO point_layer_types (type_key, type_name, description, icon, color) VALUES
            ('charging_station', '充电站', '电动汽车充电站点', 'circle', '#DC2626'),
            ('gas_station', '加油站', '燃油/燃气加油站', 'circle', '#EA580C'),
            ('industrial_park', '产业园', '各类工业园区', 'square', '#16A34A'),
            ('vertiport', '垂直起降点', 'eVTOL 垂直起降场', 'triangle', '#9333EA'),
            ('logistics_center', '物流园', '物流仓储配送中心', 'square', '#0891B2'),
            ('scenic_spot', '景点', '旅游景点/景区', 'star', '#F59E0B')
        ''')

        # 插入测试数据 - 字段定义（产业园）
        cursor.execute('''
            INSERT INTO point_field_definitions (layer_type_id, field_key, field_name, field_type, field_unit, is_required, is_display_field, is_visual_field, sort_order) VALUES
            (3, 'name', '园区名称', 'text', NULL, 1, 1, 0, 1),
            (3, 'area', '占地面积', 'number', '亩', 0, 1, 1, 2),
            (3, 'companies', '入驻企业数', 'number', '家', 0, 1, 0, 3),
            (3, 'output', '年产值', 'number', '万元', 0, 1, 1, 4),
            (3, 'level', '园区等级', 'select', NULL, 0, 1, 1, 5),
            (3, 'established_year', '成立年份', 'number', '年', 0, 0, 0, 6)
        ''')

        # 插入字段选项（园区等级）
        cursor.execute('''
            UPDATE point_field_definitions
            SET field_options = '["省级","市级","县级"]'
            WHERE field_key = 'level' AND layer_type_id = 3
        ''')

        # 插入测试数据 - 可视化规则（产业园）
        cursor.execute('''
            INSERT INTO point_visualization_rules (layer_type_id, rule_name, field_key, rule_type, config, priority, is_active) VALUES
            (3, '按等级着色', 'level', 'category', '{"省级": "#16A34A", "市级": "#2563EB", "县级": "#EA580C"}', 1, 1),
            (3, '按产值设大小', 'output', 'size', '{"min": 0, "max": 50000, "minSize": 8, "maxSize": 24}', 2, 1),
            (3, '按产值着色', 'output', 'color', '{"stops": [{"value": 0, "color": "#FEF3C7"}, {"value": 10000, "color": "#FCD34D"}, {"value": 50000, "color": "#DC2626"}]}', 3, 0)
        ''')

        # 插入测试数据 - 点位数据（产业园）
        cursor.execute('''
            INSERT INTO point_data (layer_type_id, point_name, county, township, longitude, latitude, attributes, memo) VALUES
            (3, '弋阳高新区产业园', '弋阳县', '弋江镇', 117.4436, 28.3419, '{"area": 500, "level": "省级", "output": 25000, "companies": 45}', '省级重点园区'),
            (3, '万年高新技术产业园', '万年县', '陈营镇', 117.0639, 28.6969, '{"area": 380, "level": "省级", "output": 18000, "companies": 32}', NULL),
            (3, '吉安工业园', '吉安县', '敦厚镇', 114.9169, 27.0369, '{"area": 620, "level": "省级", "output": 35000, "companies": 58}', NULL),
            (3, '遂川产业园', '遂川县', '泉江镇', 114.5269, 26.3219, '{"area": 280, "level": "市级", "output": 12000, "companies": 21}', NULL),
            (3, '弋阳县级产业园', '弋阳县', '曹溪镇', 117.5012, 28.4123, '{"area": 150, "level": "县级", "output": 5000, "companies": 12}', NULL)
        ''')

        # 插入测试数据 - 充电站
        cursor.execute('''
            INSERT INTO point_data (layer_type_id, point_name, county, township, longitude, latitude, attributes, memo) VALUES
            (1, '弋阳客运站充电站', '弋阳县', '弋江镇', 117.4512, 28.3512, '{"operator": "国网电动", "pile_count": 8, "power": 120}', NULL),
            (1, '万年县政府充电站', '万年县', '陈营镇', 117.0712, 28.7012, '{"operator": "国网电动", "pile_count": 6, "power": 90}', NULL),
            (1, '吉安市充电站', '吉安县', '敦厚镇', 114.9212, 27.0412, '{"operator": "特来电", "pile_count": 12, "power": 180}', NULL),
            (1, '遂川客运站充电站', '遂川县', '泉江镇', 114.5312, 26.3312, '{"operator": "星星充电", "pile_count": 4, "power": 60}', NULL)
        ''')

        # 插入测试数据 - 加油站
        cursor.execute('''
            INSERT INTO point_data (layer_type_id, point_name, county, township, longitude, latitude, attributes, memo) VALUES
            (2, '弋阳加油站 A', '弋阳县', '弋江镇', 117.4456, 28.3456, '{"brand": "中石化", "fuel_type": "92#/95#", "has_convenience_store": true}', NULL),
            (2, '万年加油站 B', '万年县', '陈营镇', 117.0656, 28.6956, '{"brand": "中石油", "fuel_type": "92#/95#", "has_convenience_store": true}', NULL),
            (2, '吉安加油站 C', '吉安县', '敦厚镇', 114.9156, 27.0356, '{"brand": "壳牌", "fuel_type": "92#/95#/98#", "has_convenience_store": true}', NULL),
            (2, '遂川加油站 D', '遂川县', '泉江镇', 114.5256, 26.3256, '{"brand": "中石化", "fuel_type": "92#/95#", "has_convenience_store": false}', NULL)
        ''')

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    yield test_db_path

    # 会话结束后清理测试数据库
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture(scope='function')
def reset_database(test_db_path):
    """
    在每个测试函数前重置数据库数据
    确保测试隔离性
    """
    # 如果数据库文件存在，先删除
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # 重新创建数据库和表结构
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    try:
        # 启用外键约束
        cursor.execute('PRAGMA foreign_keys = ON')

        # 1. 创建地区表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                key TEXT NOT NULL UNIQUE,
                adcode TEXT,
                center TEXT,
                province TEXT,
                city TEXT,
                boundary_geojson TEXT,
                config TEXT,
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. 创建点位图层类型表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_layer_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_key TEXT NOT NULL UNIQUE,
                type_name TEXT NOT NULL,
                description TEXT,
                icon TEXT DEFAULT 'circle',
                color TEXT DEFAULT '#2563EB',
                is_active INTEGER DEFAULT 1,
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 3. 创建点位字段定义表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_field_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_type_id INTEGER NOT NULL,
                field_key TEXT NOT NULL,
                field_name TEXT NOT NULL,
                field_type TEXT DEFAULT 'text',
                field_unit TEXT,
                field_options TEXT,
                is_required INTEGER DEFAULT 0,
                is_display_field INTEGER DEFAULT 1,
                is_visual_field INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 10,
                FOREIGN KEY (layer_type_id) REFERENCES point_layer_types(id) ON DELETE CASCADE,
                UNIQUE(layer_type_id, field_key)
            )
        ''')

        # 4. 创建点位数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_type_id INTEGER NOT NULL,
                point_name TEXT,
                county TEXT,
                township TEXT,
                longitude REAL,
                latitude REAL,
                attributes TEXT,
                custom_style TEXT,
                memo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                FOREIGN KEY (layer_type_id) REFERENCES point_layer_types(id) ON DELETE CASCADE
            )
        ''')

        # 5. 创建可视化规则表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_visualization_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_type_id INTEGER NOT NULL,
                rule_name TEXT NOT NULL,
                field_key TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                config TEXT,
                priority INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (layer_type_id) REFERENCES point_layer_types(id) ON DELETE CASCADE
            )
        ''')

        # 6. 创建数据导入历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_import_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_type_id INTEGER NOT NULL,
                filename TEXT,
                import_count INTEGER,
                import_status TEXT,
                error_log TEXT,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                imported_by TEXT,
                FOREIGN KEY (layer_type_id) REFERENCES point_layer_types(id) ON DELETE CASCADE
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_point_data_layer ON point_data(layer_type_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_point_data_county ON point_data(county)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_point_data_location ON point_data(longitude, latitude)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_point_field_layer ON point_field_definitions(layer_type_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_point_viz_layer ON point_visualization_rules(layer_type_id)')

        # 插入测试数据 - 地区
        cursor.execute('''
            INSERT INTO regions (name, key, adcode, center, province, city) VALUES
            ('弋阳县', 'yiyang', '361126', '[117.4436,28.3419]', '江西省', '上饶市'),
            ('万年县', 'wannian', '361129', '[117.0639,28.6969]', '江西省', '上饶市'),
            ('吉安县', 'jian', '360821', '[114.9169,27.0369]', '江西省', '吉安市'),
            ('遂川县', 'suichuan', '360827', '[114.5269,26.3219]', '江西省', '吉安市')
        ''')

        # 插入测试数据 - 图层类型
        cursor.execute('''
            INSERT INTO point_layer_types (type_key, type_name, description, icon, color) VALUES
            ('charging_station', '充电站', '电动汽车充电站点', 'circle', '#DC2626'),
            ('gas_station', '加油站', '燃油/燃气加油站', 'circle', '#EA580C'),
            ('industrial_park', '产业园', '各类工业园区', 'square', '#16A34A'),
            ('vertiport', '垂直起降点', 'eVTOL 垂直起降场', 'triangle', '#9333EA'),
            ('logistics_center', '物流园', '物流仓储配送中心', 'square', '#0891B2'),
            ('scenic_spot', '景点', '旅游景点/景区', 'star', '#F59E0B')
        ''')

        # 插入测试数据 - 字段定义（产业园）
        cursor.execute('''
            INSERT INTO point_field_definitions (layer_type_id, field_key, field_name, field_type, field_unit, is_required, is_display_field, is_visual_field, sort_order) VALUES
            (3, 'name', '园区名称', 'text', NULL, 1, 1, 0, 1),
            (3, 'area', '占地面积', 'number', '亩', 0, 1, 1, 2),
            (3, 'companies', '入驻企业数', 'number', '家', 0, 1, 0, 3),
            (3, 'output', '年产值', 'number', '万元', 0, 1, 1, 4),
            (3, 'level', '园区等级', 'select', NULL, 0, 1, 1, 5),
            (3, 'established_year', '成立年份', 'number', '年', 0, 0, 0, 6)
        ''')

        # 插入字段选项（园区等级）
        cursor.execute('''
            UPDATE point_field_definitions
            SET field_options = '["省级","市级","县级"]'
            WHERE field_key = 'level' AND layer_type_id = 3
        ''')

        # 插入测试数据 - 可视化规则（产业园）
        cursor.execute('''
            INSERT INTO point_visualization_rules (layer_type_id, rule_name, field_key, rule_type, config, priority, is_active) VALUES
            (3, '按等级着色', 'level', 'category', '{"省级": "#16A34A", "市级": "#2563EB", "县级": "#EA580C"}', 1, 1),
            (3, '按产值设大小', 'output', 'size', '{"min": 0, "max": 50000, "minSize": 8, "maxSize": 24}', 2, 1),
            (3, '按产值着色', 'output', 'color', '{"stops": [{"value": 0, "color": "#FEF3C7"}, {"value": 10000, "color": "#FCD34D"}, {"value": 50000, "color": "#DC2626"}]}', 3, 0)
        ''')

        # 插入测试数据 - 点位数据（产业园）
        cursor.execute('''
            INSERT INTO point_data (layer_type_id, point_name, county, township, longitude, latitude, attributes, memo) VALUES
            (3, '弋阳高新区产业园', '弋阳县', '弋江镇', 117.4436, 28.3419, '{"area": 500, "level": "省级", "output": 25000, "companies": 45}', '省级重点园区'),
            (3, '万年高新技术产业园', '万年县', '陈营镇', 117.0639, 28.6969, '{"area": 380, "level": "省级", "output": 18000, "companies": 32}', NULL),
            (3, '吉安工业园', '吉安县', '敦厚镇', 114.9169, 27.0369, '{"area": 620, "level": "省级", "output": 35000, "companies": 58}', NULL),
            (3, '遂川产业园', '遂川县', '泉江镇', 114.5269, 26.3219, '{"area": 280, "level": "市级", "output": 12000, "companies": 21}', NULL),
            (3, '弋阳县级产业园', '弋阳县', '曹溪镇', 117.5012, 28.4123, '{"area": 150, "level": "县级", "output": 5000, "companies": 12}', NULL),
            (1, '弋阳客运站充电站', '弋阳县', '弋江镇', 117.4512, 28.3512, '{"operator": "国网电动", "pile_count": 8, "power": 120}', NULL),
            (1, '万年县政府充电站', '万年县', '陈营镇', 117.0712, 28.7012, '{"operator": "国网电动", "pile_count": 6, "power": 90}', NULL),
            (1, '吉安市充电站', '吉安县', '敦厚镇', 114.9212, 27.0412, '{"operator": "特来电", "pile_count": 12, "power": 180}', NULL),
            (1, '遂川客运站充电站', '遂川县', '泉江镇', 114.5312, 26.3312, '{"operator": "星星充电", "pile_count": 4, "power": 60}', NULL),
            (2, '弋阳加油站 A', '弋阳县', '弋江镇', 117.4456, 28.3456, '{"brand": "中石化", "fuel_type": "92#/95#", "has_convenience_store": true}', NULL),
            (2, '万年加油站 B', '万年县', '陈营镇', 117.0656, 28.6956, '{"brand": "中石油", "fuel_type": "92#/95#", "has_convenience_store": true}', NULL),
            (2, '吉安加油站 C', '吉安县', '敦厚镇', 114.9156, 27.0356, '{"brand": "壳牌", "fuel_type": "92#/95#/98#", "has_convenience_store": true}', NULL),
            (2, '遂川加油站 D', '遂川县', '泉江镇', 114.5256, 26.3256, '{"brand": "中石化", "fuel_type": "92#/95#", "has_convenience_store": false}', NULL)
        ''')

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    yield test_db_path


@pytest.fixture
def app(reset_database, app_config):
    """Flask 应用夹具 - 每次测试重新创建应用实例"""
    import importlib
    import config

    # 修改 config 中的数据库路径
    config.DATABASE["path"] = Path(reset_database)

    # 重新加载 admin.routes 模块以使用新的数据库路径
    import admin.routes as routes_module
    importlib.reload(routes_module)

    # 重新加载 app 模块
    import app as app_module
    importlib.reload(app_module)

    flask_app = app_module.app
    flask_app.config.update(app_config)
    yield flask_app


@pytest.fixture
def client(app):
    """Flask 测试客户端夹具"""
    return app.test_client()


@pytest.fixture
def db_connection(reset_database):
    """数据库连接夹具"""
    conn = sqlite3.connect(reset_database)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def region_service(reset_database):
    """地区服务夹具"""
    return RegionService(reset_database)


@pytest.fixture
def layer_service(reset_database):
    """图层服务夹具"""
    return LayerService(reset_database)


@pytest.fixture
def point_service(reset_database):
    """点位服务夹具"""
    return PointService(reset_database)


@pytest.fixture
def viz_service(reset_database):
    """可视化服务夹具"""
    return VizService(reset_database)


@pytest.fixture
def sample_region_data():
    """示例地区数据"""
    return {
        'name': '测试县',
        'key': 'ceshi',
        'adcode': '360899',
        'center': [115.0, 27.0],
        'province': '江西省',
        'city': '测试市'
    }


@pytest.fixture
def sample_layer_data():
    """示例图层类型数据"""
    return {
        'type_key': 'test_park',
        'type_name': '测试园区',
        'description': '用于测试的园区类型',
        'icon': 'square',
        'color': '#FF0000'
    }


@pytest.fixture
def sample_point_data():
    """示例点位数据"""
    return {
        'layer_type_id': 1,
        'point_name': '测试点位',
        'county': '弋阳县',
        'township': '弋江镇',
        'longitude': 117.4436,
        'latitude': 28.3419,
        'attributes': json.dumps({'key': 'value', 'number': 100}),
        'memo': '测试备注'
    }


@pytest.fixture
def sample_viz_rule_data():
    """示例可视化规则数据"""
    return {
        'layer_type_id': 1,
        'rule_name': '测试规则',
        'field_key': 'test_field',
        'rule_type': 'category',
        'config': json.dumps({'value1': '#FF0000', 'value2': '#00FF00'}),
        'priority': 1,
        'is_active': 1
    }
