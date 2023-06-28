import numpy as np
import pandas as pd
import statistics
from scipy import stats

class DataFiller:
    def __init__(self, gdfs, sez_det_data):
        self.gdfs = gdfs
        self.sez_det_data = sez_det_data
        self.building_age_headers_list = []
        self.building_age_range_list = []
        self.building_floor_no_headers_list = []
        self.building_floor_no_list = []

    def fill_age(self, columns, sez_id, age_columns):

        for key in age_columns:
            self.building_age_headers_list.append(key)
            values = age_columns[key]
            self.building_age_range_list.append(values)

        for i, df in self.gdfs.items():
            row = self.sez_det_data.loc[self.sez_det_data[sez_id[0]] == i]

            for idx, age_elem in enumerate(df[columns[2]]):
                if isinstance(age_elem, (float, np.floating)) and np.isnan(age_elem):
                    age_probs = []
                    for j in range(len(self.building_age_headers_list)):
                        age_probs.append(row[self.building_age_headers_list[j]])
                    age_probs = [item for sublist in age_probs for item in sublist]
                    if sum(age_probs) == 0:
                        age_probs = [1 / len(self.building_age_range_list)] * len(self.building_age_range_list)
                    else:
                        age_probs = [prob / sum(age_probs) for prob in age_probs]
                    age = np.random.choice(self.building_age_range_list, p=age_probs)
                    df[columns[2]].iloc[idx] = age
                else:
                    pass
        return self.gdfs

    def fill_missing_height(self, columns, sez_id, floor_columns, floor_height):
        self.building_floor_no_headers_list.clear()
        self.building_floor_no_list.clear()

        for key in floor_columns:
            self.building_floor_no_headers_list.append(key)
            values = floor_columns[key]
            self.building_floor_no_list.append(values)

        for i, df in self.gdfs.items():
            row = self.sez_det_data.loc[self.sez_det_data[sez_id[0]] == i]

            for idx, h_elem in enumerate(df[columns[1]]):
                if isinstance(h_elem, (float, np.floating)) and np.isnan(h_elem):
                    floors = df[columns[4]].iloc[idx]
                    no_of_floors = float(floors)
                    if isinstance(no_of_floors, (float, np.floating)) and not np.isnan(no_of_floors):
                        height = round(((no_of_floors * floor_height) + floor_height), 1)
                    else:
                        nn_height = []
                        for height_elem in df[columns[1]]:
                            if isinstance(height_elem, (float, np.floating)) and not np.isnan(height_elem):
                                nn_height.append(height_elem)
                        if len(nn_height) >= ((2/3)*len(df)):
                            height = round((statistics.mean(nn_height)), 1)
                        else:
                            floor_probs = []
                            for j in range(len(self.building_floor_no_headers_list)):
                                floor_probs.append(row[self.building_floor_no_headers_list[j]])
                            floor_probs = [item for sublist in floor_probs for item in sublist]
                            if sum(floor_probs) == 0:
                                floor_probs = [1 / len(self.building_floor_no_list)] * len(self.building_floor_no_list)
                            else:
                                floor_probs = [prob / sum(floor_probs) for prob in floor_probs]
                            height = round((((np.random.choice(self.building_floor_no_list, p=floor_probs)) * (floor_height)) + floor_height), 1)
                    df[columns[1]].iloc[idx] = height
                else:
                    pass
        return self.gdfs

    def fill_no_of_floors(self, columns, sez_id, floor_columns, floor_height):
        self.building_floor_no_headers_list.clear()
        self.building_floor_no_list.clear()

        for key in floor_columns:
            self.building_floor_no_headers_list.append(key)
            values = floor_columns[key]
            self.building_floor_no_list.append(values)

        for i, df in self.gdfs.items():
            row = self.sez_det_data.loc[self.sez_det_data[sez_id[0]] == i]

            for idx, floor_elem in enumerate(df[columns[4]]):
                if isinstance(floor_elem, (float, np.floating)) and np.isnan(floor_elem):
                    height = df[columns[1]].iloc[idx]
                    if isinstance(height, (float, np.floating)) and not np.isnan(height):
                        no_of_floors = int(round((height - floor_height)/floor_height))
                    else:
                        floor_probs = []
                        for j in range(len(self.building_floor_no_headers_list)):
                            floor_probs.append(row[self.building_floor_no_headers_list[j]])
                        floor_probs = [item for sublist in floor_probs for item in sublist]
                        if sum(floor_probs) == 0:
                            floor_probs = [1 / len(self.building_floor_no_list)] * len(self.building_floor_no_list)
                        else:
                            floor_probs = [prob / sum(floor_probs) for prob in floor_probs]
                        no_of_floors = int(np.random.choice(self.building_floor_no_list, p=floor_probs))
                elif isinstance(floor_elem, str):
                    no_of_floors = int(floor_elem)
                else:
                    pass
                df[columns[4]].iloc[idx] = no_of_floors
        return self.gdfs
    def fill_use_destination(self, columns):
        for i, df in self.gdfs.items():
            df[columns[3]] = df[columns[3]].fillna("yes")
        return self.gdfs

    def fill_sez_cens(self, columns):
        for i, df in self.gdfs.items():
            df[columns[10]] = int(i)
        return self.gdfs

    def check_consistency(self, columns, floor_height):
        for i, df in self.gdfs.items():
            for idx, no_of_floors in enumerate(df[columns[4]]):
                height = df[columns[1]].iloc[idx]
                if (height / (float(no_of_floors) + 1)) < floor_height:
                    df[columns[1]].iloc[idx] = round((floor_height * (float(no_of_floors) + 1)), 1)
        return self.gdfs


    def fill_missing_data(self, columns, sez_id, age_columns, floor_columns, floor_height):
        self.gdfs = self.fill_age(columns, sez_id, age_columns)
        self.gdfs = self.fill_missing_height(columns, sez_id, floor_columns, floor_height)
        self.gdfs = self.fill_use_destination(columns)
        self.gdfs = self.fill_sez_cens(columns)
        self.gdfs = self.fill_no_of_floors(columns, sez_id, floor_columns, floor_height)
        gdfs = self.check_consistency(columns, floor_height)

        return gdfs