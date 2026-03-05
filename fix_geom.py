import geopandas as gpd
import json
import warnings
warnings.filterwarnings('ignore')

shp = r'c:\Users\lhn\OneDrive\Desktop\江西\弋阳县_行政区划\弋阳县_行政区划\弋阳县_乡镇边界.shp'
out_path = r'c:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\data\yiyang_townships.geojson'

# engine='fiona' may be more robust than pyogrio for these shapes
try:
    gdf = gpd.read_file(shp, engine='fiona')
except Exception as e:
    print("fiona failed:", e)
    gdf = gpd.read_file(shp)

print("CRS:", gdf.crs)
print("Rows:", len(gdf))

# Ensure geometry is valid
if not gdf.crs:
    gdf.set_crs(epsg=4326, inplace=True)
elif gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs(epsg=4326)

gdf['geometry'] = gdf.geometry.make_valid()

for i, row in gdf.iterrows():
    name = row.get("DistName", "?")
    geom = row.geometry
    if geom:
        print(f"{i}: {name} type={geom.geom_type}")
    else:
        print(f"{i}: {name} None")

# Drop any None geometries
gdf = gdf[gdf.geometry.notna()]

gdf.to_file(out_path, driver='GeoJSON')
print(f"Saved to {out_path}")
