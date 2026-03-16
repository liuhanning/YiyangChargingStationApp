"""
图层类型服务模块
负责点位图层类型的 CRUD 操作和字段管理
"""
import sqlite3
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LayerService:
    """图层类型服务类"""

    def __init__(self, db_path: str):
        """
        初始化图层服务

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_layers(self, include_inactive: bool = False) -> List[Dict]:
        """
        获取所有图层类型

        Args:
            include_inactive: 是否包含未启用的图层

        Returns:
            图层类型列表
        """
        conn = self._get_conn()
        try:
            query = "SELECT * FROM point_layer_types WHERE 1=1"
            if not include_inactive:
                query += " AND is_active = 1"
            query += " ORDER BY type_name"

            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            layers = []
            for row in rows:
                layer = dict(row)
                # 解析 config JSON
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
            logger.error(f"获取图层列表失败：{e}")
            return []
        finally:
            conn.close()

    def get_layer(self, layer_id: int) -> Optional[Dict]:
        """
        获取图层类型详情

        Args:
            layer_id: 图层 ID

        Returns:
            图层详情
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM point_layer_types WHERE id = ?", (layer_id,))
            row = cursor.fetchone()

            if row:
                layer = dict(row)
                if layer.get('config'):
                    try:
                        layer['config'] = json.loads(layer['config'])
                    except:
                        layer['config'] = {}
                return layer
            return None

        except Exception as e:
            logger.error(f"获取图层详情失败：{e}")
            return None
        finally:
            conn.close()

    def get_layer_by_key(self, type_key: str) -> Optional[Dict]:
        """
        根据 type_key 获取图层类型

        Args:
            type_key: 图层类型标识

        Returns:
            图层详情
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM point_layer_types WHERE type_key = ?", (type_key,))
            row = cursor.fetchone()

            if row:
                layer = dict(row)
                if layer.get('config'):
                    try:
                        layer['config'] = json.loads(layer['config'])
                    except:
                        layer['config'] = {}
                return layer
            return None

        except Exception as e:
            logger.error(f"获取图层详情失败：{e}")
            return None
        finally:
            conn.close()

    def create_layer(self, data: Dict) -> Optional[Dict]:
        """
        创建图层类型

        Args:
            data: 图层数据

        Returns:
            创建成功的图层数据
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # 检查 key 是否已存在
            cursor.execute("SELECT id FROM point_layer_types WHERE type_key = ?", (data.get('type_key'),))
            if cursor.fetchone():
                logger.error(f"图层类型 key 已存在：{data.get('type_key')}")
                return None

            config_json = json.dumps(data.get('config', {}))

            cursor.execute("""
                INSERT INTO point_layer_types (type_key, type_name, description, icon, color, config, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('type_key'),
                data.get('type_name'),
                data.get('description', ''),
                data.get('icon', 'circle'),
                data.get('color', '#2563EB'),
                config_json,
                1 if data.get('is_active', True) else 0
            ))

            conn.commit()
            layer_id = cursor.lastrowid

            return self.get_layer(layer_id)

        except Exception as e:
            logger.error(f"创建图层失败：{e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def update_layer(self, layer_id: int, data: Dict) -> Optional[Dict]:
        """
        更新图层类型

        Args:
            layer_id: 图层 ID
            data: 更新数据

        Returns:
            更新后的图层数据
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            update_fields = []
            params = []

            allowed_fields = ['type_name', 'description', 'icon', 'color', 'is_active']
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    params.append(data[field])

            if 'config' in data:
                update_fields.append("config = ?")
                params.append(json.dumps(data['config']))

            if not update_fields:
                logger.error("没有要更新的字段")
                return None

            params.append(layer_id)
            sql = f"UPDATE point_layer_types SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(sql, params)
            conn.commit()

            return self.get_layer(layer_id)

        except Exception as e:
            logger.error(f"更新图层失败：{e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def delete_layer(self, layer_id: int) -> bool:
        """
        删除图层类型

        Args:
            layer_id: 图层 ID

        Returns:
            是否删除成功
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # 检查是否有关联的点位数据
            cursor.execute("SELECT COUNT(*) FROM point_data WHERE layer_type_id = ?", (layer_id,))
            count = cursor.fetchone()[0]
            if count > 0:
                logger.error(f"无法删除图层：存在 {count} 条关联点位数据")
                return False

            # 检查是否有关联的字段定义
            cursor.execute("SELECT COUNT(*) FROM point_field_definitions WHERE layer_type_id = ?", (layer_id,))
            field_count = cursor.fetchone()[0]
            if field_count > 0:
                logger.error(f"无法删除图层：存在 {field_count} 条关联字段定义")
                return False

            cursor.execute("DELETE FROM point_layer_types WHERE id = ?", (layer_id,))
            conn.commit()

            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"删除图层失败：{e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ==================== 字段定义管理 ====================

    def get_fields(self, layer_type_id: int) -> List[Dict]:
        """
        获取图层字段定义列表

        Args:
            layer_type_id: 图层类型 ID

        Returns:
            字段定义列表
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM point_field_definitions
                WHERE layer_type_id = ?
                ORDER BY sort_order, field_name
            """, (layer_type_id,))
            rows = cursor.fetchall()

            fields = []
            for row in rows:
                field = dict(row)
                # 解析 field_options JSON
                if field.get('field_options'):
                    try:
                        field['field_options'] = json.loads(field['field_options'])
                    except:
                        field['field_options'] = None
                fields.append(field)

            return fields

        except Exception as e:
            logger.error(f"获取字段列表失败：{e}")
            return []
        finally:
            conn.close()

    def get_field(self, field_id: int) -> Optional[Dict]:
        """获取字段详情"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM point_field_definitions WHERE id = ?", (field_id,))
            row = cursor.fetchone()

            if row:
                field = dict(row)
                if field.get('field_options'):
                    try:
                        field['field_options'] = json.loads(field['field_options'])
                    except:
                        field['field_options'] = None
                return field
            return None

        except Exception as e:
            logger.error(f"获取字段详情失败：{e}")
            return None
        finally:
            conn.close()

    def create_field(self, layer_type_id: int, data: Dict) -> Optional[Dict]:
        """
        创建字段定义

        Args:
            layer_type_id: 图层类型 ID
            data: 字段数据

        Returns:
            创建成功的字段数据
        """
        conn = self._get_conn()
        try:
            # 检查图层类型是否存在
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM point_layer_types WHERE id = ?", (layer_type_id,))
            if not cursor.fetchone():
                logger.error(f"图层类型不存在：{layer_type_id}")
                return None

            # 检查字段 key 是否已存在
            cursor.execute("""
                SELECT id FROM point_field_definitions
                WHERE layer_type_id = ? AND field_key = ?
            """, (layer_type_id, data.get('field_key')))
            if cursor.fetchone():
                logger.error(f"字段 key 已存在：{data.get('field_key')}")
                return None

            field_options_json = None
            if data.get('field_options'):
                field_options_json = json.dumps(data['field_options'])

            cursor.execute("""
                INSERT INTO point_field_definitions
                (layer_type_id, field_key, field_name, field_type, field_unit,
                 field_options, is_required, is_display_field, is_visual_field, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                layer_type_id,
                data.get('field_key'),
                data.get('field_name'),
                data.get('field_type', 'text'),
                data.get('field_unit'),
                field_options_json,
                1 if data.get('is_required') else 0,
                1 if data.get('is_display_field', True) else 0,
                1 if data.get('is_visual_field') else 0,
                data.get('sort_order', 10)
            ))

            conn.commit()
            field_id = cursor.lastrowid

            return self.get_field(field_id)

        except Exception as e:
            logger.error(f"创建字段失败：{e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def update_field(self, field_id: int, data: Dict) -> Optional[Dict]:
        """更新字段定义"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            update_fields = []
            params = []

            allowed_fields = ['field_name', 'field_type', 'field_unit', 'is_required',
                            'is_display_field', 'is_visual_field', 'sort_order']
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    params.append(1 if field.startswith('is_') and data[field] else data[field] if not field.startswith('is_') else (1 if data[field] else 0))

            if 'field_options' in data:
                update_fields.append("field_options = ?")
                params.append(json.dumps(data['field_options']) if data['field_options'] else None)

            if not update_fields:
                logger.error("没有要更新的字段")
                return None

            params.append(field_id)
            sql = f"UPDATE point_field_definitions SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(sql, params)
            conn.commit()

            return self.get_field(field_id)

        except Exception as e:
            logger.error(f"更新字段失败：{e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def delete_field(self, field_id: int) -> bool:
        """删除字段定义"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM point_field_definitions WHERE id = ?", (field_id,))
            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"删除字段失败：{e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_field_counts(self, layer_type_id: int) -> Dict:
        """获取图层的统计信息"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # 字段数量
            cursor.execute("SELECT COUNT(*) FROM point_field_definitions WHERE layer_type_id = ?", (layer_type_id,))
            field_count = cursor.fetchone()[0]

            # 点位数量
            cursor.execute("SELECT COUNT(*) FROM point_data WHERE layer_type_id = ?", (layer_type_id,))
            point_count = cursor.fetchone()[0]

            return {
                'field_count': field_count,
                'point_count': point_count
            }

        except Exception as e:
            logger.error(f"获取统计信息失败：{e}")
            return {'field_count': 0, 'point_count': 0}
        finally:
            conn.close()
