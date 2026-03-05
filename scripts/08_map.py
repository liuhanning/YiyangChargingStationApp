# -*- coding: utf-8 -*-
"""生成天地图（支持县域聚光灯效果）"""
import sqlite3, sys, json
sys.stdout.reconfigure(encoding='utf-8')

DB  = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db"
OUT = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\map.html"
KEY = "36c2c7b1a00180d86e97fa8ca2cd3bf2"  # 天地图 Key

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

# 加油站：优先用详细地址，不够精确的补上乡镇名
gas_search_hint = {
    "城南加油站":       "弋阳县南岩镇志敏大道城南加油站",
    "第八加油站":       "弋阳县圭峰镇莲塘岗320国道加油站",
    "第五加油站":       "弋阳县南岩镇下湖村加油站",
    "第六加油站":       "弋阳县圭峰镇汤家山加油站",
    "叠山加油站":       "弋阳县叠山镇加油站",
    "箭竹加油站":       "弋阳县圭峰镇坝头村加油站",
    "漆工加油站":       "弋阳县漆工镇老瓦山加油站",
    "第七加油站":       "弋阳县圭峰镇桐子岭加油站",
    "志敏加油站":       "弋阳县志敏大道加油站",
    "中畈加油站":       "弋阳县中畈乡政府旁加油站",
    "湾里加油站":       "弋阳县湾里乡葛家村加油站",
    "南岩加油站":       "弋阳县南岩镇311国道加油站",
    "长源加油站":       "弋阳县漆工镇乐姜公路加油站",
    "海螺加油站":       "弋阳县三县岭镇205省道海螺加油站",
    "工业园区加油站":   "弋阳县弋阳大道展望大道工业园区加油站",
    "上万高速挂线加油站": "弋阳县上万高速弋阳东收费站加油站",
    "徐家垅加油站":     "弋阳县乐江大道徐家垅水库加油站",
    "江西高速石化有限责任公司上万高速弋阳服务区西加油站": "弋阳县葛溪乡上万高速弋阳服务区",
    "江西高速石化有限责任公司上万高速弋阳服务区东加油站": "弋阳县葛溪乡上万高速弋阳服务区",
    "中石油上饶弋阳沪昆挂线加油站": "弋阳县沪昆高速新出口挂线公路加油站",
    "中石油上饶弋阳江浙加油站":     "弋阳县南岩镇光辉村加油站",
    "中石油上饶弋阳花亭慧丰加油站": "弋阳县花亭乡弋漆公路加油站",
    "弋阳县曹溪镇加油站":   "弋阳县曹溪镇曹溪村加油站",
    "弋阳县弋乐加油站（个人独资）": "弋阳县中畈乡扎马山加油站",
    "弋阳县顺风加油站":     "弋阳县曹溪镇邵畈加油站",
    "弋阳县烈桥加油站":     "弋阳县烈桥加油站",
}

plan_search_hint = {
    "***县***镇小康路，行政服务中心": "弋阳县行政服务中心",
    "西街停车场一":    "弋阳县西街",
    "西街停车场二":    "弋阳县西街",
    "西街停车场三":    "弋阳县西街",
    "大桥洞以北两侧":  "弋阳县大桥洞",
    "乐江首府以北":    "弋阳县乐江首府",
    "东鑫公馆以东":    "弋阳县东鑫公馆",
    "式平路边停车场（湾里路）": "弋阳县式平路",
    "老财政局平面停车场":      "弋阳县财政局",
    "老社保局平面停车场（方格尔停车场）": "弋阳县人力资源和社会保障局",
    "长卿路北街社区旁（方格尔停车场）":  "弋阳县长卿路",
    "杨桥路方格尔停车场（中国银行对面）":"弋阳县杨桥路中国银行",
    "滨江公园洲上公园平面停车场": "弋阳县滨江公园",
    "府前社区方志敏公园（广和明月苑）": "弋阳县方志敏公园",
    "建岭社区菜场小区": "弋阳县建岭社区",
    "桃源街道淝塘岗小区": "弋阳县桃源街道",
    "桃源街道双停社区":   "弋阳县桃源街道",
    "桃源街道居委会":     "弋阳县桃源街道居委会",
    "新材料产业园内":     "弋阳县三县岭新材料产业园",
    "广场社区办公楼旁停车场": "弋阳县广场社区",
    "信江生态新天地南侧停车场": "弋阳县信江新天地",
    "南岩镇政府旁11号楼停车场": "弋阳县南岩镇人民政府",
    "南岩镇镇府大院内":       "弋阳县南岩镇人民政府",
    "府前社区新洲商博城":     "弋阳县新洲商博城",
    "东投学仕府小区旁公共停车场": "弋阳县东投学仕府",
    "弋阳县现代农业示范区（葛河之心）": "弋阳县花亭乡现代农业示范区",
}

def gas_search(name, addr):
    if name in gas_search_hint:
        return gas_search_hint[name]
    if addr and len(addr) > 4:
        return ("江西省上饶市弋阳县" + addr) if "弋阳" not in addr else addr
    return "弋阳县" + name

def plan_search(name, township):
    if name in plan_search_hint:
        return plan_search_hint[name]
    return f"弋阳县{township or ''}{name}"

urban_js = json.dumps([{
    "name": r[0], "addr": r[1] or "", "lng": r[2], "lat": r[3]
} for r in urban], ensure_ascii=False)

gas_js = json.dumps([{
    "name": r[0],
    "search": gas_search(r[0], r[1]),
    "addr": r[1] or "",
    "has_ev": r[2] in ("√","✓","是","有"),
    "sales": r[3] or 0,
    "revenue": r[4] or 0
} for r in gas], ensure_ascii=False)

plan_js = json.dumps([{
    "name": r[0],
    "search": plan_search(r[0], r[1]),
    "township": r[1] or "",
    "scene": r[2] or "",
    "qty": int(r[3]) if r[3] else 0,
    "power": int(r[4]) if r[4] else 0,
    "year": int(r[5]) if r[5] else 2026,
    "equip": r[6] or ""
} for r in planned], ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>弋阳县充换电设施规划地图</title>
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

#map{{width:100%;height:calc(100vh - 48px)}}

/* 地图样式选择器 */
#style-selector{{
  position:absolute;top:60px;left:12px;z-index:150;
  background:rgba(255,255,255,0.95);backdrop-filter:blur(6px);
  border:1px solid #d0d7de;border-radius:8px;padding:10px;width:200px;
  box-shadow:0 2px 8px rgba(0,0,0,0.1)
}}
.style-label{{
  font-size:11px;color:#57606a;margin-bottom:6px;
  font-weight:600;text-transform:uppercase;letter-spacing:0.5px
}}
#mapStyleSelect{{
  width:100%;padding:8px 10px;border:1px solid #d0d7de;
  border-radius:6px;background:#fff;color:#24292f;
  font-size:13px;cursor:pointer;transition:all .2s;
  font-family:'Microsoft YaHei',Arial,sans-serif
}}
#mapStyleSelect:hover{{border-color:#1f6feb}}
#mapStyleSelect:focus{{outline:none;border-color:#1f6feb;box-shadow:0 0 0 3px rgba(31,111,235,0.1)}}

/* 显示模式选择器 */
#mode-selector{{
  position:absolute;top:150px;left:12px;z-index:150;
  background:rgba(255,255,255,0.95);backdrop-filter:blur(6px);
  border:1px solid #d0d7de;border-radius:8px;padding:10px;width:200px;
  box-shadow:0 2px 8px rgba(0,0,0,0.1)
}}
.mode-btn{{
  width:100%;padding:8px;margin:4px 0;border:1px solid #d0d7de;
  border-radius:6px;background:#fff;color:#24292f;
  font-size:12px;cursor:pointer;transition:all .2s;
  text-align:left;display:flex;align-items:center;gap:8px
}}
.mode-btn:hover{{background:#f6f8fa;border-color:#1f6feb}}
.mode-btn.active{{background:#ddf4ff;border-color:#1f6feb;color:#0969da}}
.mode-icon{{font-size:14px;width:18px;text-align:center}}

/* 图层控制面板 */
#ctrl{{
  position:absolute;top:390px;left:12px;z-index:150;
  background:rgba(255,255,255,0.95);backdrop-filter:blur(6px);
  border:1px solid #d0d7de;border-radius:8px;padding:10px;width:200px;
  box-shadow:0 2px 8px rgba(0,0,0,0.1)
}}
.ctrl-title{{font-size:11px;color:#57606a;margin-bottom:8px;
  font-weight:600;text-transform:uppercase;letter-spacing:0.5px}}
.layer-row{{
  display:flex;align-items:center;justify-content:space-between;
  padding:6px 0;border-bottom:1px solid #e1e4e8
}}
.layer-row:last-child{{border-bottom:none}}
.layer-info{{display:flex;align-items:center;gap:7px;font-size:12px;color:#24292f}}
.dot{{width:12px;height:12px;border-radius:50%;flex-shrink:0}}
.cnt{{font-size:10px;color:#57606a;margin-left:2px}}

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

/* 加载进度 */
#loading{{
  position:absolute;top:60px;right:12px;z-index:150;
  background:rgba(255,255,255,0.95);backdrop-filter:blur(6px);
  border:1px solid #d0d7de;border-radius:8px;
  padding:10px 14px;font-size:12px;color:#57606a;min-width:180px;
  box-shadow:0 2px 8px rgba(0,0,0,0.1)
}}
#loading .prog-row{{display:flex;justify-content:space-between;margin:3px 0}}
.prog-bar{{width:100%;height:3px;background:#e1e4e8;border-radius:2px;margin-top:6px}}
.prog-fill{{height:100%;background:#3fb950;border-radius:2px;transition:width .3s}}

/* 信息窗口 */
.iw{{background:#fff;border:1px solid #d0d7de;border-radius:8px;
  padding:12px;min-width:200px;max-width:260px;font-size:12px;
  box-shadow:0 4px 12px rgba(0,0,0,0.15)}}
.iw-title{{font-size:13px;font-weight:bold;color:#24292f;
  border-bottom:1px solid #e1e4e8;padding-bottom:7px;margin-bottom:7px}}
.iw-row{{color:#57606a;margin:4px 0;line-height:1.5}}
.iw-row b{{color:#24292f}}
.badge{{display:inline-block;padding:1px 7px;border-radius:3px;font-size:11px;margin-top:2px}}
.badge-green{{background:#dafbe1;color:#1a7f37;border:1px solid #4ac26b}}
.badge-blue{{background:#ddf4ff;color:#0969da;border:1px solid #54aeff}}
.badge-orange{{background:#fff8c5;color:#9a6700;border:1px solid #d4a72c}}
.warn{{color:#57606a;font-size:10px;margin-top:4px}}

/* 弋阳边界标注 */
.amap-info-close{{color:#8b949e!important;font-size:16px!important}}
</style>
</head>
<body>

<div id="header">
  <div>
    <h1>弋阳县充换电设施规划地图</h1>
    <p>卫星影像 · 三层数据叠加 · 弋阳县全域</p>
  </div>
  <div style="font-size:11px;color:#7ee787;text-align:right">
    现有充电站 16 · 加油站 26 · 规划新增 34<br>
    2026-03-05
  </div>
</div>

<div id="map"></div>

<!-- 地图样式选择 -->
<div id="style-selector">
  <div class="style-label">地图样式</div>
  <select id="mapStyleSelect" onchange="changeMapStyle(this.value)">
    <option value="standard">标准（白天）</option>
    <option value="satellite">卫星影像</option>
    <option value="dark">深色模式</option>
  </select>
</div>

<!-- 显示模式选择 -->
<div id="mode-selector">
  <div class="style-label">显示模式</div>
  <button class="mode-btn active" onclick="setMode('all')">
    <span class="mode-icon">🗺️</span>全部显示
  </button>
  <button class="mode-btn" onclick="setMode('boundary')">
    <span class="mode-icon">📍</span>仅县域边界
  </button>
  <button class="mode-btn" onclick="setMode('current')">
    <span class="mode-icon">⚡</span>现状分析
  </button>
  <button class="mode-btn" onclick="setMode('planning')">
    <span class="mode-icon">🔋</span>规划视图
  </button>
  <button class="mode-btn" onclick="setMode('gas')">
    <span class="mode-icon">⛽</span>加油站分布
  </button>
</div>

<!-- 图层控制 -->
<div id="ctrl">
  <div class="ctrl-title">图层控制</div>
  <div class="layer-row">
    <div class="layer-info">
      <div class="dot" style="background:#3fb950"></div>
      现有充电站<span class="cnt" id="c1">16</span>
    </div>
    <label class="toggle" style="--c:#3fb950">
      <input type="checkbox" checked onchange="toggleLayer('urban',this.checked)">
      <span class="slider"></span>
    </label>
  </div>
  <div class="layer-row">
    <div class="layer-info">
      <div class="dot" style="background:#f0883e"></div>
      加油站<span class="cnt" id="c2">0/26</span>
    </div>
    <label class="toggle" style="--c:#f0883e">
      <input type="checkbox" checked onchange="toggleLayer('gas',this.checked)">
      <span class="slider"></span>
    </label>
  </div>
  <div class="layer-row">
    <div class="layer-info">
      <div class="dot" style="background:#58a6ff"></div>
      规划充电站<span class="cnt" id="c3">0/34</span>
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
      <input type="checkbox" checked onchange="toggleBound(this.checked)">
      <span class="slider"></span>
    </label>
  </div>
</div>

<!-- 加载进度 -->
<div id="loading">
  <div style="color:#24292f;font-size:12px;margin-bottom:6px">⏳ 正在定位标注...</div>
  <div class="prog-row"><span>⛽ 加油站</span><span id="pg1">0/26</span></div>
  <div class="prog-row"><span>🔋 规划站</span><span id="pg2">0/34</span></div>
  <div class="prog-bar"><div class="prog-fill" id="pb" style="width:0%"></div></div>
</div>

<script>
var URBAN = {urban_js};
var GAS   = {gas_js};
var PLAN  = {plan_js};

var map, geocoder, infoWin;
var layers = {{urban:[], gas:[], plan:[]}};
var boundPoly = null;
var doneGas=0, donePlan=0;
var mapLayers = {{
  standard: null,
  satellite: null,
  roadnet: null
}};

function updateProgress(){{
  var total = GAS.length + PLAN.length;
  var done  = doneGas + donePlan;
  document.getElementById('pb').style.width = (done/total*100)+'%';
  document.getElementById('pg1').textContent = doneGas+'/'+GAS.length;
  document.getElementById('pg2').textContent = donePlan+'/'+PLAN.length;
  document.getElementById('c2').textContent  = doneGas+'/'+GAS.length;
  document.getElementById('c3').textContent  = donePlan+'/'+PLAN.length;
  if(done >= total){{
    setTimeout(function(){{
      document.getElementById('loading').innerHTML =
        '<span style="color:#3fb950">✓ 全部标注完成</span>';
    }}, 800);
  }}
}}

function initMap(){{
  // 初始化图层
  mapLayers.standard = new AMap.TileLayer();
  mapLayers.satellite = new AMap.TileLayer.Satellite();
  mapLayers.roadnet = new AMap.TileLayer.RoadNet();

  // 默认使用标准地图
  map = new AMap.Map('map', {{
    zoom: 11,
    center: [117.44, 28.37],
    layers: [mapLayers.standard],
    resizeEnable: true,
    zooms: [9, 18],
  }});

  infoWin = new AMap.InfoWindow({{isCustom:true, closeWhenClickMap:true, offset:new AMap.Pixel(0,-30)}});

  var maskRects = [];
  var countyPolys = [];

  // 绘制弋阳县行政边界
  AMap.plugin('AMap.DistrictSearch', function(){{
    var dist = new AMap.DistrictSearch({{subdistrict:0, extensions:'all', level:'district'}});
    dist.search('弋阳县', function(status, result){{
      if(status==='complete' && result.districtList && result.districtList[0]){{
        var bounds = result.districtList[0].boundaries;
        if(bounds && bounds.length > 0){{

          // 获取县域的外接矩形范围
          var minLng = 180, maxLng = -180, minLat = 90, maxLat = -90;
          bounds.forEach(function(boundary){{
            boundary.forEach(function(point){{
              minLng = Math.min(minLng, point.lng);
              maxLng = Math.max(maxLng, point.lng);
              minLat = Math.min(minLat, point.lat);
              maxLat = Math.max(maxLat, point.lat);
            }});
          }});

          // 创建4个大矩形遮罩，覆盖县域周边区域
          // 北侧遮罩
          maskRects.push(new AMap.Rectangle({{
            bounds: new AMap.Bounds([114, maxLat], [120, 31]),
            strokeWeight: 0,
            fillColor: '#000000',
            fillOpacity: 0.7,
            map: map
          }}));

          // 南侧遮罩
          maskRects.push(new AMap.Rectangle({{
            bounds: new AMap.Bounds([114, 26], [120, minLat]),
            strokeWeight: 0,
            fillColor: '#000000',
            fillOpacity: 0.7,
            map: map
          }}));

          // 西侧遮罩
          maskRects.push(new AMap.Rectangle({{
            bounds: new AMap.Bounds([114, minLat], [minLng, maxLat]),
            strokeWeight: 0,
            fillColor: '#000000',
            fillOpacity: 0.7,
            map: map
          }}));

          // 东侧遮罩
          maskRects.push(new AMap.Rectangle({{
            bounds: new AMap.Bounds([maxLng, minLat], [120, maxLat]),
            strokeWeight: 0,
            fillColor: '#000000',
            fillOpacity: 0.7,
            map: map
          }}));

          // 绘制县域多边形（浅蓝色填充 + 蓝色描边）
          countyPolys = bounds.map(function(b){{
            return new AMap.Polygon({{
              path: b,
              strokeColor: '#0066cc',
              strokeWeight: 2.5,
              strokeStyle: 'solid',
              fillColor: '#66b3ff',
              fillOpacity: 0.25,
              map: map
            }});
          }});

          boundPoly = maskRects.concat(countyPolys);

          // 自适应边界
          map.setFitView(countyPolys, false, [60,60,60,60]);
        }}
      }}
    }});
  }});

  AMap.plugin('AMap.Geocoder', function(){{
    geocoder = new AMap.Geocoder({{city:'弋阳县', radius:20000}});
    plotUrban();
    batchGeocode(GAS, plotGas, function(){{ doneGas++; updateProgress(); }}, 80);
    batchGeocode(PLAN, plotPlan, function(){{ donePlan++; updateProgress(); }}, 60);
  }});
}}

// ── 批量编码（队列，避免并发限制）──────────────────────
function batchGeocode(arr, plotFn, onDone, delayMs){{
  arr.forEach(function(item, idx){{
    setTimeout(function(){{
      geocoder.getLocation(item.search, function(status, result){{
        if(status==='complete' && result.geocodes && result.geocodes.length>0){{
          var loc = result.geocodes[0].location;
          plotFn(item, loc.getLng(), loc.getLat(), false);
        }} else {{
          // 二次尝试：只用名称
          var fallback = item.name.replace(/[（(].*$/,'').trim();
          geocoder.getLocation('弋阳县'+fallback, function(s2,r2){{
            if(s2==='complete' && r2.geocodes && r2.geocodes.length>0){{
              var loc2 = r2.geocodes[0].location;
              plotFn(item, loc2.getLng(), loc2.getLat(), false);
            }} else {{
              plotFn(item, null, null, true); // 编码失败，标记警告
            }}
            onDone();
          }});
          return; // 等二次回调
        }}
        onDone();
      }});
    }}, idx * delayMs);
  }});
}}

// ── 城区充电站（精确坐标）────────────────────────────
function plotUrban(){{
  URBAN.forEach(function(d){{
    var m = makeMarker([d.lng,d.lat], iconHTML('#3fb950','⚡',22));
    m.on('click', function(){{
      infoWin.setContent(
        `<div class="iw">
          <div class="iw-title">⚡ ${{d.name}}</div>
          <div class="iw-row">地址：<b>${{d.addr}}</b></div>
          <div class="iw-row">坐标：<b>${{d.lng.toFixed(5)}}, ${{d.lat.toFixed(5)}}</b></div>
          <div class="iw-row"><span class="badge badge-green">已建成运营</span></div>
        </div>`
      );
      infoWin.open(map,[d.lng,d.lat]);
    }});
    layers.urban.push(m);
  }});
}}

// ── 加油站 ────────────────────────────────────────────
function plotGas(d, lng, lat, failed){{
  if(failed || !lng) return; // 编码完全失败的不画占位
  var color = d.has_ev ? '#ffa657' : '#f0883e';
  var icon  = d.has_ev ? '⛽✓' : '⛽';
  var m = makeMarker([lng,lat], iconHTML(color,'⛽',20));
  m.on('click', function(){{
    infoWin.setContent(
      `<div class="iw">
        <div class="iw-title">⛽ ${{d.name}}</div>
        <div class="iw-row">地址：<b>${{d.addr||d.search}}</b></div>
        <div class="iw-row">年销量：<b>${{d.sales}} 吨</b></div>
        ${{d.revenue?'<div class="iw-row">油品收入：<b>'+d.revenue+'万元</b></div>':''}}
        <div class="iw-row">充电设施：
          <span class="badge ${{d.has_ev?'badge-green':'badge-orange'}}">
            ${{d.has_ev?'已有充电设施':'待改造升级'}}
          </span>
        </div>
      </div>`
    );
    infoWin.open(map,[lng,lat]);
  }});
  layers.gas.push(m);
}}

// ── 规划充电站 ────────────────────────────────────────
function plotPlan(d, lng, lat, failed){{
  if(failed || !lng) return;
  var m = makeMarker([lng,lat], iconHTML('#58a6ff','🔋',20));
  m.on('click', function(){{
    infoWin.setContent(
      `<div class="iw">
        <div class="iw-title">🔋 ${{d.name}}</div>
        <div class="iw-row">乡镇：<b>${{d.township}}</b>　场景：<b>${{d.scene}}</b></div>
        <div class="iw-row">桩数：<b>${{d.qty}} 台</b>　功率：<b>${{d.power}} kW</b></div>
        <div class="iw-row">配电：<b>${{d.equip||'—'}}</b></div>
        <div class="iw-row">
          <span class="badge ${{d.year===2026?'badge-green':'badge-blue'}}">
            ${{d.year}} 年建设
          </span>
        </div>
      </div>`
    );
    infoWin.open(map,[lng,lat]);
  }});
  layers.plan.push(m);
}}

// ── 工具函数 ─────────────────────────────────────────
function makeMarker(pos, content){{
  var m = new AMap.Marker({{
    position: pos,
    content: content,
    offset: new AMap.Pixel(-13,-13),
    map: map
  }});
  return m;
}}

function iconHTML(color, icon, size){{
  return `<div style="
    width:${{size+4}}px;height:${{size+4}}px;border-radius:50%;
    background:${{color}};border:2px solid rgba(255,255,255,0.85);
    display:flex;align-items:center;justify-content:center;
    font-size:${{Math.floor(size*0.65)}}px;
    box-shadow:0 2px 8px rgba(0,0,0,0.6);cursor:pointer;
    transition:transform .15s;
  " onmouseover="this.style.transform='scale(1.35)'"
     onmouseout="this.style.transform='scale(1)'">${{icon}}</div>`;
}}

function toggleLayer(name, show){{
  layers[name].forEach(function(m){{ show?m.show():m.hide(); }});
}}

function toggleBound(show){{
  if(!boundPoly) return;
  boundPoly.forEach(function(p){{ show?p.show():p.hide(); }});
}}

// ── 显示模式切换 ─────────────────────────────────────
function setMode(mode){{
  // 更新按钮状态
  document.querySelectorAll('.mode-btn').forEach(function(btn){{
    btn.classList.remove('active');
  }});
  event.target.closest('.mode-btn').classList.add('active');

  // 根据模式显示/隐藏图层
  switch(mode){{
    case 'all': // 全部显示
      toggleLayer('urban', true);
      toggleLayer('gas', true);
      toggleLayer('plan', true);
      toggleBound(true);
      updateCheckboxes(true, true, true, true);
      break;
    case 'boundary': // 仅县域边界
      toggleLayer('urban', false);
      toggleLayer('gas', false);
      toggleLayer('plan', false);
      toggleBound(true);
      updateCheckboxes(false, false, false, true);
      break;
    case 'current': // 现状分析（现有充电站+边界）
      toggleLayer('urban', true);
      toggleLayer('gas', false);
      toggleLayer('plan', false);
      toggleBound(true);
      updateCheckboxes(true, false, false, true);
      break;
    case 'planning': // 规划视图（规划站点+边界）
      toggleLayer('urban', false);
      toggleLayer('gas', false);
      toggleLayer('plan', true);
      toggleBound(true);
      updateCheckboxes(false, false, true, true);
      break;
    case 'gas': // 加油站分布（加油站+边界）
      toggleLayer('urban', false);
      toggleLayer('gas', true);
      toggleLayer('plan', false);
      toggleBound(true);
      updateCheckboxes(false, true, false, true);
      break;
  }}
}}

function updateCheckboxes(urban, gas, plan, bound){{
  var checkboxes = document.querySelectorAll('#ctrl input[type="checkbox"]');
  checkboxes[0].checked = urban;
  checkboxes[1].checked = gas;
  checkboxes[2].checked = plan;
  checkboxes[3].checked = bound;
}}

// ── 地图样式切换 ─────────────────────────────────────
function changeMapStyle(style){{
  // 移除所有图层
  map.remove([mapLayers.standard, mapLayers.satellite, mapLayers.roadnet]);

  // 根据选择添加对应图层
  switch(style){{
    case 'standard':
      map.add(mapLayers.standard);
      break;
    case 'satellite':
      map.add([mapLayers.satellite, mapLayers.roadnet]);
      break;
    case 'dark':
      map.setMapStyle('amap://styles/dark');
      map.add(mapLayers.standard);
      break;
  }}
}}
</script>

<script src="https://webapi.amap.com/maps?v=2.0&key={KEY}&callback=initMap"></script>
</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print("地图生成:", OUT)
