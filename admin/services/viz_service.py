"""
可视化服务模块
负责可视化规则的管理和点位样式渲染
"""
import sqlite3
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VizService:
    """可视化服务类"""

    def __init__(self, db_path: str):
        """
        初始化可视化服务

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_rules(self, layer_type_id: int, include_inactive: bool = False) -> List[Dict]:
        """
        获取图层类型的可视化规则

        Args:
            layer_type_id: 图层类型 ID
            include_inactive: 是否包含未启用的规则

        Returns:
            可视化规则列表
        """
        conn = self._get_conn()
        try:
            query = "SELECT * FROM point_visualization_rules WHERE layer_type_id = ?"
            if not include_inactive:
                query += " AND is_active = 1"
            query += " ORDER BY priority, id"

            cursor = conn.cursor()
            cursor.execute(query, (layer_type_id,))
            rows = cursor.fetchall()

            rules = []
            for row in rows:
                rule = dict(row)
                # 解析 config JSON
                if rule.get('config'):
                    try:
                        rule['config'] = json.loads(rule['config'])
                    except:
                        rule['config'] = {}
                rules.append(rule)

            return rules

        except Exception as e:
            logger.error(f"获取可视化规则失败：{e}")
            return []
        finally:
            conn.close()

    def get_rule(self, rule_id: int) -> Optional[Dict]:
        """获取规则详情"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM point_visualization_rules WHERE id = ?", (rule_id,))
            row = cursor.fetchone()

            if row:
                rule = dict(row)
                if rule.get('config'):
                    try:
                        rule['config'] = json.loads(rule['config'])
                    except:
                        rule['config'] = {}
                return rule
            return None

        except Exception as e:
            logger.error(f"获取规则详情失败：{e}")
            return None
        finally:
            conn.close()

    def create_rule(self, layer_type_id: int, data: Dict) -> Optional[Dict]:
        """创建单条规则"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            config_json = json.dumps(data.get('config', {}))

            cursor.execute("""
                INSERT INTO point_visualization_rules
                (layer_type_id, rule_name, field_key, rule_type, config, priority, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                layer_type_id,
                data.get('rule_name', '新规则'),
                data.get('field_key', ''),
                data.get('rule_type', 'category'),
                config_json,
                data.get('priority', 1),
                1 if data.get('is_active', True) else 0
            ))

            conn.commit()
            rule_id = cursor.lastrowid
            return self.get_rule(rule_id)

        except Exception as e:
            logger.error(f"创建规则失败：{e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def save_rules(self, layer_type_id: int, rules: List[Dict]) -> bool:
        """
        保存图层类型的可视化规则（批量更新）

        Args:
            layer_type_id: 图层类型 ID
            rules: 规则列表

        Returns:
            是否保存成功
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # 先删除现有规则
            cursor.execute("DELETE FROM point_visualization_rules WHERE layer_type_id = ?", (layer_type_id,))

            # 插入新规则
            for idx, rule in enumerate(rules):
                config_json = json.dumps(rule.get('config', {}))

                cursor.execute("""
                    INSERT INTO point_visualization_rules
                    (layer_type_id, rule_name, field_key, rule_type, config, priority, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    layer_type_id,
                    rule.get('rule_name', f'规则{idx + 1}'),
                    rule.get('field_key', ''),
                    rule.get('rule_type', 'category'),
                    config_json,
                    rule.get('priority', idx + 1),
                    1 if rule.get('is_active', True) else 0
                ))

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"保存可视化规则失败：{e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_rule(self, rule_id: int, data: Dict) -> Optional[Dict]:
        """更新单条规则"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            update_fields = []
            params = []

            allowed_fields = ['rule_name', 'field_key', 'rule_type', 'priority', 'is_active']
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    if field == 'is_active':
                        params.append(1 if data[field] else 0)
                    else:
                        params.append(data[field])

            if 'config' in data:
                update_fields.append("config = ?")
                params.append(json.dumps(data['config']))

            if not update_fields:
                logger.error("没有要更新的字段")
                return None

            params.append(rule_id)
            sql = f"UPDATE point_visualization_rules SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(sql, params)
            conn.commit()

            return self.get_rule(rule_id)

        except Exception as e:
            logger.error(f"更新规则失败：{e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def delete_rule(self, rule_id: int) -> bool:
        """删除规则"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM point_visualization_rules WHERE id = ?", (rule_id,))
            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"删除规则失败：{e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def render_point_style(self, point_data: Dict, rules: List[Dict],
                           layer_config: Dict) -> Dict:
        """
        根据规则渲染点位样式

        Args:
            point_data: 点位数据（包含 attributes）
            rules: 可视化规则列表
            layer_config: 图层基础配置（包含默认 icon, color）

        Returns:
            渲染后的样式 {color, size, icon, ...}
        """
        style = {
            'color': layer_config.get('color', '#2563EB'),
            'icon': layer_config.get('icon', 'circle'),
            'size': 10
        }

        attributes = point_data.get('attributes', {})

        for rule in rules:
            if not rule.get('is_active', True):
                continue

            rule_type = rule.get('rule_type')
            field_key = rule.get('field_key')
            config = rule.get('config', {})

            field_value = attributes.get(field_key)

            if field_value is None:
                continue

            if rule_type == 'category':
                # 分类映射
                if field_value in config:
                    mapping = config[field_value]
                    if isinstance(mapping, dict):
                        style.update(mapping)
                    elif isinstance(mapping, str):
                        style['color'] = mapping

            elif rule_type == 'size':
                # 数值映射大小
                try:
                    value = float(field_value)
                    min_val = config.get('min', 0)
                    max_val = config.get('max', 100)
                    min_size = config.get('minSize', 8)
                    max_size = config.get('maxSize', 20)

                    # 线性插值
                    if max_val > min_val:
                        ratio = (value - min_val) / (max_val - min_val)
                        ratio = max(0, min(1, ratio))  # 限制在 0-1
                        style['size'] = min_size + ratio * (max_size - min_size)
                    else:
                        style['size'] = (min_size + max_size) / 2
                except (ValueError, TypeError):
                    pass

            elif rule_type == 'color':
                # 连续色阶映射
                try:
                    value = float(field_value)
                    # 简单实现：根据数值范围选择颜色
                    color_stops = config.get('stops', [])
                    if color_stops:
                        # 找到合适的颜色区间
                        for i, stop in enumerate(color_stops):
                            if value <= stop.get('value', float('inf')):
                                style['color'] = stop.get('color')
                                break
                        else:
                            style['color'] = color_stops[-1].get('color') if color_stops else style['color']
                except (ValueError, TypeError):
                    pass

        return style

    def render_all_points(self, layer_type_id: int) -> List[Dict]:
        """
        渲染图层所有点位的样式

        Args:
            layer_type_id: 图层类型 ID

        Returns:
            包含样式的点位列表
        """
        conn = self._get_conn()
        try:
            # 获取图层配置
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, type_key, type_name, icon, color, config
                FROM point_layer_types WHERE id = ?
            """, (layer_type_id,))
            layer_row = cursor.fetchone()

            if not layer_row:
                return []

            layer_config = {
                'id': layer_row['id'],
                'type_key': layer_row['type_key'],
                'type_name': layer_row['type_name'],
                'icon': layer_row['icon'],
                'color': layer_row['color'],
            }
            if layer_row['config']:
                try:
                    layer_config['config'] = json.loads(layer_row['config'])
                except:
                    layer_config['config'] = {}

            # 获取可视化规则
            rules = self.get_rules(layer_type_id)

            # 获取所有点位
            cursor.execute("""
                SELECT id, point_name, county, township, longitude, latitude,
                       attributes, custom_style
                FROM point_data
                WHERE layer_type_id = ?
            """, (layer_type_id,))

            points = []
            for row in cursor.fetchall():
                point = dict(row)

                # 解析 attributes
                if point.get('attributes'):
                    try:
                        point['attributes'] = json.loads(point['attributes'])
                    except:
                        point['attributes'] = {}
                else:
                    point['attributes'] = {}

                # 解析 custom_style（自定义样式优先级最高）
                custom_style = {}
                if point.get('custom_style'):
                    try:
                        custom_style = json.loads(point['custom_style'])
                    except:
                        pass

                # 应用规则样式
                style = self.render_point_style(point, rules, layer_config)

                # 应用自定义样式（覆盖规则样式）
                if custom_style:
                    style.update(custom_style)

                point['style'] = style
                points.append(point)

            return points

        except Exception as e:
            logger.error(f"渲染点位样式失败：{e}")
            return []
        finally:
            conn.close()

    def get_viz_layers(self) -> List[Dict]:
        """获取所有可视觉化的图层（有规则或有点位数据的图层）"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT plt.*
                FROM point_layer_types plt
                INNER JOIN point_visualization_rules pvr ON plt.id = pvr.layer_type_id
                WHERE plt.is_active = 1 AND pvr.is_active = 1
            """)
            rows = cursor.fetchall()

            layers = []
            for row in rows:
                layer = dict(row)
                # 确保 config 总是一个字典
                if layer.get('config'):
                    try:
                        layer['config'] = json.loads(layer['config'])
                    except:
                        layer['config'] = {}
                else:
                    layer['config'] = {}
                layers.append(layer)

            return layers

        except Exception as e:
            logger.error(f"获取视觉化图层失败：{e}")
            return []
        finally:
            conn.close()
