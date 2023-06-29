import pandas as pd
import geopandas as gpd
import glob
import os
from pyproj import Transformer

class UtilityNetworkADE:

    def __init__(self, path, crs):
        self.path = path
        self.crs = crs
        self.un_dict = {}

    def load_csv(self, path):
        csv_file = glob.glob(path)
        dataframe_dict = {}
        for file in csv_file:
            df = pd.read_csv(file)
            file_name = os.path.splitext(os.path.basename(file))[0]
            dataframe_dict[file_name] = df
        return dataframe_dict

    def check_crs(self):
        self.dataframe_dict = self.load_csv()
        network_df = self.dataframe_dict['network']
        buses_df = self.dataframe_dict['buses']

        network_gdf = gpd.GeoDataFrame(network_df)

        current_crs = network_gdf.crs
        target_crs = self.crs

        if current_crs != target_crs:
            network_gdf = network_gdf.to_crs(target_crs)

            transformer = Transformer.from_crs(current_crs, target_crs)

            buses_df['x'], buses_df['y'] = transformer.transform(buses_df['x'], buses_df['y'])

        return network_gdf, buses_df

    def map_ext(self):
        network_gdf, buses_df = self.check_crs()
        for n, network_elem in network_gdf.iterrows():
            network = {
                f"mvGrid{network_elem['name']}":
                {
                "type": "+Network",
                "attributes":
                    {
                        "class": "MediumVoltageNetwork",
                        "usage": "supply",
                        "function": "supply",
                        "transportedMedium":
                            {
                                "type": "+AbstractCommodity"
                            }
                    }
                }
            }
            self.un_dict.update(network)


        for b, bus_elem in buses_df.iterrows():
            if bus_elem["in_building"]:
                nodeValue = "interior"
            else:
                nodeValue = "exterior"

            bus = {
                f"{bus_elem['name']}": {
                    {
                        "type": "+Node",
                        "attributes":
                            {
                                "NodeValue": nodeValue
                            },
                        "geometry":
                            [
                                {
                                    "type": "MultiPoint",
                                    "lod": "1",
                                    "boundaries":
                                        [
                                            0
                                        ]
                                }
                            ],
                        "parents":
                            [
                                "myFeatureGraph"
                            ]
                    }
                }
            }