import pandas as pd
import geopandas as gpd
import glob
import os
import requests
import shapely.wkt
import time
from pyproj import Transformer


class UtilityNetworkADE:

    def __init__(self, path, crs, h_slm, lod):
        self.path = path
        self.crs = crs
        self.h_slm = h_slm
        self.lod = lod
        self.dataframe_dict = {}
        self.un_dict = {}

    # DataFrames loading
    def load_csv(self):
        csv_file = glob.glob(self.path)
        for file in csv_file:
            df = pd.read_csv(file)
            file_name = os.path.splitext(os.path.basename(file))[0]
            self.dataframe_dict[file_name] = df
        return self.dataframe_dict

    # Consistency checking
    def check_crs(self):
        self.dataframe_dict = self.load_csv()
        network_df = self.dataframe_dict['network']
        buses_df = self.dataframe_dict['buses']
        buses_df = buses_df.dropna(subset=["x", "y"])
        network_df = network_df.rename(columns={'mv_grid_district_geom': 'geometry'})
        network_df['geometry'] = network_df['geometry'].apply(shapely.wkt.loads)
        network_gdf = gpd.GeoDataFrame(network_df, geometry='geometry')
        network_gdf.set_crs(epsg=network_gdf['srid'][0], inplace=True)  # for single network loading
        # network_gdf = network_gdf.set_geometry(network_gdf['geometry'])

        current_crs = network_gdf.crs
        target_crs = self.crs

        if current_crs != target_crs:
            network_gdf = network_gdf.to_crs(target_crs)

            transformer = Transformer.from_crs(current_crs, target_crs)

            buses_df['x'], buses_df['y'] = transformer.transform(buses_df['x'], buses_df['y'])

        self.dataframe_dict['network'] = network_gdf
        self.dataframe_dict['buses'] = buses_df

        return self.dataframe_dict

    # Getting elevations of network objects through APIs, set to default city height ASL in case of failed requests
    def get_elevations(self, df, max_retry, delay):
        points = []
        for i, elem in df.iterrows():
            points.append((elem['x'], elem['y']))
        locations = "|".join([f"{point[1]},{point[0]}" for point in points])
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations}"

        request_size = len(url.encode('utf-8'))

        if request_size <= 1024:
            # GET API
            df = self.send_get_request(df, points, url, max_retry, delay)
        else:
            # POST API
            df = self.send_post_request(df, points, max_retry, delay)

        df['geometry'] = [f"POINT ({row['x']} {row['y']} {row['z']})" for r, row in df.iterrows()]
        df.drop(['x', 'y', 'z'], axis=1, inplace=True)
        df['geometry'] = df['geometry'].apply(shapely.wkt.loads)
        gdf = gpd.GeoDataFrame(df, geometry='geometry')

        return gdf

    # Sending GET request
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

        # Default city height ASL values mapping in case of failed requests
        df['z'] = [self.h_slm] * len(points)

        return df

    # Sending POST request
    def send_post_request(self, df, points, max_retry, delay):
        url = "https://api.open-elevation.com/api/v1/lookup"
        batch_size = 100
        retry_count = 0
        while retry_count < max_retry:
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                data = {"locations": [{"latitude": point[1], "longitude": point[0]} for point in batch]}

                response = requests.post(url, json=data)

                if response.status_code == 200:
                    print("Success!")
                    try:
                        batch_elevations = [result["elevation"] for result in response.json()["results"]]
                        # Assign elevations to the corresponding subset of the DataFrame
                        df.loc[i:i + batch_size - 1, 'z'] = batch_elevations
                    except ValueError:
                        print("Invalid JSON response.")
                        break
                else:
                    print(f"Request failed for batch {i // batch_size + 1}.")

            if df['z'].isna().any():
                print("Retrying failed points...")
                retry_count += 1
                time.sleep(delay)
            else:
                break

        # Filling remaining missing values with default city height ASL values
        df['z'].fillna(self.h_slm, inplace=True)

        return df

    # Mapping network data according to the Utility Network extension schema
    def map_ext(self):
        self.dataframe_dict = self.check_crs()

        network_gdf = self.dataframe_dict['network']
        buses_df = self.dataframe_dict['buses']
        buses_gdf = self.get_elevations(buses_df, max_retry=10, delay=0.5)
        lines_df = self.dataframe_dict['lines']
        lines_df = lines_df[lines_df['bus0'].isin(buses_gdf['name']) & lines_df['bus1'].isin(buses_gdf['name'])]
        loads_df = self.dataframe_dict['loads']
        generators_df = self.dataframe_dict['generators']
        switches_df = self.dataframe_dict['switches']
        transformers_df = self.dataframe_dict['transformers']
        transformers_hvmv_df = self.dataframe_dict['transformers_hvmv']

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
                            "node": list(buses_gdf['name']),
                            "interiorFeatureLink": lines_df.loc[(lines_df['bus0'].astype(int).isin(buses_gdf.index)) & (lines_df['bus1'].astype(int).isin(buses_gdf.index)), 'name'].tolist()
                        },
                    "children": list(buses_gdf['name']) + lines_df.loc[(lines_df['bus0'].astype(int).isin(buses_gdf.index)) & (lines_df['bus1'].astype(int).isin(buses_gdf.index)), 'name'].tolist()
                }
            }

            self.un_dict.update(featureNetwork)

            for b, bus_elem in buses_gdf.iterrows():
                if bus_elem["in_building"]:
                    nodeValue = "interior"
                else:
                    nodeValue = "exterior"

                bus = {
                    bus_elem['name']: {
                            "type": "+Node",
                            "attributes":
                                {
                                    "NodeValue": nodeValue,
                                    "nominalVoltage": {
                                        "value": round(float(bus_elem['v_nom']), 3),
                                        "uom": "kV"
                                    }
                                },
                            "geometry":
                                [
                                    {
                                        "type": "MultiPoint",
                                        "lod": self.lod,
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
                self.un_dict.update(bus)

            for l, line_elem in lines_df.iterrows():
                if line_elem['bus0'] in buses_gdf['name'].values and line_elem['bus1'] in buses_gdf['name'].values:
                    link = {
                        line_elem['name'] : {
                            "type": "+InteriorFeatureLink",
                            "attributes":
                                {
                                    "start": line_elem['bus0'],
                                    "end": line_elem['bus1'],
                                    "kind": line_elem['kind'],
                                    "length": {
                                        "value": float(line_elem['length']),
                                        "uom": "km"
                                    },
                                    "r": {
                                        "value": float(line_elem['r']),
                                        "uom": "ohm"
                                    },
                                    "x": {
                                        "value": float(line_elem['x']),
                                        "uom": "ohm"
                                    },
                                    "sNom": {
                                        "value": round(float(line_elem['s_nom']), 3),
                                        "uom": "MVA"
                                    },
                                    "additionalInfo": line_elem['type_info'],
                                },
                            "geometry":
                                [
                                    {
                                        "type": "MultiLineString",
                                        "lod": self.lod,
                                        "boundaries":
                                            [
                                                [
                                                    buses_gdf[buses_gdf['name'] == line_elem['bus0']]['geometry'].iloc[0].coords[0],
                                                    buses_gdf[buses_gdf['name'] == line_elem['bus1']]['geometry'].iloc[0].coords[0],
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
                if load_elem['bus'] in buses_gdf['name'].values:
                    load = {
                        load_elem['name']: {
                            "type": "+AbstractNetworkFeature",
                            "attributes":
                                {
                                    "function": "disposal",
                                    "usage": "disposal",
                                    "bus": load_elem['bus'],
                                    "peakLoad": {
                                        "value": round(float(load_elem['peak_load']), 3),
                                        "uom": "MW"
                                    },
                                    "annualConsumption": {
                                        "value": round(float(load_elem['annual_consumption']), 3),
                                        "uom": "kWh"
                                    },
                                    "sector": load_elem['sector']
                                }
                        }
                    }
                    self.un_dict.update(load)

            for g, gen_elem in generators_df.iterrows():
                if gen_elem['bus'] in buses_gdf['name'].values:
                    generator = {
                        gen_elem['name']: {
                            "type": "+AbstractNetworkFeature",
                            "attributes": {
                                "function": "supply",
                                "usage": "supply",
                                "bus": gen_elem['bus'],
                                "control": gen_elem['control'],
                                "pNom": {
                                    "value": float(gen_elem['p_nom']),
                                    "uom": "MVA"
                                },
                                "type": gen_elem['type'],
                                "subtype": gen_elem['subtype']
                            }
                        }
                    }
                    self.un_dict.update(generator)

            for s, switch_elem in switches_df.iterrows():
                if switch_elem['bus_closed'] in buses_gdf['name'].values and switch_elem['bus_open'] in buses_gdf['name'].values:
                    switch = {
                        switch_elem['name']: {
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
                if transform_elem['bus0'] in buses_gdf['name'].values and transform_elem['bus1'] in buses_gdf['name'].values:
                    transformer = {
                        transform_elem['name']: {
                            "type": "+AbstractNetworkFeature",
                            "attributes": {
                                "sourceBus": transform_elem['bus0'],
                                "endBus": transform_elem['bus1'],
                                "r": {
                                    "value": float(transform_elem['r']),
                                    "uom": "ohm"
                                },
                                "x": {
                                    "value": float(transform_elem['x']),
                                    "uom": "ohm"
                                },
                                "sNom": {
                                    "value": round(float(transform_elem['s_nom']), 3),
                                    "uom": "MVA"
                                },
                                "additionalInfo": transform_elem['type_info'],
                            }
                        }
                    }
                    self.un_dict.update(transformer)

            for trHVMV, transform_hvmv_elem in transformers_hvmv_df.iterrows():
                if transform_hvmv_elem['bus1'] in buses_gdf['name'].values:
                    transformer_hvmv = {
                        transform_hvmv_elem['name']: {
                            "type": "+AbstractNetworkFeature",
                            "attributes": {
                                "type": transform_hvmv_elem['type'],
                                "sourceBus": transform_hvmv_elem['bus0'],
                                "endBus": transform_hvmv_elem['bus1'],
                                "sNom": {
                                    "value": round(float(transform_hvmv_elem['s_nom']), 3),
                                    "uom": "MVA"
                                },
                                "additionalInfo": transform_hvmv_elem['type_info'],
                            }
                        }
                    }
                    self.un_dict.update(transformer_hvmv)

        for key, inner_dict in self.un_dict.items():
             for inner_key, dict_value in inner_dict.items():
                if isinstance(dict_value, dict):
                    for inner_inner_key, inner_inner_value in dict_value.items():
                        if inner_inner_value == "nan" or inner_inner_value == "NaN" or inner_inner_value == "Nan" or inner_inner_value is None:
                            dict_value[inner_inner_key] = "data not available"
                else:
                    if dict_value == "nan" or dict_value == "NaN" or dict_value == "Nan" or dict_value is None:
                        inner_dict[inner_key] = "data not available"


        return self.un_dict
