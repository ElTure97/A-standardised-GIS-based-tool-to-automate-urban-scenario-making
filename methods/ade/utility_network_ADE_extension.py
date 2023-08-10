import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandapower as pp
import requests
import time
from shapely.geometry import Point, Polygon, MultiPolygon, LineString
from pyproj import Transformer


class UtilityNetworkADE:

    def __init__(self, buildings_gdf):
        self.buildings_gdf = buildings_gdf
        self.network = {}
        self.un_dict = {}
        self.un_gdf_list = []
        self.un_elems_labels = []
        self.colors = []

    def load_pp(self, path):
        network = pp.from_pickle(path)
        # Cleaning empty DataFrames
        self.network = {dataframe_name: dataframe for dataframe_name, dataframe in network.items() if not isinstance(dataframe, pd.DataFrame) or not dataframe.empty}
        return self.network

    # Specific geometric operations on loaded DataFrames for crs consistency achievement
    def geometric_operations(self, path, crs, zone, bounding_box):
        self.network = self.load_pp(path)
        # network_df = self.network['ext_grid']
        buses_df = self.network['bus']
        loads_df = self.network['load']
        gens_df = self.network['sgen']
        trans_df = self.network['trafo']
        lines_df = self.network['line']
        switches_df = self.network['switch']

        buses_gdf = gpd.GeoDataFrame(buses_df)
        loads_gdf = gpd.GeoDataFrame(loads_df)
        gens_gdf = gpd.GeoDataFrame(gens_df)
        trans_gdf = gpd.GeoDataFrame(trans_df)

        # Specific coordinates scaling operation
        def multiply_coordinates(point, factor):
            new_x = point.x * factor
            new_y = point.y * factor
            return Point(new_x, new_y)

        # Multiply GeoDataFrame coordinates
        factor = 1000
        src_crs = f"EPSG:326{zone}"
        buses_gdf['geometry'] = buses_gdf['geometry'].apply(lambda point: multiply_coordinates(point, factor))

        buses_gdf = buses_gdf.set_crs(src_crs)
        loads_gdf = loads_gdf.set_crs(src_crs)
        gens_gdf = gens_gdf.set_crs(src_crs)
        trans_gdf = trans_gdf.set_crs(src_crs)

        buses_gdf = buses_gdf.to_crs(crs)
        loads_gdf = loads_gdf.to_crs(crs)
        gens_gdf = gens_gdf.to_crs(crs)
        trans_gdf = trans_gdf.to_crs(crs)

        transformer = Transformer.from_crs(src_crs, crs, always_xy=True)

        # Specific operation for from-coordinates list to-LineString geometric object conversion
        def transform_coordinates(coord_list):
            transformed_coords = [transformer.transform(x, y) for x, y in coord_list]
            return LineString(transformed_coords)

        lines_df['geometry'] = lines_df['coordinates'].apply(transform_coordinates)
        lines_gdf = gpd.GeoDataFrame(lines_df, geometry='geometry', crs=crs)
        lines_gdf = lines_gdf.drop(columns=['coordinates'])

        # Filtering elements inside the study case bounding box
        def filter_by_bbox(gdf, bounding_box):
            min_lon, min_lat, max_lon, max_lat, min_z, max_z = bounding_box

            bbox = Polygon([(min_lon, min_lat), (max_lon, min_lat), (max_lon, max_lat), (min_lon, max_lat)])

            intersected = gdf[gdf.geometry.apply(lambda geom: bbox.intersects(geom) or bbox.contains(geom))]

            return intersected

        buses_gdf = filter_by_bbox(buses_gdf, bounding_box)
        loads_gdf = filter_by_bbox(loads_gdf, bounding_box)
        gens_gdf = filter_by_bbox(gens_gdf, bounding_box)
        trans_gdf = filter_by_bbox(trans_gdf, bounding_box)
        lines_gdf = filter_by_bbox(lines_gdf, bounding_box)

        return buses_gdf, loads_gdf, gens_gdf, trans_gdf, lines_gdf, switches_df

    # Getting elevations of network objects through APIs, set to default city height ASL in case of failed requests
    def get_elevations(self, gdf, h_slm, max_retry, delay):
        points = [(elem['geometry']) for _, elem in gdf.iterrows()]
        elevs = self.send_get_or_post_request(points, h_slm, max_retry, delay)

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
            else:
                # To be defined what should be done in case of different geometries
                pass

        gdf['geometry'] = updated_geometries
        return gdf

    # Sending requests
    def send_get_or_post_request(self, points, h_slm, max_retry, delay):
        url = "https://api.open-elevation.com/api/v1/lookup"
        batch_size = 100  # number of points to send in each POST request
        elevations = [np.nan] * len(points)  # initialize with NaNs
        retry_count = 0

        while retry_count < max_retry:
            if len(url.encode('utf-8')) <= 1024:
                # GET API
                elevations = self.send_get_request(points, url, delay)
            else:
                # POST API
                elevations = self.send_post_request(points, batch_size)

            if np.isnan(elevations).any():
                print("Retrying failed points...")
                retry_count += 1
                time.sleep(delay)
            else:
                break

        # Filling remaining missing values with default city height ASL values
        elevations = [e if not np.isnan(e) else h_slm for e in elevations]

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

    def send_post_request(self, points, batch_size):
        url = "https://api.open-elevation.com/api/v1/lookup"
        elevations = [np.nan] * len(points)  # initialize with NaNs

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

    def associate_buildings_to_loads(self, gdf, loads_gdf):
        # Projecting coordinates to cartographic for more accurate distance computation
        gdf = gdf.to_crs(epsg=3395)
        loads_gdf = loads_gdf.to_crs(epsg=3395)

        gdf['nearest_load'] = None

        # Neglecting z coordinate for distance computation
        loads_gdf_2d = loads_gdf.copy()
        loads_gdf_2d.geometry = loads_gdf_2d.geometry.apply(lambda geom: Point(geom.x, geom.y))

        # To-2D objects conversion for distance computation
        def to_2d_geometry(geometry):
            if isinstance(geometry, Point):
                # exterior_coords = [(x, y) for x, y, _ in geometry.coords]
                # return Point(exterior_coords)
                pass
            elif isinstance(geometry, Polygon):
                exterior_coords = [(x, y) for x, y, _ in geometry.exterior.coords]
                return Polygon(exterior_coords)
            elif isinstance(geometry, MultiPolygon):
                polygons = []
                for poly in geometry:
                    exterior_coords = [(x, y) for x, y, _ in poly.exterior.coords]
                    polygons.append(Polygon(exterior_coords))
                return MultiPolygon(polygons)
            else:
                # To be defined what it should be done in case of different geometries
                pass

        for building_idx, building_row in gdf.iterrows():
            building_geometry = building_row.geometry

            building_geometry_2d = to_2d_geometry(building_geometry)

            # Distance computation between buildings and loads for building nearest load selection
            loads_gdf_2d['distance'] = loads_gdf_2d.geometry.distance(building_geometry_2d)
            nearest_load = loads_gdf_2d['distance'].idxmin()
            loads_gdf_2d.drop(columns=['distance'], inplace=True)

            gdf.at[building_idx, 'nearest_load'] = nearest_load

        load_associations = {(load_idx + 1): [] for load_idx in loads_gdf.index}

        for building_idx, nearest_load in gdf['nearest_load'].items():
            load_associations[nearest_load + 1].append(f"building{building_idx + 1}")

        return load_associations

    # Mapping network data according to the Utility Network extension schema
    def map_ext(self, path, crs, zone, city, h_slm, bounding_box, lod):
        buses_gdf, loads_gdf, gens_gdf, trans_gdf, lines_gdf, switches_df = self.geometric_operations(path, crs, zone, bounding_box)
        buses_gdf = self.get_elevations(buses_gdf, h_slm, max_retry=10, delay=0.5)
        loads_gdf = self.get_elevations(loads_gdf, h_slm, max_retry=10, delay=0.5)
        gens_gdf = self.get_elevations(gens_gdf, h_slm, max_retry=10, delay=0.5)
        trans_gdf = self.get_elevations(trans_gdf, h_slm, max_retry=10, delay=0.5)
        lines_gdf = self.get_elevations(lines_gdf, h_slm, max_retry=10, delay=0.5)

        load_associations = self.associate_buildings_to_loads(self.buildings_gdf, loads_gdf)

        # Equally-sized lists creation for plotting purposes
        self.un_gdf_list = [buses_gdf, loads_gdf, gens_gdf, trans_gdf, lines_gdf]
        self.un_elems_labels = ['buses', 'loads', 'generators', 'transformers', 'lines']
        self.colors = ['red', 'green', 'purple', 'orange', 'brown']

        network = {
            f"mvGrid{city}":
                {
                    "type": "+Network",
                    "attributes":
                        {
                            "class": "MediumVoltageNetwork",
                            "function": "supply",
                            "usage": "supply",
                            "transportedMedium":
                                {
                                    "type": "+AbstractCommodity"
                                }
                        }
                }
        }
        self.un_dict.update(network)

        featureNetwork = {
            f"featureGraph{city}": {
                "type": "+FeatureGraph",
                "attributes":
                    {
                        "node": list(buses_gdf['name']),
                        "interiorFeatureLink": lines_gdf.loc[(lines_gdf['from_bus'].astype(int).isin(buses_gdf.index)) & (lines_gdf['to_bus'].astype(int).isin(buses_gdf.index)), 'name'].tolist()
                    },
                "children": list(buses_gdf['name']) + lines_gdf.loc[(lines_gdf['from_bus'].astype(int).isin(buses_gdf.index)) & (lines_gdf['to_bus'].astype(int).isin(buses_gdf.index)), 'name'].tolist()
            }
        }

        self.un_dict.update(featureNetwork)

        for b, bus_elem in buses_gdf.iterrows():
            nodeValue = "exterior"

            bus = {
                bus_elem['name']: {
                        "type": "+Node",
                        "attributes":
                            {
                                "NodeValue": nodeValue,
                                "nominalVoltage": {
                                    "value": round(float(bus_elem['vn_kv']), 3),
                                    "uom": "kV"  # uom to be checked
                                }
                            },
                        "geometry":
                            [
                                {
                                    "type": "MultiPoint",
                                    "lod": lod,
                                    "boundaries":
                                        [
                                            bus_elem['geometry'].coords[0]
                                        ]
                                }
                            ],
                        "parents":
                            [
                                f"featureGraph{city}"
                            ]
                    }
                }
            self.un_dict.update(bus)

        for l, line_elem in lines_gdf.iterrows():
            if int(line_elem['from_bus']) in buses_gdf.index and int(line_elem['to_bus']) in buses_gdf.index:
                link = {
                    line_elem['name'] : {
                        "type": "+InteriorFeatureLink",
                        "attributes":
                            {
                                "start": buses_gdf.loc[int(line_elem['from_bus']), 'name'],
                                "end": buses_gdf.loc[int(line_elem['to_bus']), 'name'],
                                "length": {
                                    "value": round(float(line_elem['length_km_RNM']), 3),
                                    "uom": "km"
                                },
                                "r": {
                                    "value": float(line_elem['r_ohm_per_km']),
                                    "uom": "ohm/km"
                                },
                                "x": {
                                    "value": float(line_elem['x_ohm_per_km']),
                                    "uom": "ohm/km"
                                },
                                "c": {
                                    "value": float(line_elem['c_nf_per_km'] * 1000),
                                    "uom": "pF/km"
                                },
                                "g" : {
                                    "value": float(line_elem['g_us_per_km'] * 1000),
                                    "uom": "nS/km"
                                },
                                "iMax": {
                                    "value": float(line_elem['max_i_ka']),
                                    "uom": "kA"
                                },
                                "disconnectFrequency": {
                                    "value": float(line_elem['df']),
                                    "uom": "Hz"
                                },
                                "maximumLoadingPercent": int(line_elem['max_loading_percent']),
                                "inService": bool(line_elem['in_service'])
                            },
                        "geometry":
                            [
                                {
                                    "type": "MultiLineString",
                                    "lod": lod,
                                    "boundaries":
                                        [
                                            list(line_elem['geometry'].coords)
                                        ]
                                }
                            ],
                        "parents":
                            [
                                f"featureGraph{city}"
                            ]
                    }
                }
                self.un_dict.update(link)

        for ld, load_elem in loads_gdf.iterrows():
            if int(load_elem['bus']) in buses_gdf.index:
                load = {
                    f"load{ld + 1}": {
                        "type": "+AbstractNetworkFeature",
                        "attributes":
                            {
                                "function": "disposal",
                                "usage": "disposal",
                                "bus": buses_gdf.loc[int(load_elem['bus']), 'name'],
                                "activePower": {
                                    "value": float(load_elem['p_mw']),
                                    "uom": "MW"
                                },
                                "reactivePower": {
                                    "value": float(load_elem['q_mvar']),
                                    "uom": "MVAR"
                                },
                                "totalPower": {
                                    "value": int(load_elem['kW']),
                                    "uom": "kW"
                                },
                                "constantZPercent": int(load_elem['const_z_percent']),
                                "constantIPercent": int(load_elem['const_i_percent']),
                                "lvPods": int(load_elem['LV_pods']),
                                "type": load_elem['type'],
                                "controllable": bool(load_elem['controllable']),
                                "inService": bool(load_elem['in_service']),
                                "buildings": load_associations[ld + 1]
                            },
                        "geometry":
                            [
                                {
                                    "type": "MultiPoint",
                                    "lod": lod,
                                    "boundaries":
                                        [
                                            load_elem['geometry'].coords[0]
                                        ]
                                }
                            ]
                    }
                }
                self.un_dict.update(load)

        for g, gen_elem in gens_gdf.iterrows():
            if gen_elem['bus'] in buses_gdf.index:
                generator = {
                    f"generator{g + 1}": {
                        "type": "+AbstractNetworkFeature",
                        "attributes": {
                            "function": "supply",
                            "usage": "supply",
                            "bus": buses_gdf.loc[int(gen_elem['bus']), 'name'],
                            "activePower": {
                                "value": float(gen_elem['p_mw']),
                                "uom": "MW"
                            },
                            "reactivePower": {
                                "value": float(gen_elem['q_mvar']),
                                "uom": "MVAR"
                            },
                            "apparentNominalPower": {
                                "value": float(gen_elem['sn_mva']),
                                "uom": "MVA"
                            },
                            "type": gen_elem['type'],
                            "currentSource": bool(gen_elem['current_source']),
                            "controllable": bool(gen_elem['controllable']),
                            "inService": bool(gen_elem['in_service'])
                        },
                        "geometry":
                            [
                                {
                                    "type": "MultiPoint",
                                    "lod": lod,
                                    "boundaries":
                                        [
                                            gen_elem['geometry'].coords[0]
                                        ]
                                }
                            ]
                    }
                }
                self.un_dict.update(generator)

        for s, switch_elem in switches_df.iterrows():
            if int(switch_elem['bus']) in buses_gdf.index and int(switch_elem['element']) in buses_gdf.index:
                switch = {
                    switch_elem['name']: {
                        "type": "+InterFeatureLink",
                        "attributes": {
                            "InterFeatureLinkValue": "connects",
                            "busClosed": buses_gdf.loc[int(switch_elem['bus']), 'name'],
                            "busOpen": buses_gdf.loc[int(switch_elem['element']), 'name'],
                            "type": switch_elem['type'],
                            "isClosed": bool(switch_elem['closed'])
                        }
                    }
                }
                self.un_dict.update(switch)

        for tr, transform_elem in trans_gdf.iterrows():
            if transform_elem['hv_bus'] in buses_gdf.index and transform_elem['lv_bus'] in buses_gdf.index:
                transformer = {
                    f"transformer{tr + 1}": {
                        "type": "+AbstractNetworkFeature",
                        "attributes": {
                            "hvBus": buses_gdf.loc[int(transform_elem['hv_bus']), 'name'],
                            "lvBus": buses_gdf.loc[int(transform_elem['hv_bus']), 'name'],
                            "nominalVoltageHvBus": {
                                "value": float(transform_elem['vn_hv_kv']),
                                "uom": "kV"
                            },
                            "nominalVoltageLvBus": {
                                "value": float(transform_elem['vn_lv_kv']),
                                "uom": "kV"
                            },
                            "noLoadActivePowerLoss": {
                                "value": float(transform_elem['pfe_kw']),
                                "uom": "kW"
                            },
                            "disconnectFrequency": {
                                "value": float(transform_elem['df']),
                                "uom": "Hz"
                            },
                            "nominalVoltagePercent": int(transform_elem['vk_percent']),
                            "nominalNoLoadVoltagePercent": round(float(transform_elem['vkr_percent']), 2),
                            "maximumLoadingPercent": int(transform_elem['max_loading_percent']),
                            "tapStepPercent": float(transform_elem['tap_step_percent']),
                            "tapPosition": str(transform_elem['tap_pos']),
                            "tapPhaseShifter": bool(transform_elem['tap_phase_shifter']),
                            "onLoadTapChanger": bool(transform_elem['oltc']),
                            "inService": bool(transform_elem['in_service']),
                        },
                        "geometry":
                            [
                                {
                                    "type": "MultiPoint",
                                    "lod": lod,
                                    "boundaries":
                                        [
                                            transform_elem['geometry'].coords[0]
                                        ]
                                }
                            ]
                    }
                }
                self.un_dict.update(transformer)

        # None or NaN values checking and replacement
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

    # Plot city map with both buildings and network elements
    def plot_city_map(self, city):
        fig, ax = plt.subplots(figsize=(10, 10))

        self.buildings_gdf.plot(ax=ax, color='blue', edgecolor='black', label='buildings', aspect=1)

        for un_gdf, color, label in zip(self.un_gdf_list, self.colors, self.un_elems_labels):
            un_gdf.plot(ax=ax, color=color, linewidth=2, label=label, aspect=1)

        plt.title(f"Buildings and Utility Network {city}")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")

        ax.legend()

        plt.savefig(f"output/{city}_buildings_utility_network.png")

        plt.show()




