import geopandas as gpd
import json
from methods.cj_converter import *
from methods.ade.energy_ADE_extension import *

with open("buildings/file_loader/config/config.json", "r") as f:
    config_data = json.load(f)
app_name = config_data["application_name"]
address = config_data["address"]
city = config_data["comune"]
nation = config_data["nazione"]
nuts3 = config_data["NUTS3"]
lau2 = config_data["LAU2"]
h_slm = config_data["h_slm"]
crs = config_data["crs"]
UTM_zone = config_data["zona_UTM"]
bounds = config_data["min_bounds_coordinates"]
dist = config_data["distance"]
building_target = config_data["building_target"]

with open("config/cityjson_config.json", "r") as g:
    cj_config_data = json.load(g)
ades = cj_config_data["extensions"]
lod = cj_config_data["LoD"]
crs_url = cj_config_data["crs_url"]

with open("buildings/bounding_box.json", "r") as h:
    bbox_data = json.load(h)
bbox = tuple(bbox_data["bounding_box_z"])

gdf = gpd.read_file(f"buildings/output/{city}_{building_target}")
# headers = list(gdf.columns)

ext_list = []

# further ADEs modules must be added here following the same syntax
energy_ADE_obj = EnergyADE(gdf)
energy_ext = energy_ADE_obj.map_ext()
ext_list.append(energy_ext)

cj_creator = CityJSONCreator(gdf)
cj_creator.write_json(bbox, bounds, ades, ext_list, lod, crs, crs_url, UTM_zone, city, nation, building_target, nuts3, lau2)
