"""
直接在 index.html 中添加 loadAllData 函数
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

INDEX_FILE = Path(__file__).parent.parent / "frontend" / "index.html"

# 读取文件
with open(INDEX_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 找到 fetchJSON 函数的结束位置（第 1045 行左右，函数结束的大括号）
insert_line = None
for i, line in enumerate(lines):
    if "function loadScript(src)" in line:
        insert_line = i
        break

if insert_line is None:
    print("✗ 未找到插入位置")
    sys.exit(1)

# 要插入的代码
new_code = '''    // 重新加载所有数据（支持县域切换）
    function loadAllData() {
      console.log('切换县域：', CURRENT_COUNTY);
      clearAllLayers();
      Promise.all([
        fetchJSON('/api/boundary?county=' + CURRENT_COUNTY),
        fetchJSON('/api/stations/urban?county=' + CURRENT_COUNTY),
        fetchJSON('/api/stations/gas?county=' + CURRENT_COUNTY),
        fetchJSON('/api/stations/planned?county=' + CURRENT_COUNTY),
        fetchJSON('/api/stats?county=' + CURRENT_COUNTY),
        fetchJSON('/api/townships?county=' + CURRENT_COUNTY)
      ]).then(function(results) {
        var boundary = results[0], urban = results[1], gas = results[2],
            planned = results[3], stats = results[4], townships = results[5];
        console.log('✓', CURRENT_COUNTY, '边界:', boundary.count, '充电站:', urban.count, gas.count, planned.count);
        BOUNDARY = boundary.boundary || [];
        document.getElementById('headerStats').innerHTML = '充电站 <b>' + urban.count + '</b> 加油站 <b>' + gas.count + '</b> 规划 <b>' + planned.count + '</b>';
        updateStatsPanel(stats, urban.count, gas.count, planned.count);
        if (BOUNDARY.length > 0) drawCountyBoundary();
        if (urban.count > 0) plotUrban(urban.stations);
        if (gas.count > 0) plotGas(gas.stations);
        if (planned.count > 0) plotPlan(planned.stations);
        if (townships && townships.townships) addTownshipLabels(townships.townships);
      }).catch(function(err) { console.error('✗', err); });
    }

    // 清空图层
    function clearAllLayers() {
      ['urban','gas','plan','radius_existing','radius_planned'].forEach(function(l) {
        if (layers[l]) { layers[l].forEach(function(m) { try{map.removeOverLay(m);}catch(e){} }); layers[l]=[]; }
      });
      [countyPolygon,maskOverlay,innerFlattener,countyGlow,elevationShadow,countyLabel].forEach(function(o){
        if(o){try{map.removeOverLay(o);}catch(e){}}
      });
      if(townshipLabels){townshipLabels.forEach(function(l){try{map.removeOverLay(l);}catch(e){}}); townshipLabels=[];}
    }

'''

# 插入代码
lines.insert(insert_line, new_code)

# 保存文件
with open(INDEX_FILE, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("✓ 已添加 loadAllData 和 clearAllLayers 函数")
print("  插入位置：第", insert_line+1, "行")
print("\n请刷新浏览器测试切换功能！")
