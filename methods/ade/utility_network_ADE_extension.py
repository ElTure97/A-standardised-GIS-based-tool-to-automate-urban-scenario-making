import pandas as pd
import geopandas as gpd
import glob
import os
import requests
import time
from pyproj import Transformer

class UtilityNetworkADE:

    def __init__(self, path, crs, h_slm):
        self.path = path
        self.crs = crs
        self.h_slm = h_slm
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
        dataframe_dict = self.load_csv()
        network_df = dataframe_dict['network']
        buses_df = dataframe_dict['buses']

        network_gdf = gpd.GeoDataFrame(network_df)

        current_crs = network_gdf.crs
        target_crs = self.crs

        if current_crs != target_crs:
            network_gdf = network_gdf.to_crs(target_crs)

            transformer = Transformer.from_crs(current_crs, target_crs)

            buses_df['x'], buses_df['y'] = transformer.transform(buses_df['x'], buses_df['y'])

            dataframe_dict['network'] = network_gdf
            dataframe_dict['buses'] = buses_df

        return dataframe_dict

    def get_elevations(self, df, max_retry, delay):
        points = []
        for i, elem in df.iterrows():
            points.append((elem['x'], elem['y']))
        locations = "|".join([f"{point[1]},{point[0]}" for point in points])
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations}"

        request_size = len(url.encode('utf-8'))

        if request_size <= 1024:
            # GET API
            return self.send_get_request(df, points, url, max_retry, delay)
        else:
            # POST API
            return self.send_post_request(df, points, max_retry, delay)

    def send_get_request(self, df, points, url, max_retry, delay):
        retry_count = 0
        while retry_count < max_retry:
            response = requests.get(url)

            if response.status_code == 200:
                print("Success!")
                data = response.json()
                elevations = [result["elevation"] for result in data["results"]]
                df['z'] = elevations
                return df
            else:
                print(f"Request failed. New attempt in {delay} s")
                retry_count += 1
                time.sleep(delay)

        df['z'] = [self.h_slm] * len(points)
        return df

    def send_post_request(self, df, points, max_retry, delay):
        url = "https://api.open-elevation.com/api/v1/lookup"
        data = {"locations": []}
        for point in points:
            data["locations"].append({"latitude": point.y, "longitude": point.x})

        retry_count = 0
        while retry_count < max_retry:
            response = requests.post(url, json=data)

            if response.status_code == 200:
                print("Success!")
                data = response.json()
                elevations = [result["elevation"] for result in data["results"]]
                df['z'] = elevations
                return df
            else:
                print(f"Request failed. New attempt in {delay} s")
                retry_count += 1
                time.sleep(delay)

        # default values
        df['z'] = [self.h_slm] * len(points)
        return df

    def map_ext(self):
        dataframe_dict = self.check_crs()

        network_gdf = dataframe_dict['network']
        buses_df = dataframe_dict['buses']
        buses_df = self.get_elevations(buses_df, max_retry=10, delay=0.5)
        lines_df = dataframe_dict['lines']

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
            x = bus_elem['x']
            y = bus_elem['y']
            z = bus_elem['z']
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
                                "NodeValue": nodeValue,
                                "nominalVoltage": {
                                    "value": round(float(bus_elem['v_nom']), 1),
                                    "uom": "kV"
                                }
                            },
                        "geometry":
                            [
                                {
                                    "type": "MultiPoint",
                                    "lod": "1",
                                    "boundaries":
                                        [
                                            (x, y, z) # to be transformed according to CityJSON specifications, with z coordinate to be added
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
            self.un_dict.update(bus)

        for l, line_elem in lines_df.iterrows():
            link = {
                f"{line_elem['name']}": {
                    "type": "+InteriorFeatureLink",
                    "attributes":
                        {
                            "start": line_elem['bus0'],
                            "end": line_elem['bus1'],
                            "kind": line_elem['kind'],
                            "lenght": {
                                "value": float(line_elem['lenght']),
                                "uom": "km"
                            },
                            "r": {
                                "value": float(line_elem['r']),
                                "uom": "Ω" # uom to be checked
                            },
                            "x": {
                                "value": float(line_elem['x']),
                                "uom": "Ω"  # uom to be checked
                                  },
                            "nominalPower": {
                                "value": round(float(line_elem['s_nom']), 3),
                                "uom": "kW" # uom to be checked
                            },
                            "additionalInfo": line_elem['type_info'],
                        },
                    "geometry":
                        [
                            {
                                "type": "MultiLineString",
                                "lod": "1",
                                "boundaries":
                                    [
                                        [
                                            (buses_df[buses_df['name'] == line_elem['bus0']]['x'].values[0], buses_df[buses_df['name'] == line_elem['bus0']]['y'].values[0], buses_df[buses_df['name'] == line_elem['bus0']]['z'].values[0]),
                                            (buses_df[buses_df['name'] == line_elem['bus1']]['x'].values[0], buses_df[buses_df['name'] == line_elem['bus1']]['y'].values[0], buses_df[buses_df['name'] == line_elem['bus1']]['z'].values[0])
                                        ]
                                    ]
                            }
                        ],
                    "parents":
                        [
                            "myFeatureGraph"
                        ]
                }
            }
            self.un_dict.update(link)

