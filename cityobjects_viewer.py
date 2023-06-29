import json

with open("ext_schemas/cj_un_schema.json", "r") as f:
    config_data = json.load(f)
extraCityObjects = config_data["extraCityObjects"]

city_objs = extraCityObjects.keys()

city_obj_list = list(city_objs)