import random
from pyproj import CRS, Proj
from shapely.geometry import MultiPolygon, Point, Polygon
from .json_writer import JSON_Writer

class CityJSONCreator(JSON_Writer):

    def __init__(self, gdf):
        super().__init__(gdf)
        self.headers = list(self.gdf.columns)

        # empty dict
        self.cityjson_data = {
            "type": "CityJSON",
            "version": "1.1",
            "extensions": {},
            "transform": None,
            "metadata": None,
            "CityObjects": {},
            "vertices": None
        }

    def generate_fams_list(self, index, nuts3, lau2, building_target):
        grouped = self.gdf.groupby(self.headers[9])
        first_lett = building_target[0]
        cap_lett = first_lett.upper()
        families_sez_list = []
        self.fams_per_bld = {}
        for census_sez, group in grouped:
            if int(census_sez) < 10:
                cens_sez = f"000{int(census_sez)}"
            elif 9 < int(census_sez) < 100:
                cens_sez = f"00{int(census_sez)}"
            elif 100 < int(census_sez) < 1000:
                cens_sez = f"0{int(census_sez)}"
            else:
                cens_sez = f"{int(census_sez)}"
            total_no_of_families = group[self.headers[7]].sum()
            for f in range(total_no_of_families):
                if f + 1 < 10:
                    families_sez_list.append(f"{nuts3}_{lau2}_{cens_sez}_{cap_lett}_0000{f + 1}")
                elif 9 < f + 1 < 100:
                    families_sez_list.append(f"{nuts3}_{lau2}_{cens_sez}_{cap_lett}_000{f + 1}")
                elif 100 < f + 1 < 1000:
                    families_sez_list.append(f"{nuts3}_{lau2}_{cens_sez}_{cap_lett}_00{f + 1}")
                elif 999 < f + 1 < 10000:
                    families_sez_list.append(f"{nuts3}_{lau2}_{cens_sez}_{cap_lett}_0{f + 1}")
                else:
                    families_sez_list.append(f"{nuts3}_{lau2}_{cens_sez}_{cap_lett}_{f + 1}")
            random.shuffle(families_sez_list)
            for idx, bld_elem in group.iterrows():
                self.fams_per_bld[idx] = []
                for fam in range(bld_elem[self.headers[7]]):
                    self.fams_per_bld[idx].append(families_sez_list[-1])
                    families_sez_list.pop(-1)
        return self.fams_per_bld[index]

    def convert_to_utm(self, point, source_crs, zone):
        utm = Proj(proj='utm', zone=zone, ellps='WGS84', preserve_units=False, init=source_crs)

        source = Proj(CRS.from_string(source_crs))

        long, lat = source(point[0], point[1])
        alt = round(point[2], 3)

        east, north = utm(long, lat)
        east = round(east, 3)
        north = round(north, 3)

        return (east, north, alt)

    def create_transform_object(self, bounds):
        # scale factors
        scale = [0.001, 0.001, 0.001]
        # minimum values for translation
        translate = bounds

        self.transform = {
            "scale": scale,
            "translate": translate
        }

        return self.transform

    def compute_no_of_accomodations(self, bld_elem):
        no_of_people = float(bld_elem[self.headers[8]])
        no_of_fams = float(bld_elem[self.headers[7]])
        no_of_floors = int(bld_elem[self.headers[3]])
        min_gfa_per_pers = 60  # default value of net area per person
        not_usable_space = 30  # default value of not usable area per floor
        corr_factor = 3 / 2  # correction factor
        gfa = float(bld_elem[self.headers[5]])
        if no_of_fams != 0:
            no_of_people_per_fam = no_of_people / no_of_fams
            gfa_per_fam = gfa / no_of_fams
            if gfa_per_fam / no_of_people_per_fam > min_gfa_per_pers:
                no_of_accomodations = round(gfa / gfa_per_fam)
            else:
                no_of_accomodations = round(gfa / (min_gfa_per_pers * no_of_people_per_fam))
        else:
            # a correction factor is applied to take into account also not usable space
            no_of_accomodations = round(gfa / (no_of_floors * corr_factor * min_gfa_per_pers))

        avg_area = round(((gfa - (no_of_floors * not_usable_space))/no_of_accomodations), 2)

        return no_of_accomodations, avg_area

    def create_CJ(self, bbox, bounds, ext_name, ext, lod, crs, crs_url, zone, city, nation, nuts3, lau2, building_target):
        self.cityjson_data["vertices"] = []
        for index, row in self.gdf.iterrows():
            geom = row[self.headers[12]]
            if isinstance(geom, Point):
                continue
            elif isinstance(geom, Polygon):
                coords = [list(geom.exterior.coords)]
                coords[0] = [x for i, x in enumerate(coords[0]) if x not in coords[0][:i]]
                coords_base = []
                for coord in coords[0]:
                    new_coord_z = coord[2] - self.gdf.loc[index, self.headers[0]]
                    new_coord = list(coord)
                    new_coord[2] = new_coord_z
                    coords_base.append(tuple(new_coord))
                coords[0] = coords[0] + coords_base
                for cr in range(len(coords[0])):
                    coords[0][cr] = self.convert_to_utm(coords[0][cr], crs, zone)
                self.cityjson_data["vertices"] = self.cityjson_data["vertices"] + coords[0]
                geom_type = "Solid"
            elif isinstance(geom, MultiPolygon):
                coords = []
                polygons = list(geom.geoms)
                for p in range(len(polygons)):
                    coords.append(list(polygons[p].exterior.coords))
                p = len(coords)
                for poly in range(p):
                    coords[poly] = [x for i, x in enumerate(coords[poly]) if x not in coords[poly][:i]]
                    coords_base = []
                    for coord in coords[poly]:
                        new_coord_z = coord[2] - self.gdf.loc[index, self.headers[0]]
                        new_coord = list(coord)
                        new_coord[2] = new_coord_z
                        coords_base.append(tuple(new_coord))
                    coords[poly] = coords[poly] + coords_base
                    for cr in range(len(coords[poly])):
                        coords[poly][cr] = self.convert_to_utm(coords[poly][cr], crs, zone)
                    self.cityjson_data["vertices"] = self.cityjson_data["vertices"] + coords[poly]
                geom_type = "CompositeSolid"
            else:
                # to be defined what it should be done in case of different geometry type with respect to Point, Polygon or MultiPolygon
                coords = None
                geom_type = None

            bound = []
            if len(coords) == 1:
                bound.append([])
                poly_size = int(len(coords[0])/2)
                for c in range(poly_size + 1):
                    bound[0].append([[]])
                for crd in range(poly_size):
                    bound[0][0][0].append(self.cityjson_data["vertices"].index(coords[0][crd]))
                i = 0
                for j in range(1, len(bound[0])):
                    current = bound[0][0][0][i]
                    next = bound[0][0][0][(i + 1) % len(bound[0][0][0])]
                    bound[0][j][0].append(current)
                    bound[0][j][0].append(next)
                    bound[0][j][0].append(next + int(len(coords[0])/2))
                    bound[0][j][0].append(current + int(len(coords[0])/2))
                    i += 1
            else:
                for pol in range(len(coords)):
                    bound.append([[]])
                    poly_size = int(len(coords[pol])/2)
                    for c in range(poly_size + 1):
                        bound[pol][0].append([[]])
                    for crd in range(poly_size):
                        bound[pol][0][0][0].append(self.cityjson_data["vertices"].index(coords[pol][crd]))
                    i = 0
                    for j in range(1, len(bound[pol][0])):
                        current = bound[pol][0][0][0][i]
                        next = bound[pol][0][0][0][(i + 1) % len(bound[pol][0][0][0])]
                        bound[pol][0][j][0].append(current)
                        bound[pol][0][j][0].append(next)
                        bound[pol][0][j][0].append(next + int(len(coords[pol]) / 2))
                        bound[pol][0][j][0].append(current + int(len(coords[pol]) / 2))
                        i += 1

            # create a dict for each building
            building = {
                "type": "Building",
                "attributes": {
                    "name": f"building-{index + 1}",
                    "censusSection": int(row[self.headers[9]]),
                    # "measuredHeight": float(row[self.headers[0]]),
                    "yearOfConstruction": int(row[self.headers[1]]),
                    # "function": row[self.headers[2]],
                    "storeysAboveGround": int(row[self.headers[3]]),
                    "footprintArea": float(row[self.headers[4]]),
                    # "grossFloorArea": float(row[self.headers[5]]),
                    "families": int(row[self.headers[7]]),
                    "familiesID": self.generate_fams_list(index, nuts3, lau2, building_target),
                    "occupants": int(row[self.headers[8]]),
                    "accomodations": self.compute_no_of_accomodations(row)[0],
                    "avgArea": self.compute_no_of_accomodations(row)[1],
                    # "tabulaBuildingType": row[self.headers[6]],
                    "tabulaTypeUID": row[self.headers[10]],
                    "POD": row[self.headers[11]]
                },

                "geometry": [{
                    "type": geom_type,
                    "lod": lod,
                    "boundaries": bound
                }]
            }

            # add energy attributes --> keep track of extension position in the list of extensions
            building["attributes"].update(ext[0][index])

            # for i in range(len(ext_name)):
            #     building["attributes"].update(ext[i][index])

            #     building["attributes"][f"+{list(ext_name[i].keys())[0]}"] = ext[i][index]

            # part of the code specific for energy extension integration
            if building["geometry"][0]["type"] == "Solid":
                building["attributes"]["+energy-referencePoint"] = str(bound[0][0][0][0]) # default value
            else:
                building["attributes"]["+energy-referencePoint"] = str(bound[0][0][0][0][0])  # default value

            # add building object to CityObjects dict
            self.cityjson_data["CityObjects"][f"id-{index + 1}"] = building
            print(f"Building {index + 1} succesfully added to cityjson!")

        for ade_elem in ext_name:
            self.cityjson_data["extensions"][list(ade_elem.values())[0]["name"]] = {
                "url": list(ade_elem.values())[0]["url"],
                "version": list(ade_elem.values())[0]["version"]
            }
        self.cityjson_data["transform"] = self.create_transform_object(bounds)

        # fill metadata
        lon_min, lat_min, lon_max, lat_max, z_min, z_max = bbox
        min_point = (lon_min, lat_min, z_min)
        max_point = (lon_max, lat_max, z_max)

        transf_min_point = self.convert_to_utm(min_point, crs, zone)
        transf_max_point = self.convert_to_utm(max_point, crs, zone)
        ltmin = list(transf_min_point)
        ltmax = list(transf_max_point)
        bbox_def = ltmin + ltmax

        metadata_dict = {
            "geographicalExtent": bbox_def,
            "referenceSystem": crs_url,
            "title": f"Buildings in LoD{lod} of {city}, {nation}",

        }

        self.cityjson_data["metadata"] = metadata_dict
        for v in range(len(self.cityjson_data["vertices"])):
            self.cityjson_data["vertices"][v] = list(self.cityjson_data["vertices"][v])
            for i in range(len(self.cityjson_data["vertices"][v])):
                vert = self.cityjson_data["vertices"][v][i]
                transl = self.cityjson_data["transform"]["translate"][i]
                scal = self.cityjson_data["transform"]["scale"][i]
                self.cityjson_data["vertices"][v][i] = round((vert - transl)/scal)
        return self.cityjson_data

    def write_json(self, bbox, bounds, ext_name, ext, lod, crs, crs_url, zone, city, nation, building_target, nuts3, lau2):
        path = f"output/{city}_{building_target}.json"
        super().write_json(path, self.create_CJ(bbox, bounds, ext_name, ext, lod, crs, crs_url, zone, city, nation, nuts3, lau2, building_target))