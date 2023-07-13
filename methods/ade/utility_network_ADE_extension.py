import pandas as pd
import geopandas as gpd
import glob
import os
import requests
import time
from pyproj import Transformer
from shapely.geometry import Point


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

        df['geometry'] = df.apply(lambda row: Point(row['x'], row['y'], row['z']), axis=1)

        gdf = gpd.GeoDataFrame(df, geometry='geometry')

        return gdf

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

        df['geometry'] = df.apply(lambda row: Point(row['x'], row['y'], row['z']), axis=1)

        gdf = gpd.GeoDataFrame(df, geometry='geometry')

        return gdf

    def map_ext(self):
        dataframe_dict = self.check_crs()

        network_gdf = dataframe_dict['network']
        buses_df = dataframe_dict['buses']
        buses_gdf = self.get_elevations(buses_df, max_retry=10, delay=0.5)
        lines_df = dataframe_dict['lines']
        loads_df = dataframe_dict['loads']
        generators_df = dataframe_dict['generators']
        switches_df = dataframe_dict['switches']
        transformers_df = dataframe_dict['transformers']
        transformers_hvmv_df = dataframe_dict['transformers_hvmv']

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

            featureNetwork = {
                f"featureGraph{network_elem['name']}": {
                    "type": "+FeatureGraph",
                    "attributes":
                        {
                            "node": list(dataframe_dict['buses']['name']),
                            "interiorFeatureLink": list(dataframe_dict['lines']['name'])
                        },
                    "children": list(dataframe_dict['buses']['name']) + list(dataframe_dict['buses']['name'])
                }
            }

            self.un_dict.update(featureNetwork)

            for b, bus_elem in buses_gdf.iterrows():
                # if bus_elem['name'] in loads_df.loc[loads_df['sector'] == 'residential', 'bus'].values:
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
                                        "value": round(float(bus_elem['v_nom']), 3),
                                        "uom": "kV"  # uom to be checked
                                    }
                                },
                            "geometry":
                                [
                                    {
                                        "type": "MultiPoint",
                                        "lod": "1",
                                        "boundaries":
                                            [
                                                bus_elem['geometry'].coords[0]
                                                # to be transformed according to CityJSON specifications, with z coordinate to be added
                                            ]
                                    }
                                ],
                            "parents":
                                [
                                    f"featureGraph{network_elem['name']}"
                                ]
                        }
                    }
                }
                self.un_dict.update(bus)

            for l, line_elem in lines_df.iterrows():
                # if line_elem['bus0'] in loads_df.loc[loads_df['sector'] == 'residential', 'bus'].values or line_elem[
                #   'bus1'] in loads_df.loc[loads_df['sector'] == 'residential', 'bus'].values:
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
                                    "uom": "Ω"  # uom to be checked
                                },
                                "x": {
                                    "value": float(line_elem['x']),
                                    "uom": "Ω"  # uom to be checked
                                },
                                "sNom": {
                                    "value": round(float(line_elem['s_nom']), 3),
                                    "uom": "MVA"  # uom to be checked
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
                                                buses_gdf[buses_gdf['name'] == line_elem['bus0']]['geometry'].coords[0],
                                                buses_gdf[buses_gdf['name'] == line_elem['bus1']]['geometry'].coords[0],
                                            ]
                                        ]
                                }
                            ],
                        "parents":
                            [
                                f"featureGraph{network_elem['name']}"
                            ]
                    }
                }
                self.un_dict.update(link)

            for ld, load_elem in loads_df.iterrows():
                # if load_elem['sector'] == 'residential':
                load = {
                    f"{bus_elem['name']}": {
                        "type": "+AbstractNetworkFeature",
                        "attributes":
                            {
                                "function": "disposal",
                                "usage": "disposal",
                                "bus": load_elem['bus'],
                                "peakLoad": {
                                    "value": round(float(load_elem['peak_load']), 3),
                                    "uom": "MW"  # uom to be checked
                                },
                                "annualConsumption": {
                                    "value": round(float(load_elem['annual_consumption']), 3),
                                    "uom": "kWh"  # uom to be checked
                                },
                                "sector": load_elem['sector']
                            }
                    }
                }
                self.un_dict.update(load)

            for g, gen_elem in generators_df.iterrows():
                # if gen_elem['bus'] in loads_df.loc[loads_df['sector'] == 'residential', 'bus'].values:
                generator = {
                    f"{gen_elem['name']}": {
                        "type": "+AbstractNetworkFeature",
                        "attributes": {
                            "function": "supply",
                            "usage": "supply",
                            "bus": gen_elem['bus'],
                            "control": gen_elem['control'],
                            "pNom": {
                                "value": float(gen_elem['p_nom']),
                                "uom": "MVA"  # uom to be checked
                            },
                            "type": gen_elem['type'],
                            "subtype": gen_elem['subtype'],
                            "weatherCellId": gen_elem['weather_cell_id'],
                        }
                    }
                }
                self.un_dict.update(generator)

            for s, switch_elem in switches_df.iterrows():
                switch = {
                    f"{switch_elem['name']}": {
                        "type": "+AbstractNetworkFeature",
                        "attributes": {
                            "busClosed": switch_elem['bus_closed'],
                            "busOpen": switch_elem['bus_open'],
                            "branch": switch_elem['branch'],
                            "type": switch_elem['type_info'],
                        }
                    }
                }
                self.un_dict.update(switch)

            for tr, transform_elem in transformers_df.iterrows():
                transformer = {
                    f"{transform_elem['name']}": {
                        "type": "+AbstractNetworkFeature",
                        "attributes": {
                            "sourceBus": transform_elem['bus0'],
                            "endBus": transform_elem['bus1'],
                            "r": {
                                "value": float(transform_elem['r']),
                                "uom": "Ω"  # uom to be checked
                            },
                            "x": {
                                "value": float(transform_elem['x']),
                                "uom": "Ω"  # uom to be checked
                            },
                            "sNom": {
                                "value": round(float(transform_elem['s_nom']), 3),
                                "uom": "MVA"  # uom to be checked
                            },
                            "additionalInfo": transform_elem['type_info'],
                        }
                    }
                }
                self.un_dict.update(transformer)

            for trHVMV, transform_hvmv_elem in transformers_hvmv_df.iterrows():
                transformer_hvmv = {
                    f"{transform_hvmv_elem['name']}": {
                        "type": "+AbstractNetworkFeature",
                        "attributes": {
                            "type": transform_hvmv_elem['type'],
                            "sourceBus": transform_hvmv_elem['bus0'],
                            "endBus": transform_hvmv_elem['bus1'],
                            "sNom": {
                                "value": round(float(transform_hvmv_elem['s_nom']), 3),
                                "uom": "MVA"  # uom to be checked
                            },
                            "additionalInfo": transform_hvmv_elem['type_info'],
                        }
                    }
                }
                self.un_dict.update(transformer_hvmv)

        return self.un_dict
