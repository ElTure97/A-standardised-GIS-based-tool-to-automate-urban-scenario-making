import json

class JSON_Writer:

    def __init__(self, gdf):
        self.gdf = gdf

    def write_json(self, path, empty_dict):
        with open(path, "w") as j:
            json.dump(empty_dict, j, indent=4)



