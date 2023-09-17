import geopandas as gpd
import json
import os
import subprocess
import sys
import warnings
from methods.cj_converter import *
from methods.ade.energy_ADE_extension import *
# from methods.ade.utility_network_ADE_extension_for_ding0 import *
from methods.ade.utility_network_ADE_extension import *

current_dir = os.getcwd()

warnings.filterwarnings('ignore')

start_time = time.time()

loader_dir = os.path.dirname(os.path.abspath("buildings/file_loader/loader.py"))
os.chdir(loader_dir)
python_exe = sys.executable
loader = "loader.py"
subprocess.call([python_exe, loader])

os.chdir(current_dir)

# Loading configuration parameters
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
building_filtering_values = config_data["building_filtering_values"]

# For terminal interface
print(f"***BUILDING CATEGORIES***")
for bld_cat in building_filtering_values:
    print(bld_cat)
print(f'''
***CONFIGURATION STEP***
In the following step, you will be required to type the building categories you want to store 
as Apartment Blocks (AB), Single Family Houses (SFH), Multi Family Houses (MFH), Terraced House (TH),
or not-specified for very generic categories.
Please choose among the list above the categories you want to map to each of the above-mentioned
building archetype, paying attention to avoid typos.
You can discard the categories you do not want to focus on for that application.
Press ENTER, if none of the building categories belong to the current archetype.

***PRESS ENTER TO CONTINUE***
''')

input()

AB_list = input("AB: ").split()
SFH_list = input("SFH: ").split()
MFH_list = input("MFH: ").split()
TH_list = input("TH: ").split()
not_specified_list = input("not-specified: ").split()
print("")

building_filtering_values = {}
building_filtering_values["not_specified"] = not_specified_list
building_filtering_values["AB"] = AB_list
building_filtering_values["SFH"] = SFH_list
building_filtering_values["MFH"] = MFH_list
building_filtering_values["TH"] = TH_list

config_data["building_filtering_values"] = building_filtering_values

with open("buildings/file_loader/config/config.json", "w") as outfile:
    json.dump(config_data, outfile, indent=4)

main_dir = os.path.dirname(os.path.abspath("buildings/main.py"))
os.chdir(main_dir)
python_exe = sys.executable
loader = "main.py"
subprocess.call([python_exe, loader])

os.chdir(current_dir)

with open("config/cityjson_config.json", "r") as g:
    cj_config_data = json.load(g)
ades = cj_config_data["extensions"]
lod = cj_config_data["LoD"]
crs_url = cj_config_data["crs_url"]
energy_acquisition_method = cj_config_data["energy_acquisition_method"]
energy_interpolation_method = cj_config_data["energy_interpolation_method"]
energy_measurement_period = cj_config_data["energy_measurement_period"]
pp_path = cj_config_data["pp_utility_file_path"]

with open("buildings/bounding_box.json", "r") as h:
    bbox_data = json.load(h)
bbox = tuple(bbox_data["bounding_box_z"])

with open("utility/config/ding0_config.json", "r") as j:
    ding0_data = json.load(j)
MV_district = str(ding0_data["MV_district"])

with open("config/weather_config.json", "r") as k:
    weather_config_data = json.load(k)

''' 
Loading buildings GeoDataFrame: 
the user can choose among two possible loading options 
accordingly to the file format previously chosen for saving in buildings\main.py:
 1) ShapeFile folder;
 2) GeoJSON data.
 '''
gdf = gpd.read_file(f"buildings/output/{city}_{building_target}")
# gdf = gpd.read_file(f"buildings/output/{city}_{building_target}.geojson")

# Creation of two empty lists respectively for building objects extension and for city objects extension
ext_bld_list = []
ext_city_list = []

''' Further ADEs modules must be added here following the same syntax
pay attention to append the extension to the right list since according to that, 
the extension will be applied to buildings or city. '''
energy_ADE_obj = EnergyADE(gdf)
energy_bld_ext, energy_city_ext = energy_ADE_obj.map_ext(city, address, energy_acquisition_method, energy_interpolation_method, energy_measurement_period, weather_config_data)
ext_bld_list.append(energy_bld_ext)

''' 
Loading grid data: 
the user can choose among two possible loading options 
accordingly to the available files:
 1) Ding0 output;
 2) PandaPower data.
 '''
# ding0_path = f"utility/ding0-output/{MV_district}/*.csv"
# un_ADE = UtilityNetworkADE(ding0_path, crs, h_slm, lod)

un_ADE = UtilityNetworkADE(gdf)

utility_network_ext = un_ADE.map_ext(pp_path, crs, UTM_zone, city, h_slm, bbox, lod)
un_ADE.plot_city_map(city)

ext_city_list.append(energy_city_ext)
ext_city_list.append(utility_network_ext)

'''Extension removal from the ADEs list just for single extension testing purposes, if needed.
Element 0 is the energy extension, while element -1 is the utility network one.
In addition to that, in the previous lines, no appending must be operated. '''
# ades.pop(0)
# ades.pop(-1)

# CityJSON writing
cj_creator = CityJSONCreator(gdf)
cj_creator.write_json(bbox, bounds, ades, ext_bld_list, ext_city_list, lod, crs, crs_url, UTM_zone, city, nation, building_target, nuts3, lau2)

# Computing execution time
end_time = time.time()
total_time = end_time - start_time
hours, diff = divmod(total_time, 3600)
minutes, seconds = divmod(diff, 60)

print(f"Pipeline execution time: {int(hours)} h, {int(minutes)} min, {int(seconds)} s")