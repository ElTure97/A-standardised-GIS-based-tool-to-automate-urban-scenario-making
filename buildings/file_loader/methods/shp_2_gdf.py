import geopandas as gpd
from shapely.geometry import box

''' ShapeFile data loader '''
class SHP2GeoDF:
    def __init__(self, shapefile, bounding_box, crs):
        self.shapefile = shapefile
        self.bounding_box = bounding_box
        self.crs = crs

    def get_gdf_from_shp(self):
        gdf_shapefile = gpd.read_file(self.shapefile)
        gdf_shapefile = gdf_shapefile.to_crs(self.crs)
        bbox = box(self.bounding_box[0], self.bounding_box[1], self.bounding_box[2], self.bounding_box[3])
        gdf_shp = gdf_shapefile[gdf_shapefile.intersects(bbox)]
        return gdf_shp

