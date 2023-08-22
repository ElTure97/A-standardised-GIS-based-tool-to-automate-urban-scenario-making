import json
import osmnx as ox
import numpy as np
import geopandas as gpd

''' OpenStreetMap data loader '''
class OSM2GeoDF:
    def __init__(self, address, distance, target, required_columns, crs):
        self.address = address
        self.distance = distance
        self.target = target
        self.required_columns = required_columns
        self.crs = crs

    def get_gdf_from_osm(self):
        gdf = ox.geometries.geometries_from_address(self.address, tags={self.target: True}, dist=self.distance)
        gdf.crs = self.crs
        return gdf

    def update_gdf(self, gdf):
        for col in self.required_columns:
            if col not in gdf.columns:
                gdf[col] = np.nan

        # Filling missing values with NaN
        gdf = gdf.fillna(np.nan)
        return gdf




