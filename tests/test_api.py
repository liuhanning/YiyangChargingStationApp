"""
API 集成测试
测试所有后台管理 API 端点
"""

import pytest
import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestRegionsAPI:
    """地区管理 API 测试"""

    def test_get_regions(self, client):
        """测试获取地区列表"""
        response = client.get('/admin/api/regions')
        assert response.status_code == 200
        data = response.get_json()
        assert 'regions' in data
        assert isinstance(data['regions'], list)
        assert len(data['regions']) == 4  # fixture 中 4 个地区

    def test_get_region_detail(self, client):
        """测试获取地区详情"""
        response = client.get('/admin/api/regions/1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'region' in data
        assert data['region']['id'] == 1

    def test_get_region_not_found(self, client):
        """测试获取不存在的地区"""
        response = client.get('/admin/api/regions/99999')
        assert response.status_code == 404

    def test_create_region(self, client, sample_region_data):
        """测试创建地区"""
        response = client.post(
            '/admin/api/regions',
            json=sample_region_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['region']['name'] == sample_region_data['name']

    def test_update_region(self, client):
        """测试更新地区"""
        update_data = {'name': '更新后的县名'}
        response = client.put(
            '/admin/api/regions/1',
            json=update_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['region']['name'] == '更新后的县名'

    def test_delete_region(self, client):
        """测试删除地区（先创建再删除）"""
        # 创建
        data = {
            'name': '待删除县',
            'key': 'delete_test_api',
            'adcode': '360800'
        }
        create_resp = client.post('/admin/api/regions', json=data)
        region_id = create_resp.get_json()['region']['id']

        # 删除
        delete_resp = client.delete(f'/admin/api/regions/{region_id}')
        assert delete_resp.status_code == 200


class TestLayersAPI:
    """图层类型管理 API 测试"""

    def test_get_layers(self, client):
        """测试获取图层类型列表"""
        response = client.get('/admin/api/layers')
        assert response.status_code == 200
        data = response.get_json()
        assert 'layers' in data
        assert len(data['layers']) == 6  # fixture 中 6 个图层

    def test_get_layer_detail(self, client):
        """测试获取图层详情"""
        response = client.get('/admin/api/layers/3')
        assert response.status_code == 200
        data = response.get_json()
        assert data['layer']['type_name'] == '产业园'

    def test_create_layer(self, client, sample_layer_data):
        """测试创建图层类型"""
        response = client.post(
            '/admin/api/layers',
            json=sample_layer_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_update_layer(self, client):
        """测试更新图层类型"""
        update_data = {'type_name': '更新后的产业园', 'color': '#FF0000'}
        response = client.put(
            '/admin/api/layers/3',
            json=update_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_delete_layer_with_data(self, client):
        """测试删除有关联数据的图层（应该失败）"""
        response = client.delete('/admin/api/layers/3')
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestFieldsAPI:
    """字段定义管理 API 测试"""

    def test_get_fields(self, client):
        """测试获取字段定义列表"""
        response = client.get('/admin/api/layers/3/fields')
        assert response.status_code == 200
        data = response.get_json()
        assert 'fields' in data
        assert len(data['fields']) >= 6  # 产业园有 6 个字段

    def test_create_field(self, client):
        """测试创建字段定义"""
        field_data = {
            'field_key': 'test_api_field',
            'field_name': 'API 测试字段',
            'field_type': 'text'
        }
        response = client.post(
            '/admin/api/layers/3/fields',
            json=field_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_update_field(self, client):
        """测试更新字段定义"""
        # 先获取一个字段
        fields_resp = client.get('/admin/api/layers/3/fields')
        fields = fields_resp.get_json()['fields']
        # 找一个可以修改的字段
        target = next((f for f in fields if f['field_key'] != 'name'), fields[0])

        update_data = {'field_name': '更新后的字段名', 'field_unit': 'km²'}
        response = client.put(
            f'/admin/api/layers/fields/{target["id"]}',
            json=update_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_delete_field(self, client):
        """测试删除字段定义（先创建再删除）"""
        # 创建
        field_data = {
            'field_key': 'test_delete_api',
            'field_name': '待删除字段',
            'field_type': 'text'
        }
        create_resp = client.post('/admin/api/layers/3/fields', json=field_data)
        field_id = create_resp.get_json()['field']['id']

        # 删除
        delete_resp = client.delete(f'/admin/api/layers/fields/{field_id}')
        assert delete_resp.status_code == 200


class TestPointsAPI:
    """点位数据 API 测试"""

    def test_get_points(self, client):
        """测试获取点位列表"""
        response = client.get('/admin/api/points?page=1&limit=20')
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data
        assert data['total'] > 0

    def test_get_points_by_layer(self, client):
        """测试按图层筛选点位"""
        response = client.get('/admin/api/points?layer_type_id=3')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] >= 5  # 产业园至少 5 个

    def test_get_points_by_county(self, client):
        """测试按县区筛选点位"""
        response = client.get('/admin/api/points?county=弋阳县')
        assert response.status_code == 200
        data = response.get_json()
        # 弋阳县有产业园和充电站
        assert data['total'] >= 2

    def test_get_point_detail(self, client):
        """测试获取点位详情"""
        # 先获取一个点位 ID
        points_resp = client.get('/admin/api/points?limit=1')
        point_id = points_resp.get_json()['items'][0]['id']

        response = client.get(f'/admin/api/points/{point_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert 'point' in data
        assert data['point']['id'] == point_id

    def test_create_point(self, client):
        """测试创建点位"""
        point_data = {
            'layer_type_id': 1,
            'point_name': 'API 测试充电站',
            'longitude': 117.5,
            'latitude': 28.5,
            'attributes': {'operator': '测试运营商', 'pile_count': 10}
        }
        response = client.post(
            '/admin/api/points',
            json=point_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['point']['point_name'] == 'API 测试充电站'

        # 清理
        point_id = data['point']['id']
        client.delete(f'/admin/api/points/{point_id}')

    def test_update_point(self, client):
        """测试更新点位"""
        # 先获取一个点位
        points_resp = client.get('/admin/api/points?layer_type_id=3&limit=1')
        point_id = points_resp.get_json()['items'][0]['id']

        update_data = {
            'point_name': '更新后的产业园',
            'attributes': {'area': 999, 'level': '省级'}
        }
        response = client.put(
            f'/admin/api/points/{point_id}',
            json=update_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_delete_point(self, client):
        """测试删除点位（先创建再删除）"""
        # 创建
        point_data = {
            'layer_type_id': 1,
            'point_name': '待删除点位',
            'longitude': 117.0,
            'latitude': 28.0
        }
        create_resp = client.post('/admin/api/points', json=point_data)
        point_id = create_resp.get_json()['point']['id']

        # 删除
        delete_resp = client.delete(f'/admin/api/points/{point_id}')
        assert delete_resp.status_code == 200

    def test_batch_delete(self, client):
        """测试批量删除"""
        # 先创建几个测试点位
        point_ids = []
        for i in range(3):
            point_data = {
                'layer_type_id': 1,
                'point_name': f'批量测试{i}',
                'longitude': 117.0 + i * 0.001,
                'latitude': 28.0 + i * 0.001
            }
            resp = client.post('/admin/api/points', json=point_data)
            point_ids.append(resp.get_json()['point']['id'])

        # 批量删除
        response = client.post(
            '/admin/api/points/batch',
            json={'action': 'delete', 'point_ids': point_ids},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data['success'], int)
        assert data['success'] == 3


class TestVizRulesAPI:
    """可视化规则 API 测试"""

    def test_get_rules(self, client):
        """测试获取可视化规则"""
        response = client.get('/admin/api/viz/rules/3')
        assert response.status_code == 200
        data = response.get_json()
        assert 'rules' in data
        assert len(data['rules']) >= 2  # 产业园有 2-3 个规则

    def test_save_rules(self, client):
        """测试保存可视化规则"""
        rules = [
            {
                'rule_name': 'API 测试规则 1',
                'field_key': 'level',
                'rule_type': 'category',
                'config': {'省级': '#16A34A', '市级': '#2563EB'},
                'priority': 1,
                'is_active': True
            },
            {
                'rule_name': 'API 测试规则 2',
                'field_key': 'output',
                'rule_type': 'size',
                'config': {'min': 0, 'max': 10000, 'minSize': 8, 'maxSize': 20},
                'priority': 2,
                'is_active': True
            }
        ]
        response = client.put(
            '/admin/api/layers/3/viz-rules',
            json={'rules': rules},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # 恢复原有规则
        restore_rules = [
            {'rule_name': '按等级着色', 'field_key': 'level', 'rule_type': 'category',
             'config': {'省级': '#16A34A', '市级': '#2563EB', '县级': '#EA580C'},
             'priority': 1, 'is_active': True},
            {'rule_name': '按产值设大小', 'field_key': 'output', 'rule_type': 'size',
             'config': {'min': 0, 'max': 50000, 'minSize': 8, 'maxSize': 24},
             'priority': 2, 'is_active': True},
            {'rule_name': '按产值着色', 'field_key': 'output', 'rule_type': 'color',
             'config': {'stops': [{'value': 0, 'color': '#FEF3C7'}, {'value': 10000, 'color': '#FCD34D'}, {'value': 50000, 'color': '#DC2626'}]},
             'priority': 3, 'is_active': False}
        ]
        client.put('/admin/api/layers/3/viz-rules', json={'rules': restore_rules})


class TestMapAPI:
    """地图服务 API 测试"""

    def test_get_boundary_all(self, client):
        """测试获取所有县边界"""
        response = client.get('/api/boundary/all')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
        assert len(data) >= 3  # 至少有弋阳、万年等县

    def test_get_viz_points(self, client):
        """测试获取带样式的点位"""
        response = client.get('/admin/api/viz/render/3')
        assert response.status_code == 200
        data = response.get_json()
        assert 'points' in data
        assert len(data['points']) > 0
        # 验证点位包含样式
        for point in data['points'][:5]:  # 检查前 5 个
            assert 'style' in point
            assert 'color' in point['style']


class TestAPIErrors:
    """API 错误处理测试"""

    def test_invalid_json(self, client):
        """测试无效 JSON 请求"""
        response = client.post(
            '/admin/api/regions',
            data='invalid json',
            content_type='application/json'
        )
        # Flask 应该返回 400 Bad Request
        assert response.status_code == 400

    def test_not_found(self, client):
        """测试 404 路由"""
        response = client.get('/admin/api/nonexistent')
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """测试方法不允许"""
        response = client.post('/admin/api/regions/1')  # POST 到 detail 路由
        assert response.status_code == 405
