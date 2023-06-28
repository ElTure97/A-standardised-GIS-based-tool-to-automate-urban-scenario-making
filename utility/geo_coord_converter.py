from shapely import wkb
from shapely.geometry import MultiPolygon
import geopandas as gpd
import json
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from shapely.geometry import Point

with open("config/ding0_config.json", "r") as f:
    ding0_data = json.load(f)
exa_str = ding0_data["MV_district_geom"]

wkb_data = bytes.fromhex(exa_str)
# decode WKB
multipolygon = wkb.loads(wkb_data)

found_cities = []

geolocator = Nominatim(user_agent="my_app")

for polygon in multipolygon.geoms:
    for point in polygon.exterior.coords:
        p = Point(point[0], point[1])

        location = geolocator.reverse([p.y, p.x], exactly_one=True)

        if location:
            city = location.raw.get('address', {}).get('city')
            zone = location.raw.get('address', {}).get('suburb')


            if city:
                if city not in found_cities:
                    found_cities.append(city)
            elif zone:
                if zone not in found_cities:
                    found_cities.append(zone)

print(found_cities)

data = {'geometry': [multipolygon]}
gdf = gpd.GeoDataFrame(data)

# Plotta il GeoDataFrame
gdf.plot()

# Mostra il grafico
plt.show()
