import pickle
import json
import warnings
from methods.geometric_operations import *
from methods.data_filling import *
from methods.building_type_classifier import *
from methods.tabula_archetypes import *
from methods.get_elevation import *
from methods.pod_mapper import *
from file_loader.methods.bbox_generator import *

warnings.filterwarnings('ignore')

start_time = time.time()

# Loading configuration parameters
with open("file_loader/config/config.json", "r") as c:
    config_data = json.load(c)
app_name = config_data["application_name"]
address = config_data["address"]
city = config_data["comune"]
h_slm = config_data["h_slm"]
crs = config_data["crs"]
target_crs = config_data["zona_UTM"]
dist = config_data["distance"]
res = config_data["resolution"]
target = config_data["target"]
building_target = config_data["building_target"]
filtering_values = config_data["building_filtering_values"]
required_columns = config_data["required_features"]
id_field = config_data["sezioni_di_censimento"]["metadata"]["id_to_select"]
DSM = config_data["DEM"]["DSM"]
DTM = config_data["DEM"]["DTM"]

with open("config/processing_config.json", "r") as d:
    pro_config_data = json.load(d)
shp_columns = pro_config_data["shp_columns_to_keep"]
building_age_columns = pro_config_data["building_age_columns"]
no_floors_columns = pro_config_data["floors"]["building_floors_no_columns"]
floor_height = pro_config_data["floors"]["single_floor_height"]
population_columns = pro_config_data["population_columns"]
z_score_thresh = pro_config_data["z_score_threshold"]
infiltration_rate_range = pro_config_data["infiltration_rate_range"]
cooling_prob = pro_config_data["cooling_system_probability"]
heating_prob = pro_config_data["heating_system_probability"]
en_demand_per_hh = pro_config_data["energy_demand"]

with open("config/tabula_config.json", "r") as e:
    tabula_data = json.load(e)
tabula_file = tabula_data["input_file_path"]
sheet = tabula_data["sheet_name"]
country_code_column = tabula_data["country_code_column_name"]
country_code = tabula_data["country_code_to_filter"]
distr_code = tabula_data["distribution_code"]
columns_to_filter = tabula_data["columns_of_interest"]

# Loading input files
with open('file_loader/output/osm.pkl', 'rb') as f:
    osm_gdf = pickle.load(f)

with open('file_loader/output/shp.pkl', 'rb') as g:
    shp_gdf = pickle.load(g)

with open('file_loader/output/sez.pkl', 'rb') as h:
    sez_gdf = pickle.load(h)

sez_det_df = pd.read_pickle('file_loader/output/sez_det.pkl')

# Geometric operations for input data overlapping and filtering
print("Starting geometric operations...")
gdf_obj = GeomOperator(osm_gdf, shp_gdf, sez_gdf, sez_det_df)
gdfs, unlocated_buildings = gdf_obj.place_building(target, required_columns, shp_columns, filtering_values, id_field, target_crs, z_score_thresh)

# Counting buildings and comparing found ones with effective registered ones
bld = 0
cens = sez_det_df['E3'].sum()
for key in gdfs.keys():
    bld += gdfs[key].shape[0]
print(f"No. of achieved residential buildings: {bld}")
print(f"No. of found residential buildings in census sections: {cens}")

''' Data filling and further computations according to 
statistical assumptions and available census data. '''

# Data filling operations
filled_gdfs_obj = DataFiller(gdfs, sez_det_df)
gdfs_filled = filled_gdfs_obj.fill_missing_data(required_columns, id_field, building_age_columns, no_floors_columns, floor_height, cooling_prob, heating_prob, infiltration_rate_range)

# Building type classification according to TABULA DataSet labels and further computations
def_gdfs_obj = BuildingTypeClassifier(gdfs_filled, sez_det_df)
gdfs_def = def_gdfs_obj.classify_building(required_columns, id_field, population_columns, building_target, filtering_values, en_demand_per_hh)

# Merging GeoDataFrames previously split per census section for consistent data filling and computation
merged_gdf = pd.concat(gdfs_def.values(), ignore_index=True)

# TABULA DataSet code label assignation
tabula_info_obj = TabulaInfoLoader(merged_gdf, tabula_file, sheet, country_code_column, country_code)
final_gdf, tabula_df = tabula_info_obj.add_tabula_info(required_columns, columns_to_filter)

# Random building POD generator
pod_gdf_obj = POD_mapper(final_gdf)
pod_final_gdf = pod_gdf_obj.map_POD(required_columns, country_code, distr_code)

# Displaying the final number of buildings
print(f"No. of residential buildings: {len(pod_final_gdf)}")

# Bounding box tuple generation
loc_object = BboxGenerator(address, dist, app_name)
bbox = loc_object.generate_bbox()

# Mapping z coordinate to buildings according to bounding box discretisation
print("Mapping Buildings elevation... ")
z_gdf_obj = ElevationMapper(pod_final_gdf)
z_gdf, grid = z_gdf_obj.get_elevation(crs, bbox, res, h_slm, required_columns)

# Appending minimum and maximum bounding box z coordinate
min_z, max_z = z_gdf_obj.get_bbox_z_coords()
bbox_z = list(bbox)
bbox_z.append(min_z)
bbox_z.append(max_z)
bbox_z = tuple(bbox_z)

# Writing bounding box coordinates in a JSON for later processing purposes
bbox_data = {}
bbox_data["bounding_box_z"] = bbox_z
with open("bounding_box.json", "w") as out:
    json.dump(bbox_data, out, indent=4)

# Filtering the achieved GeoDataFrame by keeping only buildings represented by Polygon and MultiPolygon geometries
filtered_z_gdf = z_gdf[z_gdf['geometry'].apply(lambda geom: isinstance(geom, (Polygon, MultiPolygon)))]

''' 
Saving buildings GeoDataFrame: 
the user can choose among two possible saving options 
accordingly to the file format chosen for loading in to_cj.py
located in the parent folder:
 1) ShapeFile folder;
 2) GeoJSON data.
 '''
filtered_z_gdf.to_file(f"output/{city}_{building_target}")
# filtered_z_gdf.to_file(f"output/{city}_{building_target}.geojson", driver='GeoJSON')

# Computing execution time
end_time = time.time()
total_time = end_time - start_time
hours, diff = divmod(total_time, 3600)
minutes, seconds = divmod(diff, 60)

print(f"Processing carried out in: {int(hours)} h, {int(minutes)} min, {int(seconds)} s")




