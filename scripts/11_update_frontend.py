"""
更新前端 index.html 添加万年县支持 - 完整版本
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"

# 读取原文件
with open(INDEX_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 更新标题
content = content.replace(
    '<title>弋阳县充换电设施规划地图</title>',
    '<title>弋阳县/万年县充换电设施规划地图</title>'
)

# 2. 更新头部标题
content = content.replace(
    '<h1>🗺️ 弋阳县充换电设施规划地图</h1>',
    '<h1>🗺️ 弋阳县/万年县充换电设施规划地图</h1>'
)

# 3. 添加县域切换器
old_stats = '''<div class="stats" id="headerStats">'''
new_selector = '''<div class="stats" style="display:flex;align-items:center;gap:12px;margin-right:16px">
  <label style="font-size:11px;color:#5a8bb5">选择县域：</label>
  <select id="county-selector" onchange="switchCounty(this.value)" 
    style="padding:4px 8px;border:1px solid #3388cc;border-radius:4px;font-size:11px;background:#fff;color:#1a3a5c;cursor:pointer">
    <option value="yiyang">弋阳县</option>
    <option value="wannian">万年县</option>
    <option value="all">两县联合</option>
  </select>
</div>
<div class="stats" id="headerStats">'''
content = content.replace(old_stats, new_selector)

# 4. 添加全局变量和 switchCounty 函数
old_var = 'var CFG = null;'
new_var = '''var CFG = null;
var CURRENT_COUNTY = 'yiyang';  // 当前选择的县

// 切换县域
function switchCounty(county) {
  CURRENT_COUNTY = county;
  console.log('切换到：', county);
  loadAllData();
}'''
content = content.replace(old_var, new_var)

# 5. 在 fetchJSON 函数后添加 loadAllData 和 clearAllLayers
old_fetch = '''function fetchJSON(url) {
      return fetch(url).then(function (r) {
        if (!r.ok) throw new Error('API 请求失败：' + url + ' (' + r.status + ')');
        return r.json();
      });
    }'''

new_functions = '''function fetchJSON(url) {
      return fetch(url).then(function (r) {
        if (!r.ok) throw new Error('API 请求失败：' + url + ' (' + r.status + ')');
        return r.json();
      });
    }

    // 重新加载所有数据（支持县域切换）
    function loadAllData() {
      console.log('重新加载数据，当前县：', CURRENT_COUNTY);
      clearAllLayers();
      
      Promise.all([
        fetchJSON('/api/boundary?county=' + CURRENT_COUNTY),
        fetchJSON('/api/stations/urban?county=' + CURRENT_COUNTY),
        fetchJSON('/api/stations/gas?county=' + CURRENT_COUNTY),
        fetchJSON('/api/stations/planned?county=' + CURRENT_COUNTY),
        fetchJSON('/api/stats?county=' + CURRENT_COUNTY),
        fetchJSON('/api/townships?county=' + CURRENT_COUNTY)
      ]).then(function(results) {
        var boundary = results[0];
        var urban = results[1];
        var gas = results[2];
        var planned = results[3];
        var stats = results[4];
        var townships = results[5];
        
        console.log('✓ 数据加载完成：', CURRENT_COUNTY);
        console.log('  边界点数:', boundary.count);
        console.log('  充电站:', urban.count, gas.count, planned.count);
        
        BOUNDARY = boundary.boundary || [];
        allPlannedData = planned.stations || [];
        
        var countyName = CURRENT_COUNTY === 'yiyang' ? '弋阳县' : (CURRENT_COUNTY === 'wannian' ? '万年县' : '两县联合');
        document.getElementById('headerStats').innerHTML =
          '现有充电站 <b>' + urban.count + '</b> · 加油站 <b>' + gas.count +
          '</b> · 规划新增 <b>' + planned.count + '</b>';
        
        updateStatsPanel(stats, urban.count, gas.count, planned.count);
        
        if (BOUNDARY && BOUNDARY.length > 0) {
          drawCountyBoundary();
        }
        if (urban.count > 0) plotUrban(urban.stations);
        if (gas.count > 0) plotGas(gas.stations);
        if (planned.count > 0) plotPlan(planned.stations);
        
        if (townships && townships.townships) {
          townshipLabels.forEach(function(lbl) { try { map.removeOverLay(lbl); } catch(e) {} });
          townshipLabels = [];
          addTownshipLabels(townships.townships);
        }
        
        if (CURRENT_COUNTY === 'yiyang') applyCatFilter();
        
      }).catch(function(err) {
        console.error('数据加载失败:', err);
        alert('数据加载失败：' + err.message);
      });
    }

    // 清空所有图层
    function clearAllLayers() {
      console.log('清空图层...');
      ['urban', 'gas', 'plan', 'radius_existing', 'radius_planned'].forEach(function(layer) {
        if (layers[layer]) {
          layers[layer].forEach(function(m) { try { map.removeOverLay(m); } catch(e) {} });
          layers[layer] = [];
        }
      });
      [countyPolygon, maskOverlay, innerFlattener, countyGlow, elevationShadow, countyLabel].forEach(function(obj) {
        if (obj) { try { map.removeOverLay(obj); } catch(e) {} }
      });
    }'''

content = content.replace(old_fetch, new_functions)

# 保存
with open(INDEX_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("✓ 前端更新完成！")
print("  - 添加县域切换下拉框")
print("  - 添加 switchCounty 函数")
print("  - 添加 loadAllData 函数")
print("  - 添加 clearAllLayers 函数")
print("  - API 调用添加 county 参数")
print("\n请刷新浏览器查看效果！")
