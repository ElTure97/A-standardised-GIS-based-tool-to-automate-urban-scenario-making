from methods.osm_2_gdf import *
from methods.bbox_generator import *
from methods.shp_2_gdf import *
from methods.consistency_checking import *
from methods.csv_2_df import *
import time
import warnings

warnings.filterwarnings('ignore')

start_time = time.time()

# open the configuration file
with open("config/config.json", "r") as f:
    config_data = json.load(f)

# load configuration data
application_name = config_data["application_name"]
address = config_data["address"]
provincia = config_data["provincia"]
comune = config_data["comune"]
crs = config_data["crs"]
distance = config_data["distance"]
target = config_data["target"]
required_columns = config_data["required_features"]
shapefile = config_data["shapefile"]
sez_shp = config_data["sezioni_di_censimento"]["shp"]
sez_csv = config_data["sezioni_di_censimento"]["csv"]
sez_meta = config_data["sezioni_di_censimento"]["metadata"]["metadata_file"]
fields = config_data["sezioni_di_censimento"]["metadata"]["fields"]
id_to_filter = config_data["sezioni_di_censimento"]["metadata"]["id_to_select"]

# load the open street map geodataframe
osm_data = OSM2GeoDF(address, distance, target, required_columns, crs)
gdf = osm_data.get_gdf_from_osm()
osm_gdf = osm_data.update_gdf(gdf)

filtering_values = osm_gdf[target].unique().tolist()
config_data["building_filtering_values"] = filtering_values

with open("config/config.json", "w") as outfile:
    json.dump(config_data, outfile, indent=4)

# generate the corresponding bounding box
loc_object = BboxGenerator(address, distance, application_name)
bbox = loc_object.generate_bbox()

# load the shapefile by specifying the bounding box
shapefile_path = shapefile
shp2gdf = SHP2GeoDF(shapefile_path, bbox, crs)
shp_gdf = shp2gdf.get_gdf_from_shp()

# check for consistency and store altitude coordinates (if available) for further processing
checker_osm =ConsistencyChecker(osm_gdf, crs)
osm_gdf, osm_z = checker_osm.check_consistency()
osm_gdf.to_pickle('output/osm.pkl') # save

checker_shp = ConsistencyChecker(shp_gdf, crs)
shp_gdf, shp_z = checker_shp.check_consistency()
shp_gdf.to_pickle('output/shp.pkl') # save

# load sezioni di censimento by specifying the bounding box
sezioni_di_censimento = sez_shp
sez_shp2gdf = SHP2GeoDF(sezioni_di_censimento, bbox, crs)
sez_shp_gdf = sez_shp2gdf.get_gdf_from_shp()
sez_shp_gdf.to_pickle('output/sez.pkl') # save

# load sezioni di censimento detailed data
sez_cens = CSV2DF(sez_csv, provincia, comune, fields, crs)
sez_cens_df = sez_cens.load_csv(sez_shp_gdf, id_to_filter)
sez_cens_df.to_pickle('output/sez_det.pkl')

end_time = time.time()
total_time = end_time - start_time
ore, resto = divmod(total_time, 3600)
minuti, secondi = divmod(resto, 60)

print(f"Tempo di esecuzione: {int(ore)} h, {int(minuti)} min, {int(secondi)} s")
