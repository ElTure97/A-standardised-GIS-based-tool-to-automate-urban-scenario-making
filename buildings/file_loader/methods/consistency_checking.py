import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon, Point, Polygon, shape
from pyproj import CRS

''' Consistency checker for correct specified Coordinate Reference System (CRS) setting and 
altitude coordinates (if there) storing. '''
class ConsistencyChecker:
    def __init__(self, gdf, crs):
        self.gdf = gdf
        self.crs = crs

    def check_indexing(self):
        if isinstance(self.gdf.index, pd.MultiIndex):
            self.gdf = self.gdf.reset_index(level=list(range(self.gdf.index.nlevels)), drop=True)
        return self.gdf

    def check_projection(self):
        coord_ref_system = CRS.from_string(self.crs)
        self.gdf = self.gdf.to_crs(coord_ref_system)
        return self.gdf

    def check_geometry(self):
        z_coord = []
        for i in range(len(self.gdf['geometry'])):
            z_coord.append([])
            geom = self.gdf['geometry'].iloc[i]
            if isinstance(geom, Point):
                coords = list(geom.coords)
                sum_h = 0
                for j in range(len(coords)):
                    if len(coords[j]) > 2:
                        sum_h += coords[j][2]
                        coords[j] = coords[j][:2]
                    z_coord[i] = sum_h / len(coords)
                new_point = Point(coords)
                self.gdf['geometry'].iloc[i] = new_point
            elif isinstance(geom, Polygon):
                coords = list(geom.exterior.coords)
                sum_h = 0
                for j in range(len(coords)):
                    if len(coords[j]) > 2:
                        sum_h += coords[j][2]
                        coords[j] = coords[j][:2]
                    z_coord[i] = sum_h / len(coords)
                new_poly = Polygon(coords)
                self.gdf['geometry'].iloc[i] = new_poly
            elif isinstance(geom, MultiPolygon):
                polygons = list(geom.geoms)
                new_polygons = []
                for p in range(len(polygons)):
                    z_coord[i].append([])
                    coords = list(polygons[p].exterior.coords)
                    sum_h = 0
                    for j in range(len(coords)):
                        if len(coords[j]) > 2:
                            sum_h += coords[j][2]
                            coords[j] = coords[j][:2]
                        z_coord[i][p] = sum_h / len(coords)
                    new_poly = Polygon(coords)
                    new_polygons.append(new_poly)
                new_mp = MultiPolygon(new_polygons)
                self.gdf['geometry'].iloc[i] = new_mp
            else:
                # to be defined what it should be done in case of different geometry type with respect to Point, Polygon or MultiPolygon
                z_coord[i].append([])
        return self.gdf, z_coord

    def check_consistency(self):
        self.gdf = self.check_indexing()
        self.gdf, z_coord = self.check_geometry()
        gdf = self.check_projection()
        return gdf, z_coord
