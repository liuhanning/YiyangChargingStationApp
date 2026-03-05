# -*- coding: utf-8 -*-
"""生成天地图（支持县域聚光灯效果）"""
import sqlite3, sys, json
sys.stdout.reconfigure(encoding='utf-8')

DB  = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db"
OUT = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\map.html"
KEY = "36c2c7b1a00180d86e97fa8ca2cd3bf2"
BOUNDARY_FILE = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\data\yiyang_boundary.json"

# 读取真实县界数据
try:
    with open(BOUNDARY_FILE, 'r', encoding='utf-8') as f:
        COUNTY_BOUNDARY = json.load(f)
    print(f"✓ 已加载真实县界数据，共 {len(COUNTY_BOUNDARY)} 个坐标点")
except:
    print("⚠ 无法加载县界数据，使用默认边界")
    COUNTY_BOUNDARY = [
        [117.25, 28.25], [117.25, 28.50], [117.60, 28.50],
        [117.60, 28.25], [117.25, 28.25]
    ]

conn = sqlite3.connect(DB)

urban = conn.execute("""
    SELECT station_name, address, longitude, latitude
    FROM stations_urban_coords WHERE longitude IS NOT NULL
""").fetchall()

gas = conn.execute("""
    SELECT station_name, address, has_ev_charger, total_sales, oil_revenue
    FROM gas_stations
""").fetchall()

planned = conn.execute("""
    SELECT station_name, township, scene, quantity, power_kw, year, equipment
    FROM stations_planned WHERE station_name IS NOT NULL
""").fetchall()
conn.close()

urban_js = json.dumps([{
    "name": r[0], "addr": r[1] or "", "lng": r[2], "lat": r[3]
} for r in urban], ensure_ascii=False)

gas_js = json.dumps([{
    "name": r[0],
    "addr": r[1] or "",
    "has_ev": r[2] in ("√","✓","是","有"),
    "sales": r[3] or 0,
    "revenue": r[4] or 0
} for r in gas], ensure_ascii=False)

plan_js = json.dumps([{
    "name": r[0],
    "township": r[1] or "",
    "scene": r[2] or "",
    "qty": int(r[3]) if r[3] else 0,
    "power": int(r[4]) if r[4] else 0,
    "year": int(r[5]) if r[5] else 2026,
    "equip": r[6] or ""
} for r in planned], ensure_ascii=False)

# 县界边界数据
boundary_js = json.dumps(COUNTY_BOUNDARY, ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>弋阳县充换电设施规划地图（天地图）</title>
<script src="http://api.tianditu.gov.cn/api?v=4.0&tk={KEY}"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Microsoft YaHei',Arial,sans-serif;background:#f6f8fa;overflow:hidden}}

#header{{
  height:48px;background:linear-gradient(135deg,#1a6b3c,#0d4d2c);
  color:#fff;padding:0 20px;display:flex;align-items:center;
  justify-content:space-between;border-bottom:2px solid #238636;
  position:relative;z-index:200
}}
#header h1{{font-size:16px;letter-spacing:1px}}
#header p{{font-size:11px;color:#7ee787}}

#map{{width:100%;height:calc(100vh - 48px);position:relative;z-index:1}}

/* 控制面板 */
.control-panel{{
  position:fixed !important;
  top:60px;left:12px;z-index:9999 !important;
  background:rgba(255,255,255,0.98);
  backdrop-filter:blur(6px);
  border:1px solid #d0d7de;
  border-radius:8px;
  padding:10px;
  width:200px;
  box-shadow:0 4px 12px rgba(0,0,0,0.15);
  margin-bottom:10px;
  pointer-events:auto !important;
}}
.panel-title{{
  font-size:11px;color:#57606a;margin-bottom:6px;
  font-weight:600;text-transform:uppercase;letter-spacing:0.5px
}}
.mode-btn{{
  width:100%;padding:8px;margin:4px 0;border:1px solid #d0d7de;
  border-radius:6px;background:#fff;color:#24292f;
  font-size:12px;cursor:pointer;transition:all .2s;
  text-align:left;display:flex;align-items:center;gap:8px
}}
.mode-btn:hover{{background:#f6f8fa;border-color:#1f6feb}}
.mode-btn.active{{background:#ddf4ff;border-color:#1f6feb;color:#0969da}}

.layer-row{{
  display:flex;align-items:center;justify-content:space-between;
  padding:6px 0;border-bottom:1px solid #e1e4e8
}}
.layer-row:last-child{{border-bottom:none}}
.layer-info{{display:flex;align-items:center;gap:7px;font-size:12px;color:#24292f}}
.dot{{width:12px;height:12px;border-radius:50%;flex-shrink:0}}

/* 切换开关 */
.toggle{{position:relative;width:36px;height:20px;flex-shrink:0}}
.toggle input{{opacity:0;width:0;height:0}}
.slider{{
  position:absolute;inset:0;background:#d0d7de;border-radius:20px;
  cursor:pointer;transition:.2s
}}
.slider:before{{
  content:'';position:absolute;width:14px;height:14px;
  background:#fff;border-radius:50%;bottom:3px;left:3px;transition:.2s;
  box-shadow:0 1px 3px rgba(0,0,0,0.2)
}}
input:checked+.slider{{background:var(--c,#3fb950)}}
input:checked+.slider:before{{transform:translateX(16px)}}

/* 信息窗口 */
.info-window{{
  background:#fff;border:1px solid #d0d7de;border-radius:8px;
  padding:12px;min-width:200px;max-width:260px;font-size:12px;
  box-shadow:0 4px 12px rgba(0,0,0,0.15)
}}
.info-title{{font-size:13px;font-weight:bold;color:#24292f;
  border-bottom:1px solid #e1e4e8;padding-bottom:7px;margin-bottom:7px}}
.info-row{{color:#57606a;margin:4px 0;line-height:1.5}}
.info-row b{{color:#24292f}}
.badge{{display:inline-block;padding:1px 7px;border-radius:3px;font-size:11px;margin-top:2px}}
.badge-green{{background:#dafbe1;color:#1a7f37;border:1px solid #4ac26b}}
.badge-blue{{background:#ddf4ff;color:#0969da;border:1px solid #54aeff}}
.badge-orange{{background:#fff8c5;color:#9a6700;border:1px solid #d4a72c}}
</style>
</head>
<body>

<div id="header">
  <div>
    <h1>弋阳县充换电设施规划地图</h1>
    <p>天地图 · 县域聚光灯效果 · 弋阳县全域</p>
  </div>
  <div style="font-size:11px;color:#7ee787;text-align:right">
    现有充电站 16 · 加油站 26 · 规划新增 34<br>
    2026-03-05
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

<!-- 显示模式 -->
<div class="control-panel" style="top:140px">
  <div class="panel-title">显示模式</div>
  <button class="mode-btn active" onclick="setMode('all')">
    <span>🗺️</span>全部显示
  </button>
  <button class="mode-btn" onclick="setMode('boundary')">
    <span>📍</span>仅县域边界
  </button>
  <button class="mode-btn" onclick="setMode('current')">
    <span>⚡</span>现状分析
  </button>
  <button class="mode-btn" onclick="setMode('planning')">
    <span>🔋</span>规划视图
  </button>
</div>

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
var COUNTY_BOUNDARY = {boundary_js};

var map, imageLayer, vectorLayer;
var layers = {{urban:[], gas:[], plan:[]}};
var maskPolygon = null;
var countyPolygon = null;

// 初始化地图
function initMap(){{
  // 创建地图实例
  map = new T.Map('map');
  map.centerAndZoom(new T.LngLat(117.44, 28.37), 12);

  console.log('使用真实县界数据，共 ' + COUNTY_BOUNDARY.length + ' 个坐标点');
  createCountySpotlight(COUNTY_BOUNDARY);

  // 绘制标注点
  plotUrban();
  plotGas();
  plotPlan();
}}

// 切换地图样式
function changeMapStyle(style){{
  // 移除现有图层
  if(imageLayer) map.removeLayer(imageLayer);
  if(vectorLayer) map.removeLayer(vectorLayer);

  if(style === 'satellite'){{
    // 影像地图
    var imageURL = "http://t{{s}}.tianditu.gov.cn/DataServer?T=img_w&x={{x}}&y={{y}}&l={{z}}&tk={KEY}";
    imageLayer = new T.TileLayer(imageURL, {{minZoom:1, maxZoom:18, subdomains:['0','1','2','3','4','5','6','7']}});
    map.addLayer(imageLayer);

    var annoURL = "http://t{{s}}.tianditu.gov.cn/DataServer?T=cia_w&x={{x}}&y={{y}}&l={{z}}&tk={KEY}";
    vectorLayer = new T.TileLayer(annoURL, {{minZoom:1, maxZoom:18, subdomains:['0','1','2','3','4','5','6','7']}});
    map.addLayer(vectorLayer);
  }} else {{
    // 默认矢量地图（天地图会自动显示）
  }}
}}

// 获取弋阳县精确边界
function fetchCountyBoundary(){{
  var url = 'http://api.tianditu.gov.cn/administrative';
  var postStr = JSON.stringify({{
    searchWord: '弋阳县',
    searchType: '1',
    needSubInfo: 'false',
    needAll: 'false',
    needPolygon: 'true',
    needPre: 'false'
  }});

  // 使用JSONP方式调用（避免跨域问题）
  var script = document.createElement('script');
  script.src = url + '?postStr=' + encodeURIComponent(postStr) + '&tk={KEY}&callback=handleBoundaryData';
  document.head.appendChild(script);
}}

// 处理边界数据回调
function handleBoundaryData(data){{
  var countyBounds = [];

  if(data.status === '0' && data.data && data.data.length > 0){{
    var result = data.data[0];
    if(result.polyline){{
      // 解析边界坐标：lng1,lat1;lng2,lat2;...
      var coordsStr = result.polyline;
      var pairs = coordsStr.split(';');
      pairs.forEach(function(pair){{
        if(pair.trim()){{
          var coords = pair.split(',');
          countyBounds.push([parseFloat(coords[0]), parseFloat(coords[1])]);
        }}
      }});
      console.log('成功获取弋阳县边界，共 ' + countyBounds.length + ' 个坐标点');
    }}
  }}

  // 如果获取失败，使用默认边界
  if(countyBounds.length === 0){{
    console.log('使用默认边界');
    countyBounds = [
      [117.25, 28.25], [117.25, 28.50], [117.60, 28.50], [117.60, 28.25], [117.25, 28.25]
    ];
  }}

  // 创建县域聚光灯效果
  createCountySpotlight(countyBounds);
}}

// 创建县域聚光灯效果
function createCountySpotlight(countyBounds){{
  console.log('创建聚光灯效果（Polygon方式），边界点数:', countyBounds.length);

  // 1. 创建大范围遮罩矩形（覆盖周边区域）
  var outerBounds = [
    [116, 27], [119, 27], [119, 30], [116, 30], [116, 27]
  ];

  var maskPoints = outerBounds.map(function(p){{ return new T.LngLat(p[0], p[1]); }});
  maskPolygon = new T.Polygon(maskPoints, {{
    color: '#000000',
    weight: 0,
    opacity: 0,
    fillColor: '#000000',
    fillOpacity: 0.7
  }});
  map.addOverLay(maskPolygon);
  console.log('✓ 遮罩层创建完成');

  // 2. 创建县域高亮多边形（覆盖在遮罩层之上）
  var countyPoints = countyBounds.map(function(p){{ return new T.LngLat(p[0], p[1]); }});
  countyPolygon = new T.Polygon(countyPoints, {{
    color: '#0066cc',
    weight: 2.5,
    opacity: 1,
    fillColor: '#66b3ff',
    fillOpacity: 0.35
  }});
  map.addOverLay(countyPolygon);
  console.log('✓ 县域多边形创建完成');

  // 3. 自适应视图到县域边界
  map.setViewport(countyPoints);
  console.log('✓ 聚光灯效果创建完成');
}}

// 绘制现有充电站
function plotUrban(){{
  URBAN.forEach(function(d){{
    var marker = new T.Marker(new T.LngLat(d.lng, d.lat), {{
      icon: createIcon('#3fb950', '⚡', 22)
    }});
    marker.addEventListener('click', function(){{
      var infoWin = new T.InfoWindow();
      infoWin.setContent(
        '<div class="info-window">' +
        '<div class="info-title">⚡ ' + d.name + '</div>' +
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

// 绘制加油站
function plotGas(){{
  GAS.forEach(function(d){{
    // 简化：使用县城中心附近随机位置（实际需要地理编码）
    var lng = 117.44 + (Math.random() - 0.5) * 0.2;
    var lat = 28.37 + (Math.random() - 0.5) * 0.2;

    var marker = new T.Marker(new T.LngLat(lng, lat), {{
      icon: createIcon('#f0883e', '⛽', 20)
    }});
    marker.addEventListener('click', function(){{
      var infoWin = new T.InfoWindow();
      infoWin.setContent(
        '<div class="info-window">' +
        '<div class="info-title">⛽ ' + d.name + '</div>' +
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

// 绘制规划充电站
function plotPlan(){{
  PLAN.forEach(function(d){{
    // 简化：使用县城中心附近随机位置（实际需要地理编码）
    var lng = 117.44 + (Math.random() - 0.5) * 0.2;
    var lat = 28.37 + (Math.random() - 0.5) * 0.2;

    var marker = new T.Marker(new T.LngLat(lng, lat), {{
      icon: createIcon('#58a6ff', '🔋', 20)
    }});
    marker.addEventListener('click', function(){{
      var infoWin = new T.InfoWindow();
      infoWin.setContent(
        '<div class="info-window">' +
        '<div class="info-title">🔋 ' + d.name + '</div>' +
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
  if(maskPolygon && countyPolygon){{
    if(show){{
      map.addOverLay(maskPolygon);
      map.addOverLay(countyPolygon);
    }} else {{
      map.removeOverLay(maskPolygon);
      map.removeOverLay(countyPolygon);
    }}
  }}
}}

// 设置显示模式
function setMode(mode){{
  document.querySelectorAll('.mode-btn').forEach(function(btn){{
    btn.classList.remove('active');
  }});
  event.target.closest('.mode-btn').classList.add('active');

  var checkboxes = document.querySelectorAll('.toggle input[type="checkbox"]');

  switch(mode){{
    case 'all':
      toggleLayer('urban', true);
      toggleLayer('gas', true);
      toggleLayer('plan', true);
      toggleBoundary(true);
      checkboxes[0].checked = true;
      checkboxes[1].checked = true;
      checkboxes[2].checked = true;
      checkboxes[3].checked = true;
      break;
    case 'boundary':
      toggleLayer('urban', false);
      toggleLayer('gas', false);
      toggleLayer('plan', false);
      toggleBoundary(true);
      checkboxes[0].checked = false;
      checkboxes[1].checked = false;
      checkboxes[2].checked = false;
      checkboxes[3].checked = true;
      break;
    case 'current':
      toggleLayer('urban', true);
      toggleLayer('gas', false);
      toggleLayer('plan', false);
      toggleBoundary(true);
      checkboxes[0].checked = true;
      checkboxes[1].checked = false;
      checkboxes[2].checked = false;
      checkboxes[3].checked = true;
      break;
    case 'planning':
      toggleLayer('urban', false);
      toggleLayer('gas', false);
      toggleLayer('plan', true);
      toggleBoundary(true);
      checkboxes[0].checked = false;
      checkboxes[1].checked = false;
      checkboxes[2].checked = true;
      checkboxes[3].checked = true;
      break;
  }}
}}

// 页面加载完成后初始化地图
window.onload = initMap;
</script>
</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print("天地图生成:", OUT)
