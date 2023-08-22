import pandas as pd
import numpy as np
import random

class BuildingTypeClassifier:

    def __init__(self, gdfs, sez_det_data):
        self.gdfs = gdfs
        self.sez_det_data = sez_det_data

    ''' Building classification according to TABULA DataSet labels based on parameters previously computed
    inside that function. Energy demand has been estimated too based on available data but not used 
    for building classification. '''
    def classify_building(self, columns, sez_id, pop_columns, building_target, filtering_values, en_dem_per_hh):
        for i, df in self.gdfs.items():
            row = self.sez_det_data.loc[self.sez_det_data[sez_id[0]] == i]
            if row['E3'].iloc[0] != 0:
                corr_fact = len(df) / float(row['E3'].iloc[0])
            else:
                corr_fact = 1
            no_of_families = float(row[pop_columns[0]].iloc[0]) * corr_fact
            population = float(row[pop_columns[1]].iloc[0]) * corr_fact

            def calculate_building_GFA(building):  # Gross Floor Area
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

            def calculate_electricity_energy_demand(bu_elem):
                bu_families = bu_elem[columns[8]]
                return int(en_dem_per_hh["electricity"] * bu_families)

            ele_energy_mask = df[columns[17]].isna()

            df.loc[ele_energy_mask, columns[17]] = df[ele_energy_mask].apply(calculate_electricity_energy_demand, axis=1)

            def calculate_cooling_energy_demand(bui_elem):
                bui_families = bui_elem[columns[8]]
                if bui_elem[columns[14]]:
                    return int(en_dem_per_hh["cooling"] * bui_families)
                else:
                    return 0

            cool_energy_mask = df[columns[18]].isna()

            df.loc[cool_energy_mask, columns[18]] = df[cool_energy_mask].apply(calculate_cooling_energy_demand, axis=1)

            def calculate_heating_energy_demand(buil_elem):
                buil_families = buil_elem[columns[8]]
                if buil_elem[columns[15]]:
                    return int(en_dem_per_hh["heating"] * buil_families)
                else:
                    return 0

            heat_energy_mask = df[columns[19]].isna()

            df.loc[heat_energy_mask, columns[19]] = df[heat_energy_mask].apply(calculate_heating_energy_demand, axis=1)

            def calculate_total_energy_demand(build_elem):
                energy_demand = int(build_elem[columns[17]] + build_elem[columns[18]] + build_elem[columns[19]])
                return energy_demand

            tot_energy_mask = df[columns[16]].isna()

            df.loc[tot_energy_mask, columns[16]] = df[tot_energy_mask].apply(calculate_total_energy_demand, axis=1)

            for idx, building_elem in enumerate(df[columns[3]]):
                if building_elem not in filtering_values["not_specified"]:
                    if building_elem in filtering_values["AB"]:
                        df[columns[7]].iloc[idx] = "AB"  # Apartment Block
                    elif building_elem in filtering_values["SFH"]:
                        df[columns[7]].iloc[idx] = "SFH"  # Single Family House
                    elif building_elem in filtering_values["MFH"]:
                        df[columns[7]].iloc[idx] = "MFH"   # Multi Family House
                    elif building_elem in filtering_values["TH"]:
                        df[columns[7]].iloc[idx] = "TH"  # Terraced House
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




