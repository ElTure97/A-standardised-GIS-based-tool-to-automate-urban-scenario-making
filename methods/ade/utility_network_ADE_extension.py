import pandas as pd
import geopandas as gpd
import numpy as np
import pandapower as pp
import requests
import shapely.wkt
import time
from shapely.geometry import Point, Polygon, LineString
from pyproj import Transformer


class UtilityNetworkADE:

    def __init__(self, path, crs, zone, h_slm, bounding_box):
        self.path = path
        self.crs = crs
        self.zone = zone
        self.h_slm = h_slm
        self.bounding_box = bounding_box
        self.network = {}
        self.un_dict = {}

    def load_pp(self):
        network = pp.from_pickle(self.path)
        # clean empty dfs
        self.network = {dataframe_name: dataframe for dataframe_name, dataframe in network.items() if not isinstance(dataframe, pd.DataFrame) or not dataframe.empty}
        return self.network

    def geometric_operations(self):
        self.network = self.load_pp()
        # network_df = self.network['ext_grid']
        buses_df = self.network['bus']
        loads_df = self.network['load']
        gens_df = self.network['sgen']
        trans_df = self.network['trafo']
        lines_df = self.network['line']

        buses_gdf = gpd.GeoDataFrame(buses_df)
        loads_gdf = gpd.GeoDataFrame(loads_df)
        gens_gdf = gpd.GeoDataFrame(gens_df)
        trans_gdf = gpd.GeoDataFrame(trans_df)

        def multiply_coordinates(point, factor):
            new_x = point.x * factor
            new_y = point.y * factor
            return Point(new_x, new_y)

        # multiply gdf coords
        factor = 1000
        src_crs = f"EPSG:326{self.zone}"
        buses_gdf['geometry'] = buses_gdf['geometry'].apply(lambda point: multiply_coordinates(point, factor))

        buses_gdf = buses_gdf.set_crs(src_crs)
        loads_gdf = loads_gdf.set_crs(src_crs)
        gens_gdf = gens_gdf.set_crs(src_crs)
        trans_gdf = trans_gdf.set_crs(src_crs)

        buses_gdf = buses_gdf.to_crs(self.crs)
        loads_gdf = loads_gdf.to_crs(self.crs)
        gens_gdf = gens_gdf.to_crs(self.crs)
        trans_gdf = trans_gdf.to_crs(self.crs)

        transformer = Transformer.from_crs(src_crs, self.crs, always_xy=True)

        def transform_coordinates(coord_list):
            transformed_coords = [transformer.transform(x, y) for x, y in coord_list]
            return LineString(transformed_coords)

        lines_df['geometries'] = lines_df['coordinates'].apply(transform_coordinates)

        lines_gdf = gpd.GeoDataFrame(lines_df, geometry='geometries', crs=self.crs)

        def filter_by_bbox(gdf):
            min_lon, min_lat, max_lon, max_lat, min_z, max_z = self.bounding_box

            bbox = Polygon([(min_lon, min_lat), (max_lon, min_lat), (max_lon, max_lat), (min_lon, max_lat)])

            intersected = gdf[gdf.geometry.apply(lambda geom: bbox.intersects(geom) or bbox.contains(geom))]

            return intersected

        buses_gdf = filter_by_bbox(buses_gdf)
        loads_gdf = filter_by_bbox(loads_gdf)
        gens_gdf = filter_by_bbox(gens_gdf)
        trans_gdf = filter_by_bbox(trans_gdf)
        lines_gdf = filter_by_bbox(lines_gdf)

        return buses_gdf, loads_gdf, gens_gdf, trans_gdf, lines_gdf

    def get_elevations(self, gdf, max_retry, delay):
        points = [(elem['geometry']) for _, elem in gdf.iterrows()]
        elevs = self.send_get_or_post_request(points, max_retry, delay)

        updated_geometries = []
        for geom, elev in zip(gdf['geometry'], elevs):
            if isinstance(geom, Point):
                coords = list(geom.coords)
                coords[0] = (coords[0][0], coords[0][1], elev)
                updated_geometries.append(Point(coords[0]))
            elif isinstance(geom, LineString):
                coords = list(geom.coords)
                updated_coords = [(coord[0], coord[1], elev) for coord in coords]
                updated_geometries.append(LineString(updated_coords))

        gdf['geometry'] = updated_geometries
        return gdf

    def send_get_or_post_request(self, points, max_retry, delay):
        url = "https://api.open-elevation.com/api/v1/lookup"
        batch_size = 100  # Number of points to send in each POST request
        elevations = [np.nan] * len(points)  # Initialize with NaNs
        retry_count = 0

        while retry_count < max_retry:
            if len(url.encode('utf-8')) <= 1024:
                # GET API
                elevations = self.send_get_request(points, url, delay)
            else:
                # POST API
                elevations = self.send_post_request(points)

            if np.isnan(elevations).any():
                print("Retrying failed points...")
                retry_count += 1
                time.sleep(delay)
            else:
                break

        # Fill remaining missing values with default values
        elevations = [e if not np.isnan(e) else self.h_slm for e in elevations]

        return elevations

    def send_get_request(self, points, url, delay):
        response = requests.get(url)
        if response.status_code == 200:
            print("Success!")
            data = response.json()
            elevations = [result["elevation"] for result in data["results"]]
            return elevations
        else:
            print(f"Request failed. New attempt in {delay} s")
            return [np.nan] * len(points)

    def send_post_request(self, points):
        url = "https://api.open-elevation.com/api/v1/lookup"
        batch_size = 100  # Number of points to send in each POST request
        elevations = [np.nan] * len(points)  # Initialize with NaNs

        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            data = {"locations": [{"latitude": point.y, "longitude": point.x} for point in batch]}

            response = requests.post(url, json=data)

            if response.status_code == 200:
                print("Success!")
                try:
                    batch_elevations = [result["elevation"] for result in response.json()["results"]]
                    elevations[i:i + len(batch_elevations)] = batch_elevations
                except ValueError:
                    print("Invalid JSON response.")
                    break
            else:
                print(f"Request failed for batch {i // batch_size + 1}.")

        return elevations

    def map_ext(self):
        self.network = self.check_crs()

        network_gdf = self.network['network']
        buses_df = self.network['buses']
        buses_gdf = self.get_elevations(buses_df, max_retry=10, delay=0.5)
        lines_df = self.network['lines']
        lines_df = lines_df[lines_df['bus0'].isin(buses_gdf['name']) & lines_df['bus1'].isin(buses_gdf['name'])]
        loads_df = self.network['loads']
        generators_df = self.network['generators']
        switches_df = self.network['switches']
        transformers_df = self.network['transformers']
        transformers_hvmv_df = self.network['transformers_hvmv']

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
                            "interiorFeatureLink": list(lines_df['name'])
                        },
                    "children": list(buses_gdf['name']) + list(lines_df['name'])
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
                    bus_elem['name']: {
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
                                        "uom": "ohm"  # uom to be checked
                                    },
                                    "x": {
                                        "value": float(line_elem['x']),
                                        "uom": "ohm"  # uom to be checked
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
                                    "uom": "MVA"  # uom to be checked
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
                                    "uom": "ohm"  # uom to be checked
                                },
                                "x": {
                                    "value": float(transform_elem['x']),
                                    "uom": "ohm"  # uom to be checked
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
                                    "uom": "MVA"  # uom to be checked
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
