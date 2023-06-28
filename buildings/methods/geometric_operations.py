import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from .outliers_filtering import *
from rtree import index

class GeomOperator:

    def __init__(self, osm_data, shp_data, sez_data, sez_det_data):
        self.osm_data = osm_data
        self.shp_data = shp_data
        self.sez_data = sez_data
        self.sez_det_data = sez_det_data


    def join_gdf(self, target, columns, filtering_values, id):
        filter_values = set(val for bld_val in filtering_values.values() for val in bld_val)
        filtered_data = self.osm_data[self.osm_data[target].isin(filter_values)].copy()

        osm_geometries = filtered_data[columns[0]]

        idx = index.Index()
        for i, row in self.sez_data.iterrows():
            geom = row[columns[0]]
            idx.insert(i, geom.bounds)

        matching_sez = []
        for osm_geometry in osm_geometries:
            intersected_sez = list(idx.intersection(osm_geometry.bounds))
            for i in intersected_sez:
                if osm_geometry.intersects(self.sez_data.loc[i, columns[0]]):
                    matching_sez.append(self.sez_data.loc[i, id[1]])
                    break

        filtered_sez_data = []
        for sez_id in matching_sez:
            sez_geometry = self.sez_data.loc[self.sez_data[id[1]] == sez_id, columns[0]].values[0]
            filtered_sez_data.extend(self.shp_data[self.shp_data.intersects(sez_geometry)].values.tolist())

        filtered_sez_data = gpd.GeoDataFrame(filtered_sez_data, columns=self.shp_data.columns)

        filtered_data = filtered_data.loc[filtered_data.intersects(filtered_sez_data.unary_union)]

        filtered_data[columns[3]] = filtered_data[target]
        osm_gdf = filtered_data.loc[:, columns]
        return osm_gdf

    def get_shp_data(self, target, columns, fields, filtering_values, target_crs, id):
        osm_gdf = self.join_gdf(target, columns, filtering_values, id)
        print("Geometric operations in progress...")
        def map_height(row):
            intersecting_features_osm = self.osm_data.loc[self.osm_data.intersects(row.geometry)]
            intersecting_features_shp = self.shp_data.loc[self.shp_data.intersects(row.geometry)]

            # check if height data are available in both osm_data and shp_data
            if not intersecting_features_osm.empty and not intersecting_features_shp.empty:
                h_osm = intersecting_features_osm[columns[1]].values[0]
                h_shp = intersecting_features_shp[fields[0]].values[0]
                try:
                    h_osm = float(h_osm)
                except:
                    h_osm = np.nan
                try:
                    h_shp = float(h_shp)
                except:
                    h_shp = np.nan
                if not np.isnan(h_osm) and not np.isnan(h_shp):
                    avg_height = np.mean([h_osm, h_shp])
                    return round(avg_height, 1)
                elif not np.isnan(h_osm):
                    return round(h_osm, 1)
                else:
                    return round(h_shp, 1)
            # check if height data is available only in osm_data
            elif not intersecting_features_osm.empty:
                return intersecting_features_osm[columns[1]].values[0]
            # check if height data is available only in shp_data
            elif not intersecting_features_shp.empty:
                return intersecting_features_shp[fields[0]].values[0]
            # if no height data is available, return nan
            else:
                return np.nan

        osm_gdf[columns[1]] = osm_gdf.apply(map_height, axis=1)

        def map_area(row):
            intersecting_features_osm = self.osm_data.loc[self.osm_data.intersects(row.geometry)]
            intersecting_features_shp = self.shp_data.loc[self.shp_data.intersects(row.geometry)]

            # check if area data is available in both osm_data and shp_data
            if not intersecting_features_osm.empty and not intersecting_features_shp.empty:
                area_osm = intersecting_features_osm[columns[5]].values[0]
                area_shp = intersecting_features_shp[fields[2]].values[0]
                try:
                    area_osm = float(area_osm)
                except:
                    area_osm = np.nan
                try:
                    area_shp = float(area_shp)
                except:
                    area_shp = np.nan

                if not np.isnan(area_osm) and not np.isnan(area_shp):
                    avg_area = np.mean([area_osm, area_shp])
                    return round(avg_area, 1)
                elif not np.isnan(area_osm):
                    return round(area_osm, 2)
                else:
                    return round(area_shp, 2)
            # check if area data is available only in osm_data
            elif not intersecting_features_osm.empty:
                return intersecting_features_osm[columns[5]].values[0]
            # check if area data is available only in shp_data
            elif not intersecting_features_shp.empty:
                return intersecting_features_shp[fields[2]].values[0]
            # if no area data is available, calculate area from polygon
            else:
                polygon = row.geometry.to_crs(target_crs)
                area = Polygon(polygon.exterior.coords).area
                return round(area, 2)

        osm_gdf[columns[5]] = osm_gdf.apply(map_area, axis=1)
        return osm_gdf

    def place_building(self, target, columns, fields, filtering_values, id, target_crs, z_score):
        sez_gdfs = {}
        gdf = self.get_shp_data(target, columns, fields, filtering_values, target_crs, id)
        gdf_obj = OutliersFilter(gdf)
        gdf_filtered = gdf_obj.filter_outliers(columns, z_score)
        not_in_poly_gdf = gdf_filtered.copy()
        for index, row in self.sez_data.iterrows():
            poly = row[columns[0]]
            gdf_in_poly = not_in_poly_gdf[not_in_poly_gdf.intersects(poly)]
            not_in_poly_gdf.drop(gdf_in_poly.index, inplace=True)
            if not gdf_in_poly.empty:
                sez_gdfs[row[id[1]]] = gdf_in_poly
                print("Building successfully mapped")
        return sez_gdfs, not_in_poly_gdf

