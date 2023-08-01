import pandas as pd
import numpy as np
import random

class BuildingTypeClassifier:

    def __init__(self, gdfs, sez_det_data):
        self.gdfs = gdfs
        self.sez_det_data = sez_det_data

    def classify_building(self, columns, sez_id, pop_columns, building_target, filtering_values, en_dem_per_hh):
        for i, df in self.gdfs.items():
            row = self.sez_det_data.loc[self.sez_det_data[sez_id[0]] == i]
            if row['E3'].iloc[0] != 0:
                corr_fact = len(df) / float(row['E3'].iloc[0])
            else:
                corr_fact = 1
            no_of_families = float(row[pop_columns[0]].iloc[0]) * corr_fact
            family_uid_list = []
            if no_of_families > 0:
                for k in range(int(no_of_families)):
                    family_uid_list.append(f"SEZ{str(int(i))}FAM{str(k)}")
                random.shuffle(family_uid_list)
            population = float(row[pop_columns[1]].iloc[0]) * corr_fact

            def calculate_building_GFA(building):  # gross floor area
                area = building[columns[5]]
                levels = float(building[columns[4]])
                if levels >= 1:
                    gross_floor_area = area * levels
                else:
                    gross_floor_area = area * (levels + 1)
                return round(gross_floor_area, 2)

            df[columns[6]] = df.apply(calculate_building_GFA, axis=1)

            total_GFA = df[columns[6]].sum()

            def calculate_building_no_of_families(bld_elem):
                building_GFA = bld_elem[columns[6]]
                no_of_families_per_building = round(((building_GFA * no_of_families) / total_GFA))
                return no_of_families_per_building

            df[columns[8]] = df.apply(calculate_building_no_of_families, axis=1)

            def calculate_building_no_of_people(bldng_elem):
                building_GFA = bldng_elem[columns[6]]
                if bldng_elem[columns[8]] == 0:
                    no_of_people_per_building = 0
                else:
                    no_of_people_per_building = round(((building_GFA * population) / total_GFA))
                return no_of_people_per_building

            df[columns[9]] = df.apply(calculate_building_no_of_people, axis=1)

            def calculate_energy_demand(build_elem):
                en_dem = 0
                if build_elem[columns[14]] and build_elem[columns[15]]:
                    en_dem = en_dem_per_hh["energy_demand"]["electricity"] + en_dem_per_hh["energy_demand"]["cooling"] + en_dem_per_hh["energy_demand"]["heating"]
                elif build_elem[columns[14]] and not build_elem[columns[15]]:
                    en_dem = en_dem_per_hh["energy_demand"]["electricity"] + en_dem_per_hh["energy_demand"]["cooling"]
                elif not build_elem[columns[14]] and build_elem[columns[15]]:
                    en_dem = en_dem_per_hh["energy_demand"]["electricity"] + en_dem_per_hh["energy_demand"]["heating"]
                elif not build_elem[columns[14]] and not build_elem[columns[15]]:
                    en_dem = en_dem_per_hh["energy_demand"]["electricity"]
                building_families = build_elem[columns[8]]
                energy_demand = int(building_families * en_dem)
                return energy_demand

            energy_mask = df[columns[16]].isna()

            df.loc[energy_mask, columns[16]] = df[energy_mask].apply(calculate_energy_demand, axis=1)


            for idx, building_elem in enumerate(df[columns[3]]):
                if building_elem not in filtering_values["not_specified"]:
                    if building_elem in filtering_values["AB"]:
                        df[columns[7]].iloc[idx] = "AB" # apartment block
                    elif building_elem in filtering_values["SFH"]:
                        df[columns[7]].iloc[idx] = "SFH" # single family house
                    elif building_elem in filtering_values["MFH"]:
                        df[columns[7]].iloc[idx] = "MFH"  # multifamily house
                    elif building_elem in filtering_values["TH"]:
                        df[columns[7]].iloc[idx] = "TH" # terraced house
                else:
                    no_of_floors = float(df[columns[4]].iloc[idx])
                    if no_of_floors >= 3:
                        df[columns[7]].iloc[idx] = "AB"
                    else:
                        if df[columns[8]].iloc[idx] <= 1:
                            df[columns[7]].iloc[idx] = "SFH"
                        else:
                            df[columns[7]].iloc[idx] = "MFH"
                df[columns[3]].iloc[idx] = building_target


        return self.gdfs




