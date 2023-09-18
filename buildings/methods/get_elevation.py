import requests
from shapely.geometry import box, Point, Polygon, MultiPolygon
from pyproj import CRS, Proj, Transformer
import time

''' Mapping elevation by discretizing the bounding box into cells according to the specified resolution and taking
the height of their centroids as reference for getting buildings height as average of heights associated with each point
of the Polygon or MultiPolygon object. The resulting height will be mapped as z coordinate (same for all points), 
expressed as height above the sea level. '''
class ElevationMapper:
    def __init__(self, gdf):
        self.gdf = gdf

    def get_3d_coordinates(self, crs, lat, lon, alt_slm, building_height):
        source_crs = CRS.from_string("+proj=latlong +datum=WGS84 +ellps=WGS84 +geoidgrids=egm96_15.gtx")
        target_crs = CRS.from_string(crs)

        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        transformed_coords = transformer.transform(lat, lon, alt_slm + building_height)

        return transformed_coords[2]

    def get_elevation(self, crs, bbox, res, h_slm, columns):
        cells, cells_elevs = self.divide_bbox_into_cells(crs, bbox, h_slm, res)
        for i in range(len(self.gdf[columns[0]])):
            geom = self.gdf[columns[0]].iloc[i]
            h_bld = self.gdf[columns[1]].iloc[i]
            if isinstance(geom, Point):
                coords = list(geom.coords)
                lat, lon = coords[0][1], coords[0][0]
                terrain_elevation = self.get_elevation_for_point(crs, cells, cells_elevs, lat, lon, h_slm)
                z_coord = terrain_elevation + h_bld
                coords[0] = (lon, lat, z_coord)
                new_point = Point(coords)
                self.gdf[columns[0]].iloc[i] = new_point
            elif isinstance(geom, Polygon):
                coords = list(geom.exterior.coords)
                new_coords = []
                z_coords = []
                for j in range(len(coords)):
                    lat, lon = coords[j][1], coords[j][0]
                    terrain_elevation = self.get_elevation_for_point(crs, cells, cells_elevs, lat, lon, h_slm)
                    z_coord = terrain_elevation + h_bld
                    z_coords.append(z_coord)
                    sum_z = 0
                for z in range(len(z_coords)):
                    sum_z += z_coords[z]
                new_z_coord = sum_z / len(z_coords)
                for j in range(len(coords)):
                    lat, lon = coords[j][1], coords[j][0]
                    new_coords.append((lon, lat, new_z_coord))
                new_poly = Polygon(new_coords)
                self.gdf[columns[0]].iloc[i] = new_poly
            elif isinstance(geom, MultiPolygon):
                polygons = list(geom.geoms)
                new_polygons = []
                for p in range(len(polygons)):
                    coords = list(polygons[p].exterior.coords)
                    new_coords = []
                    z_coords = []
                    for j in range(len(coords)):
                        lat, lon = coords[j][1], coords[j][0]
                        terrain_elevation = self.get_elevation_for_point(crs, cells, cells_elevs, lat, lon, h_slm)
                        z_coord = terrain_elevation + h_bld
                        z_coords.append(z_coord)
                    sum_z = 0
                    for z in range(len(z_coords)):
                        sum_z += z_coords[z]
                    new_z_coord = sum_z/len(z_coords)
                    for j in range(len(coords)):
                        lat, lon = coords[j][1], coords[j][0]
                        new_coords.append((lon, lat, new_z_coord))
                    new_poly = Polygon(new_coords)
                    new_polygons.append(new_poly)
                new_mp = MultiPolygon(new_polygons)
                self.gdf[columns[0]].iloc[i] = new_mp
            else:
                # To be defined what it should be done in case of different geometry type with respect to Point, Polygon or MultiPolygon
                pass
            print(f"Z coordinate successfully mapped to building {i + 1}")
        return self.gdf, cells

    def get_elevation_for_point(self, crs, cells, cells_elevs, lat, lon, h_slm):
        source_crs = CRS.from_string(crs)
        target_crs = CRS.from_string("+proj=latlong +datum=WGS84 +ellps=WGS84 +geoidgrids=egm96_15.gtx")
        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        transformed_coords = transformer.transform(lon, lat)

        lon, lat = transformed_coords[0], transformed_coords[1]

        matching_cells = []
        for i, cell in enumerate(cells):
            cell_bbox = box(cell[0], cell[1], cell[2], cell[3])
            if cell_bbox.contains(Point(lon, lat)):
                matching_cells.append(i)

        if len(matching_cells) != 0:
            elevs = [cells_elevs[index] for index in matching_cells]
            average_elevation = sum(elevs) / len(elevs)
            return average_elevation
        else:
            return h_slm

    def get_elevations(self, points, h_slm, max_retry, delay):
        retry_count = 0
        while retry_count < max_retry:
            locations = "|".join([f"{point.y},{point.x}" for point in points])
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations}"
            response = requests.get(url)

            if response.status_code == 200:
                # print("Success!")
                data = response.json()
                elevations = [result["elevation"] for result in data["results"]]
                return elevations
            else:
                print(f"Request failed. New attempt in {delay} s")
                retry_count += 1
                time.sleep(delay)

        elevs = []
        for p in range(len(points)):
            elevs.append(h_slm)
        return elevs

    def divide_bbox_into_cells(self, crs, bbox, h_slm, resolution):
        lon_min, lat_min, lon_max, lat_max = bbox

        source_crs = CRS.from_string(crs)
        target_crs = CRS.from_string("+proj=aeqd +datum=WGS84 +ellps=WGS84")

        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        lon_min_geo, lat_min_geo = transformer.transform(lon_min, lat_min)
        lon_max_geo, lat_max_geo = transformer.transform(lon_max, lat_max)

        lon_cell_count = int((lon_max_geo - lon_min_geo) / resolution)
        lat_cell_count = int((lat_max_geo - lat_min_geo) / resolution)
        cells = []

        for i in range(lon_cell_count):
            for j in range(lat_cell_count):
                lon_start = lon_min_geo + i * resolution
                lat_start = lat_min_geo + j * resolution
                lon_end = lon_start + resolution
                lat_end = lat_start + resolution

                lon_start_geo, lat_start_geo = transformer.transform(lon_start, lat_start, direction="INVERSE")
                lon_end_geo, lat_end_geo = transformer.transform(lon_end, lat_end, direction="INVERSE")

                cell_bbox = (lon_start_geo, lat_start_geo, lon_end_geo, lat_end_geo)
                cells.append(cell_bbox)

        def get_cell_centroids(cells):
            centroids = [Point((cell[0] + cell[2]) / 2, (cell[1] + cell[3]) / 2) for cell in cells]
            return centroids

        cell_centroids = get_cell_centroids(cells)
        self.elevations = self.get_elevations(cell_centroids, h_slm, max_retry=10, delay=0.5)

        return cells, self.elevations

    def get_bbox_z_coords(self):
        return min(self.elevations), max(self.elevations)



