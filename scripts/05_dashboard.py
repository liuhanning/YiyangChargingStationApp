# -*- coding: utf-8 -*-
"""
弋阳县充电桩规划 - 可视化仪表盘
生成一个独立的 HTML 文件，包含多个交互图表
"""
import sqlite3, os, sys, json
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

DB = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db"
OUT = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\dashboard.html"

conn = sqlite3.connect(DB)

# ── 辅助函数 ─────────────────────────────────────────────
def ni(v):
    """安全转int，NaN返回'-'"""
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return '-'
        return str(int(float(v)))
    except:
        return '-'

def nf(v, dec=0):
    """安全转float，NaN返回'-'"""
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return '-'
        return f"{float(v):.{dec}f}"
    except:
        return '-'

def ns(v):
    """安全转字符串，NaN返回'-'"""
    if v is None: return '-'
    s = str(v).strip()
    return '-' if s in ('nan','None','') else s

# ── 读取数据 ─────────────────────────────────────────────
eco = pd.read_sql("SELECT * FROM economic_stats WHERE region='弋阳' ORDER BY year", conn)
existing = pd.read_sql("""
    SELECT township, SUM(quantity) as total FROM stations_existing_township GROUP BY township
""", conn)
status25 = pd.read_sql("SELECT * FROM stations_status_2025", conn)
coords = pd.read_sql("SELECT * FROM stations_urban_coords WHERE longitude IS NOT NULL", conn)
planned = pd.read_sql("SELECT * FROM stations_planned WHERE station_name IS NOT NULL", conn)
gas = pd.read_sql("SELECT * FROM gas_stations", conn)
conn.close()

# ── 统计 ─────────────────────────────────────────────────
total_existing = int(existing['total'].sum())
total_planned_2026 = int(planned[planned['year']==2026]['quantity'].sum() or 0)
total_planned_all  = int(planned['quantity'].sum() or 0)
total_power_planned = float(planned['power_kw'].sum() or 0)
gas_total = len(gas)
gas_with_ev = int((gas['has_ev_charger'].isin(['√','✓','是','有'])).sum())

# 规划按年分组
plan_by_year = planned.groupby('year')['quantity'].sum().reset_index().dropna()
plan_by_scene = planned.groupby('scene')['quantity'].sum().reset_index().dropna()
plan_by_township = planned.groupby('township')['quantity'].sum().reset_index().dropna()

# 现状按场景
scene25 = status25.groupby('scene')['quantity'].sum().reset_index().dropna()
scene25 = scene25[scene25['scene'] != 'None']

# 经济趋势
eco_nev = eco[eco['nev_total'].notna()][['year','nev_total','car_total','gdp']].copy()

# JSON序列化辅助
def jd(df, cols):
    return {c: df[c].tolist() for c in cols if c in df.columns}

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>弋阳县充电桩规划数据仪表盘</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Microsoft YaHei',Arial,sans-serif;background:#0d1117;color:#e6edf3}}
  .header{{background:linear-gradient(135deg,#1a6b3c 0%,#0d4d2c 100%);padding:24px 32px;border-bottom:2px solid #238636}}
  .header h1{{font-size:24px;font-weight:700;letter-spacing:2px}}
  .header p{{font-size:13px;color:#7ee787;margin-top:6px}}
  .kpi-row{{display:flex;gap:16px;padding:20px 32px;flex-wrap:wrap}}
  .kpi{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px 24px;flex:1;min-width:160px;text-align:center}}
  .kpi .val{{font-size:36px;font-weight:700;color:#58a6ff}}
  .kpi .lbl{{font-size:12px;color:#8b949e;margin-top:4px}}
  .kpi .sub{{font-size:11px;color:#3fb950;margin-top:2px}}
  .grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;padding:0 32px 16px}}
  .grid-3{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;padding:0 32px 16px}}
  .card{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px}}
  .card h3{{font-size:13px;color:#8b949e;margin-bottom:12px;border-bottom:1px solid #21262d;padding-bottom:8px}}
  .chart{{width:100%;height:320px}}
  .chart-tall{{width:100%;height:400px}}
  .full-card{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;margin:0 32px 16px}}
  .table-wrap{{overflow-x:auto;margin-top:8px}}
  table{{width:100%;border-collapse:collapse;font-size:12px}}
  th{{background:#21262d;color:#8b949e;padding:8px 12px;text-align:left;border-bottom:1px solid #30363d}}
  td{{padding:7px 12px;border-bottom:1px solid #21262d;color:#c9d1d9}}
  tr:hover td{{background:#1c2128}}
  .tag{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px}}
  .tag-green{{background:#1a3a1a;color:#3fb950;border:1px solid #238636}}
  .tag-blue{{background:#0d2035;color:#58a6ff;border:1px solid #1f6feb}}
  .tag-orange{{background:#2d1b00;color:#f0883e;border:1px solid #9e6a03}}
  footer{{text-align:center;padding:20px;font-size:11px;color:#484f58}}
</style>
</head>
<body>
<div class="header">
  <h1>弋阳县充换电设施规划数据仪表盘</h1>
  <p>数据来源：弋阳县充换电申报材料 · 生成时间：2026-03-05</p>
</div>

<!-- KPI 卡片 -->
<div class="kpi-row">
  <div class="kpi"><div class="val">{total_existing}</div><div class="lbl">现有充电桩（台）</div><div class="sub">覆盖 {len(existing)} 个乡镇</div></div>
  <div class="kpi"><div class="val">{total_planned_2026}</div><div class="lbl">2026年规划新增（台）</div><div class="sub">正在申报建设</div></div>
  <div class="kpi"><div class="val">{total_planned_all}</div><div class="lbl">2026-2028规划总量（台）</div><div class="sub">总功率 {total_power_planned:.0f} kW</div></div>
  <div class="kpi"><div class="val">{gas_total}</div><div class="lbl">加油站总数（座）</div><div class="sub">其中 {gas_with_ev} 座已有充电设施</div></div>
  <div class="kpi"><div class="val">{eco_nev['nev_total'].iloc[-1]:.4f}<span style="font-size:16px">万辆</span></div><div class="lbl">新能源车保有量（2025）</div><div class="sub">全县汽车 {eco_nev['car_total'].iloc[-1]:.3f} 万辆</div></div>
  <div class="kpi"><div class="val">203.94<span style="font-size:16px">亿</span></div><div class="lbl">GDP（2025年）</div><div class="sub">常住人口约 32.94 万人</div></div>
</div>

<!-- 图表行1 -->
<div class="grid">
  <div class="card">
    <h3>📈 弋阳县历年新能源车 & 汽车保有量趋势</h3>
    <div id="chart_eco" class="chart"></div>
  </div>
  <div class="card">
    <h3>🏘️ 各乡镇现有充电桩数量分布</h3>
    <div id="chart_township" class="chart"></div>
  </div>
</div>

<!-- 图表行2 -->
<div class="grid">
  <div class="card">
    <h3>📅 2026-2028规划充电桩 - 按年度 & 乡镇分布</h3>
    <div id="chart_plan_year" class="chart"></div>
  </div>
  <div class="card">
    <h3>🏷️ 规划充电桩应用场景分布</h3>
    <div id="chart_scene" class="chart"></div>
  </div>
</div>

<!-- 图表行3 -->
<div class="grid-3">
  <div class="card">
    <h3>💰 弋阳县历年GDP增长</h3>
    <div id="chart_gdp" class="chart"></div>
  </div>
  <div class="card">
    <h3>⛽ 加油站改造潜力（是否有充电设施）</h3>
    <div id="chart_gas" class="chart"></div>
  </div>
  <div class="card">
    <h3>🔌 现状充电设施应用场景（2025年）</h3>
    <div id="chart_scene25" class="chart"></div>
  </div>
</div>

<!-- 城区充电站地图占位（坐标表格） -->
<div class="full-card">
  <h3>📍 城区充电站坐标信息（16座，已对接高德地图格式）</h3>
  <div class="table-wrap">
    <table>
      <tr><th>#</th><th>场站名称</th><th>详细地址</th><th>高德经度</th><th>高德纬度</th></tr>
      {"".join(f"<tr><td>{i+1}</td><td>{r['station_name']}</td><td>{r['address'] or '-'}</td><td>{r['longitude']}</td><td>{r['latitude']}</td></tr>" for i, r in coords.iterrows())}
    </table>
  </div>
</div>

<!-- 规划清单详情表 -->
<div class="full-card">
  <h3>📋 2026-2028年充电站规划清单（{len(planned)} 个站点）</h3>
  <div class="table-wrap">
    <table>
      <tr><th>乡镇</th><th>年度</th><th>场景</th><th>站点名称</th><th>桩数（台）</th><th>功率（kW）</th><th>设备容量</th></tr>
      {"".join(f'''<tr>
        <td>{ns(r['township'])}</td>
        <td><span class="tag {'tag-green' if r['year']==2026 else 'tag-blue' if r['year']==2027 else 'tag-orange'}">{ni(r['year'])}</span></td>
        <td>{ns(r['scene'])}</td>
        <td>{ns(r['station_name'])}</td>
        <td style="text-align:center;font-weight:bold;color:#58a6ff">{ni(r['quantity'])}</td>
        <td style="text-align:center">{ni(r['power_kw'])}</td>
        <td style="font-size:11px;color:#8b949e">{ns(r['equipment'])}</td>
      </tr>''' for _, r in planned.iterrows())}
    </table>
  </div>
</div>

<!-- 加油站详情表 -->
<div class="full-card">
  <h3>⛽ 弋阳县加油站详情（2024年，共 {gas_total} 座）</h3>
  <div class="table-wrap">
    <table>
      <tr><th>加油站名称</th><th>地址</th><th>位置类型</th><th>汽油(吨)</th><th>柴油(吨)</th><th>合计(吨)</th><th>储油(m³)</th><th>有充电设施</th><th>油品收入(万元)</th></tr>
      {"".join(f'''<tr>
        <td>{ns(r['station_name'])}</td>
        <td style="font-size:11px">{ns(r['address'])}</td>
        <td style="font-size:11px">{ns(r['location_type'])}</td>
        <td style="text-align:right">{nf(r['petrol_sales'])}</td>
        <td style="text-align:right">{nf(r['diesel_sales'])}</td>
        <td style="text-align:right;font-weight:bold">{nf(r['total_sales'])}</td>
        <td style="text-align:right">{nf(r['storage_cap'])}</td>
        <td style="text-align:center">{"<span class='tag tag-green'>已有</span>" if r['has_ev_charger'] in ('√','✓','是','有') else "<span style='color:#484f58'>—</span>"}</td>
        <td style="text-align:right">{nf(r['oil_revenue'])}</td>
      </tr>''' for _, r in gas.iterrows())}
    </table>
  </div>
</div>

<footer>弋阳县充换电设施规划项目 · 数据整理版本 v1.0 · 2026-03-05</footer>

<script>
// ── 图1：新能源车趋势 ─────────────────────────────────
var c1 = echarts.init(document.getElementById('chart_eco'));
c1.setOption({{
  tooltip:{{trigger:'axis'}},
  legend:{{data:['汽车保有量(万辆)','新能源车保有量(万辆)'],textStyle:{{color:'#8b949e'}}}},
  grid:{{top:40,bottom:40,left:50,right:20}},
  xAxis:{{type:'category',data:{json.dumps(eco_nev['year'].tolist())},axisLabel:{{color:'#8b949e'}}}},
  yAxis:[
    {{type:'value',name:'汽车保有量',axisLabel:{{color:'#8b949e',formatter:'{{value}}'}},splitLine:{{lineStyle:{{color:'#21262d'}}}}}},
    {{type:'value',name:'新能源',axisLabel:{{color:'#8b949e',formatter:'{{value}}'}},splitLine:{{show:false}}}}
  ],
  series:[
    {{name:'汽车保有量(万辆)',type:'bar',data:{json.dumps(eco_nev['car_total'].tolist())},
      itemStyle:{{color:'#1f6feb'}}}},
    {{name:'新能源车保有量(万辆)',type:'line',yAxisIndex:1,
      data:{json.dumps(eco_nev['nev_total'].tolist())},
      itemStyle:{{color:'#3fb950'}},lineStyle:{{width:3}},symbol:'circle',symbolSize:8}}
  ]
}});

// ── 图2：各乡镇充电桩 ─────────────────────────────────
var c2 = echarts.init(document.getElementById('chart_township'));
var twn_data = {json.dumps(list(zip(existing['township'].tolist(), existing['total'].tolist())))};
twn_data.sort((a,b)=>b[1]-a[1]);
c2.setOption({{
  tooltip:{{trigger:'axis',axisPointer:{{type:'shadow'}}}},
  grid:{{top:20,bottom:70,left:60,right:20}},
  xAxis:{{type:'category',data:twn_data.map(d=>d[0]),axisLabel:{{color:'#8b949e',rotate:30}}}},
  yAxis:{{type:'value',axisLabel:{{color:'#8b949e'}},splitLine:{{lineStyle:{{color:'#21262d'}}}}}},
  series:[{{
    type:'bar',data:twn_data.map(d=>d[1]),
    itemStyle:{{color:function(p){{
      var c=['#58a6ff','#3fb950','#f0883e','#a371f7','#ff7b72','#ffa657','#79c0ff'];
      return c[p.dataIndex%c.length];
    }}}},
    label:{{show:true,position:'top',color:'#e6edf3',fontSize:11}}
  }}]
}});

// ── 图3：规划桩数量 按年度 & 乡镇 ────────────────────
var c3 = echarts.init(document.getElementById('chart_plan_year'));
var planData = {json.dumps(list(zip(plan_by_township['township'].tolist(), plan_by_township['quantity'].tolist())))};
planData.sort((a,b)=>b[1]-a[1]);
c3.setOption({{
  tooltip:{{trigger:'axis',axisPointer:{{type:'shadow'}}}},
  grid:{{top:20,bottom:70,left:60,right:20}},
  xAxis:{{type:'category',data:planData.map(d=>d[0]),axisLabel:{{color:'#8b949e',rotate:30}}}},
  yAxis:{{type:'value',axisLabel:{{color:'#8b949e'}},splitLine:{{lineStyle:{{color:'#21262d'}}}}}},
  series:[{{
    type:'bar',data:planData.map(d=>d[1]),
    itemStyle:{{color:'#a371f7'}},
    label:{{show:true,position:'top',color:'#e6edf3',fontSize:11}}
  }}]
}});

// ── 图4：规划应用场景饼图 ─────────────────────────────
var c4 = echarts.init(document.getElementById('chart_scene'));
c4.setOption({{
  tooltip:{{trigger:'item',formatter:'{{b}}: {{c}}台 ({{d}}%)'}},
  legend:{{orient:'vertical',left:'left',textStyle:{{color:'#8b949e',fontSize:11}}}},
  series:[{{
    type:'pie',radius:['35%','70%'],center:['60%','50%'],
    data:{json.dumps([{"name": str(r['scene']), "value": int(r['quantity'])} for _, r in plan_by_scene.iterrows() if r['scene'] and r['scene'] != 'None'])},
    itemStyle:{{borderColor:'#0d1117',borderWidth:2}},
    label:{{color:'#e6edf3',fontSize:11}}
  }}]
}});

// ── 图5：GDP折线 ──────────────────────────────────────
var eco_gdp = {json.dumps(eco[eco['gdp'].notna()][['year','gdp']].values.tolist())};
var c5 = echarts.init(document.getElementById('chart_gdp'));
c5.setOption({{
  tooltip:{{trigger:'axis',formatter:params=>params[0].name+'年: '+params[0].value+'亿元'}},
  grid:{{top:20,bottom:40,left:60,right:20}},
  xAxis:{{type:'category',data:eco_gdp.map(d=>d[0]),axisLabel:{{color:'#8b949e'}}}},
  yAxis:{{type:'value',axisLabel:{{color:'#8b949e',formatter:'{{value}}亿'}},splitLine:{{lineStyle:{{color:'#21262d'}}}}}},
  series:[{{
    type:'line',data:eco_gdp.map(d=>d[1]),
    itemStyle:{{color:'#f0883e'}},lineStyle:{{width:3}},
    areaStyle:{{color:{{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{{offset:0,color:'rgba(240,136,62,0.4)'}},{{offset:1,color:'rgba(240,136,62,0)'}}]}}}},
    symbol:'circle',symbolSize:6
  }}]
}});

// ── 图6：加油站改造饼图 ──────────────────────────────
var c6 = echarts.init(document.getElementById('chart_gas'));
c6.setOption({{
  tooltip:{{trigger:'item',formatter:'{{b}}: {{c}}座 ({{d}}%)'}},
  series:[{{
    type:'pie',radius:'70%',
    data:[
      {{value:{gas_with_ev},name:'已有充电设施',itemStyle:{{color:'#3fb950'}}}},
      {{value:{gas_total - gas_with_ev},name:'待改造升级',itemStyle:{{color:'#484f58'}}}}
    ],
    label:{{color:'#e6edf3',formatter:'{{b}}\\n{{c}}座'}},
    itemStyle:{{borderColor:'#0d1117',borderWidth:2}}
  }}]
}});

// ── 图7：现状应用场景 ─────────────────────────────────
var c7 = echarts.init(document.getElementById('chart_scene25'));
var s25 = {json.dumps([{"name": str(r['scene']), "value": int(r['quantity'])} for _, r in scene25.iterrows() if r['scene'] and r['scene'] not in ('None', 'nan')])};
c7.setOption({{
  tooltip:{{trigger:'item',formatter:'{{b}}: {{c}}台 ({{d}}%)'}},
  series:[{{
    type:'pie',radius:['30%','65%'],
    data:s25,
    itemStyle:{{borderColor:'#0d1117',borderWidth:2}},
    label:{{color:'#e6edf3',fontSize:10}}
  }}]
}});

// 响应式
window.addEventListener('resize',function(){{
  [c1,c2,c3,c4,c5,c6,c7].forEach(c=>c.resize());
}});
</script>
</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"仪表盘已生成：{OUT}")
print(f"文件大小：{os.path.getsize(OUT)/1024:.1f} KB")
