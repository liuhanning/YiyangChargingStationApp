"""
地图渲染模块
负责生成天地图交互式地图
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from config import (
    MAP_API, COUNTY_INFO, COUNTY_BOUNDARY_DEFAULT,
    STYLE_CONFIG, EXPORT_CONFIG, DISPLAY_MODES, OUTPUT_DIR
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MapRenderer:
    """地图渲染器"""

    def __init__(self):
        """初始化渲染器"""
        self.tianditu_key = MAP_API["tianditu"]["key"]
        self.county_center = COUNTY_INFO["center"]
        self.county_name = COUNTY_INFO["name"]

    def render_map(self, data: Dict, output_path: Optional[Path] = None) -> str:
        """
        渲染交互式地图

        Args:
            data: 包含所有数据的字典
            output_path: 输出文件路径

        Returns:
            生成的HTML文件路径
        """
        if output_path is None:
            output_path = OUTPUT_DIR / EXPORT_CONFIG["html"]["filename"]

        # 准备数据
        urban_js = json.dumps(data.get("urban_stations", []), ensure_ascii=False)
        gas_js = json.dumps(data.get("gas_stations", []), ensure_ascii=False)
        plan_js = json.dumps(data.get("planned_stations", []), ensure_ascii=False)

        # 生成HTML
        html = self._generate_html(urban_js, gas_js, plan_js)

        # 写入文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"✓ 地图生成: {output_path}")
        return str(output_path)

    def _generate_html(self, urban_js: str, gas_js: str, plan_js: str) -> str:
        """生成HTML内容"""

        # 获取样式配置
        boundary_style = STYLE_CONFIG["county_boundary"]
        mask_style = STYLE_CONFIG["spotlight_mask"]
        station_style = STYLE_CONFIG["station_existing"]
        gas_style = STYLE_CONFIG["gas_station"]
        plan_style = STYLE_CONFIG["station_planned"]

        # 提取具体的样式值
        boundary_stroke_color = boundary_style["stroke_color"]
        boundary_stroke_width = boundary_style["stroke_width"]
        boundary_fill_color = boundary_style["fill_color"]
        boundary_fill_opacity = boundary_style["fill_opacity"]

        mask_fill_color = mask_style["fill_color"]
        mask_fill_opacity = mask_style["fill_opacity"]

        station_color = station_style["color"]
        station_icon = station_style["icon"]
        station_size = station_style["size"]

        gas_color = gas_style["color"]
        gas_icon = gas_style["icon"]
        gas_size = gas_style["size"]

        plan_color = plan_style["color"]
        plan_icon = plan_style["icon"]
        plan_size = plan_style["size"]

        # 获取统计数据
        urban_count = len(json.loads(urban_js))
        gas_count = len(json.loads(gas_js))
        plan_count = len(json.loads(plan_js))

        # 县域中心坐标
        center_lng = self.county_center[0]
        center_lat = self.county_center[1]

        # 当前日期
        today = datetime.now().strftime("%Y-%m-%d")

        # 县域边界默认值
        boundary_default = json.dumps(COUNTY_BOUNDARY_DEFAULT)

        # 显示模式配置
        display_modes_json = json.dumps({k: v['layers'] for k, v in DISPLAY_MODES.items()})

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{EXPORT_CONFIG["html"]["title"]}</title>
<script src="http://api.tianditu.gov.cn/api?v=4.0&tk={self.tianditu_key}"></script>
<style>
* {{box-sizing:border-box;margin:0;padding:0}}
body {{font-family:'Microsoft YaHei',Arial,sans-serif;background:#f6f8fa;overflow:hidden}}

#header {{
  height:48px;background:linear-gradient(135deg,#1a6b3c,#0d4d2c);
  color:#fff;padding:0 20px;display:flex;align-items:center;
  justify-content:space-between;border-bottom:2px solid #238636;
  position:relative;z-index:200
}}
#header h1 {{font-size:16px;letter-spacing:1px}}
#header p {{font-size:11px;color:#7ee787}}

#map {{width:100%;height:calc(100vh - 48px)}}

/* 控制面板 */
.control-panel {{
  position:absolute;left:12px;z-index:150;
  background:rgba(255,255,255,0.95);backdrop-filter:blur(6px);
  border:1px solid #d0d7de;border-radius:8px;padding:10px;width:200px;
  box-shadow:0 2px 8px rgba(0,0,0,0.1);margin-bottom:10px
}}
.panel-title {{
  font-size:11px;color:#57606a;margin-bottom:6px;
  font-weight:600;text-transform:uppercase;letter-spacing:0.5px
}}
.mode-btn {{
  width:100%;padding:8px;margin:4px 0;border:1px solid #d0d7de;
  border-radius:6px;background:#fff;color:#24292f;
  font-size:12px;cursor:pointer;transition:all .2s;
  text-align:left;display:flex;align-items:center;gap:8px
}}
.mode-btn:hover {{background:#f6f8fa;border-color:#1f6feb}}
.mode-btn.active {{background:#ddf4ff;border-color:#1f6feb;color:#0969da}}

.layer-row {{
  display:flex;align-items:center;justify-content:space-between;
  padding:6px 0;border-bottom:1px solid #e1e4e8
}}
.layer-row:last-child {{border-bottom:none}}
.layer-info {{display:flex;align-items:center;gap:7px;font-size:12px;color:#24292f}}
.dot {{width:12px;height:12px;border-radius:50%;flex-shrink:0}}

/* 切换开关 */
.toggle {{position:relative;width:36px;height:20px;flex-shrink:0}}
.toggle input {{opacity:0;width:0;height:0}}
.slider {{
  position:absolute;inset:0;background:#d0d7de;border-radius:20px;
  cursor:pointer;transition:.2s
}}
.slider:before {{
  content:'';position:absolute;width:14px;height:14px;
  background:#fff;border-radius:50%;bottom:3px;left:3px;transition:.2s;
  box-shadow:0 1px 3px rgba(0,0,0,0.2)
}}
input:checked+.slider {{background:var(--c,#3fb950)}}
input:checked+.slider:before {{transform:translateX(16px)}}

/* 信息窗口 */
.info-window {{
  background:#fff;border:1px solid #d0d7de;border-radius:8px;
  padding:12px;min-width:200px;max-width:260px;font-size:12px;
  box-shadow:0 4px 12px rgba(0,0,0,0.15)
}}
.info-title {{font-size:13px;font-weight:bold;color:#24292f;
  border-bottom:1px solid #e1e4e8;padding-bottom:7px;margin-bottom:7px}}
.info-row {{color:#57606a;margin:4px 0;line-height:1.5}}
.info-row b {{color:#24292f}}
.badge {{display:inline-block;padding:1px 7px;border-radius:3px;font-size:11px;margin-top:2px}}
.badge-green {{background:#dafbe1;color:#1a7f37;border:1px solid #4ac26b}}
.badge-blue {{background:#ddf4ff;color:#0969da;border:1px solid #54aeff}}
.badge-orange {{background:#fff8c5;color:#9a6700;border:1px solid #d4a72c}}
</style>
</head>
<body>

<div id="header">
  <div>
    <h1>{self.county_name}充换电设施规划地图</h1>
    <p>天地图 · 县域聚光灯效果 · {self.county_name}全域</p>
  </div>
  <div style="font-size:11px;color:#7ee787;text-align:right">
    现有充电站 {urban_count} · 加油站 {gas_count} · 规划新增 {plan_count}<br>
    {today}
  </div>
</div>

<div id="map"></div>

<!-- 地图样式选择 -->
<div class="control-panel" style="top:60px">
  <div class="panel-title">地图样式</div>
  <select onchange="changeMapStyle(this.value)" style="width:100%;padding:6px;border:1px solid #d0d7de;border-radius:6px;font-size:12px">
    <option value="standard">标准地图</option>
    <option value="satellite">卫星影像</option>
  </select>
</div>

<!-- 显示模式选择 -->
<div class="control-panel" style="top:140px">
  <div class="panel-title">显示模式</div>
"""

        # 添加显示模式按钮
        for mode_id, mode_config in DISPLAY_MODES.items():
            active_class = "active" if mode_id == "all" else ""
            html += f"""  <button class="mode-btn {active_class}" onclick="setMode('{mode_id}')">
    <span>{mode_config['icon']}</span>{mode_config['name']}
  </button>
"""

        html += """</div>

<!-- 图层控制 -->
<div class="control-panel" style="top:360px">
  <div class="panel-title">图层控制</div>
  <div class="layer-row">
    <div class="layer-info">
      <div class="dot" style="background:#3fb950"></div>
      现有充电站
    </div>
    <label class="toggle" style="--c:#3fb950">
      <input type="checkbox" checked onchange="toggleLayer('urban',this.checked)">
      <span class="slider"></span>
    </label>
  </div>
  <div class="layer-row">
    <div class="layer-info">
      <div class="dot" style="background:#f0883e"></div>
      加油站
    </div>
    <label class="toggle" style="--c:#f0883e">
      <input type="checkbox" checked onchange="toggleLayer('gas',this.checked)">
      <span class="slider"></span>
    </label>
  </div>
  <div class="layer-row">
    <div class="layer-info">
      <div class="dot" style="background:#58a6ff"></div>
      规划充电站
    </div>
    <label class="toggle" style="--c:#58a6ff">
      <input type="checkbox" checked onchange="toggleLayer('plan',this.checked)">
      <span class="slider"></span>
    </label>
  </div>
  <div class="layer-row">
    <div class="layer-info">
      <div class="dot" style="background:#58a6ff;border-radius:2px"></div>
      县域边界
    </div>
    <label class="toggle" style="--c:#58a6ff">
      <input type="checkbox" checked onchange="toggleBoundary(this.checked)">
      <span class="slider"></span>
    </label>
  </div>
</div>

<script>
var URBAN = {urban_js};
var GAS   = {gas_js};
var PLAN  = {plan_js};

var map, imageLayer, vectorLayer;
var layers = {{urban:[], gas:[], plan:[]}};
var spotlightOverlay = null;

// 初始化地图
function initMap(){{
  map = new T.Map('map');
  map.centerAndZoom(new T.LngLat({center_lng}, {center_lat}), 12);

  // 先用固定边界测试聚光灯效果
  var testBoundary = {boundary_default};

  console.log('开始创建聚光灯效果...');
  createCountySpotlight(testBoundary);

  // 绘制标注点
  plotUrban();
  plotGas();
  plotPlan();
}}

// 创建县域聚光灯效果（使用SVG）
function createCountySpotlight(countyBounds){{
  console.log('创建SVG聚光灯效果，边界点数:', countyBounds.length);

  // 创建SVG叠加层
  spotlightOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  spotlightOverlay.setAttribute('id', 'spotlight-overlay');
  spotlightOverlay.style.position = 'absolute';
  spotlightOverlay.style.top = '0';
  spotlightOverlay.style.left = '0';
  spotlightOverlay.style.width = '100%';
  spotlightOverlay.style.height = '100%';
  spotlightOverlay.style.pointerEvents = 'none';
  spotlightOverlay.style.zIndex = '50';

  // 创建defs定义遮罩
  var defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  var mask = document.createElementNS('http://www.w3.org/2000/svg', 'mask');
  mask.setAttribute('id', 'county-mask');

  // 白色背景（遮罩区域）
  var maskBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  maskBg.setAttribute('width', '100%');
  maskBg.setAttribute('height', '100%');
  maskBg.setAttribute('fill', 'white');
  mask.appendChild(maskBg);

  // 黑色县域区域（透明区域）
  var maskPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  maskPath.setAttribute('fill', 'black');
  mask.appendChild(maskPath);

  defs.appendChild(mask);
  spotlightOverlay.appendChild(defs);

  // 创建遮罩矩形
  var maskRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  maskRect.setAttribute('width', '100%');
  maskRect.setAttribute('height', '100%');
  maskRect.setAttribute('fill', '{mask_fill_color}');
  maskRect.setAttribute('fill-opacity', '{mask_fill_opacity}');
  maskRect.setAttribute('mask', 'url(#county-mask)');
  spotlightOverlay.appendChild(maskRect);

  // 创建县域边界线
  var boundaryPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  boundaryPath.setAttribute('fill', '{boundary_fill_color}');
  boundaryPath.setAttribute('fill-opacity', '{boundary_fill_opacity}');
  boundaryPath.setAttribute('stroke', '{boundary_stroke_color}');
  boundaryPath.setAttribute('stroke-width', '{boundary_stroke_width}');
  spotlightOverlay.appendChild(boundaryPath);

  // 添加到地图容器
  document.getElementById('map').appendChild(spotlightOverlay);

  // 更新路径函数
  function updatePaths(){{
    var pathData = 'M ';
    var maskPathData = 'M ';

    countyBounds.forEach(function(point, index){{
      var pixel = map.lngLatToContainerPixel(new T.LngLat(point[0], point[1]));
      var cmd = index === 0 ? 'M ' : 'L ';
      pathData += cmd + pixel.x + ' ' + pixel.y + ' ';
      maskPathData += cmd + pixel.x + ' ' + pixel.y + ' ';
    }});

    pathData += 'Z';
    maskPathData += 'Z';

    boundaryPath.setAttribute('d', pathData);
    maskPath.setAttribute('d', maskPathData);
  }}

  // 初始更新
  updatePaths();

  // 地图移动或缩放时更新
  map.addEventListener('moveend', updatePaths);
  map.addEventListener('zoomend', updatePaths);

  console.log('SVG聚光灯效果创建完成');

  // 自适应视图
  var countyPoints = countyBounds.map(function(p){{ return new T.LngLat(p[0], p[1]); }});
  map.setViewport(countyPoints);
}}

// 绘制现有充电站
function plotUrban(){{
  URBAN.forEach(function(d){{
    var marker = new T.Marker(new T.LngLat(d.lng, d.lat), {{
      icon: createIcon('{station_color}', '{station_icon}', {station_size})
    }});
    marker.addEventListener('click', function(){{
      var infoWin = new T.InfoWindow();
      infoWin.setContent(
        '<div class="info-window">' +
        '<div class="info-title">{station_icon} ' + d.name + '</div>' +
        '<div class="info-row">地址：<b>' + d.addr + '</b></div>' +
        '<div class="info-row"><span class="badge badge-green">已建成运营</span></div>' +
        '</div>'
      );
      infoWin.setLngLat(new T.LngLat(d.lng, d.lat));
      map.openInfoWindow(infoWin);
    }});
    map.addOverLay(marker);
    layers.urban.push(marker);
  }});
}}

// 绘制加油站（模拟坐标）
function plotGas(){{
  GAS.forEach(function(d){{
    var lng = {center_lng} + (Math.random() - 0.5) * 0.2;
    var lat = {center_lat} + (Math.random() - 0.5) * 0.2;

    var marker = new T.Marker(new T.LngLat(lng, lat), {{
      icon: createIcon('{gas_color}', '{gas_icon}', {gas_size})
    }});
    marker.addEventListener('click', function(){{
      var infoWin = new T.InfoWindow();
      infoWin.setContent(
        '<div class="info-window">' +
        '<div class="info-title">{gas_icon} ' + d.name + '</div>' +
        '<div class="info-row">地址：<b>' + d.addr + '</b></div>' +
        '<div class="info-row">年销量：<b>' + d.sales + ' 吨</b></div>' +
        '<div class="info-row"><span class="badge ' + (d.has_ev ? 'badge-green' : 'badge-orange') + '">' +
        (d.has_ev ? '已有充电设施' : '待改造升级') + '</span></div>' +
        '</div>'
      );
      infoWin.setLngLat(new T.LngLat(lng, lat));
      map.openInfoWindow(infoWin);
    }});
    map.addOverLay(marker);
    layers.gas.push(marker);
  }});
}}

// 绘制规划充电站（模拟坐标）
function plotPlan(){{
  PLAN.forEach(function(d){{
    var lng = {center_lng} + (Math.random() - 0.5) * 0.2;
    var lat = {center_lat} + (Math.random() - 0.5) * 0.2;

    var marker = new T.Marker(new T.LngLat(lng, lat), {{
      icon: createIcon('{plan_color}', '{plan_icon}', {plan_size})
    }});
    marker.addEventListener('click', function(){{
      var infoWin = new T.InfoWindow();
      infoWin.setContent(
        '<div class="info-window">' +
        '<div class="info-title">{plan_icon} ' + d.name + '</div>' +
        '<div class="info-row">乡镇：<b>' + d.township + '</b>　场景：<b>' + d.scene + '</b></div>' +
        '<div class="info-row">桩数：<b>' + d.qty + ' 台</b>　功率：<b>' + d.power + ' kW</b></div>' +
        '<div class="info-row"><span class="badge badge-green">' + d.year + ' 年建设</span></div>' +
        '</div>'
      );
      infoWin.setLngLat(new T.LngLat(lng, lat));
      map.openInfoWindow(infoWin);
    }});
    map.addOverLay(marker);
    layers.plan.push(marker);
  }});
}}

// 创建自定义图标
function createIcon(color, text, size){{
  var icon = new T.Icon({{
    iconUrl: 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="' + (size+4) + '" height="' + (size+4) + '">' +
      '<circle cx="' + (size/2+2) + '" cy="' + (size/2+2) + '" r="' + (size/2+2) + '" fill="' + color + '" stroke="white" stroke-width="2"/>' +
      '<text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="' + Math.floor(size*0.6) + '" fill="white">' + text + '</text>' +
      '</svg>'
    ),
    iconSize: new T.Point(size+4, size+4),
    iconAnchor: new T.Point((size+4)/2, (size+4)/2)
  }});
  return icon;
}}

// 切换图层显示
function toggleLayer(name, show){{
  layers[name].forEach(function(marker){{
    if(show){{
      map.addOverLay(marker);
    }} else {{
      map.removeOverLay(marker);
    }}
  }});
}}

// 切换边界显示
function toggleBoundary(show){{
  if(spotlightOverlay){{
    spotlightOverlay.style.display = show ? 'block' : 'none';
  }}
}}

// 切换地图样式
function changeMapStyle(style){{
  // 暂未实现
  console.log('切换地图样式:', style);
}}

// 设置显示模式
function setMode(mode){{
  document.querySelectorAll('.mode-btn').forEach(function(btn){{
    btn.classList.remove('active');
  }});
  event.target.closest('.mode-btn').classList.add('active');

  var checkboxes = document.querySelectorAll('.toggle input[type="checkbox"]');
  var modes = {display_modes_json};
  var layers_to_show = modes[mode] || [];

  toggleLayer('urban', layers_to_show.includes('urban'));
  toggleLayer('gas', layers_to_show.includes('gas'));
  toggleLayer('plan', layers_to_show.includes('plan'));
  toggleBoundary(layers_to_show.includes('boundary'));

  checkboxes[0].checked = layers_to_show.includes('urban');
  checkboxes[1].checked = layers_to_show.includes('gas');
  checkboxes[2].checked = layers_to_show.includes('plan');
  checkboxes[3].checked = layers_to_show.includes('boundary');
}}

// 页面加载完成后初始化地图
window.onload = initMap;
</script>
</body>
</html>"""

        return html


# 测试代码
if __name__ == "__main__":
    from data_loader import DataLoader

    # 加载数据
    loader = DataLoader()
    data = loader.load_all_data()

    # 渲染地图
    renderer = MapRenderer()
    output_path = renderer.render_map(data)

    print(f"\n✓ 地图已生成: {output_path}")
    print(f"  请在浏览器中打开查看")
