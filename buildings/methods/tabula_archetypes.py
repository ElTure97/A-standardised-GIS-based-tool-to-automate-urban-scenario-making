import pandas as pd
import time
import random

class TabulaInfoLoader:

    def __init__(self, gdf, input_file, sheet_name, code_country_column, code_country):
        self.gdf = gdf
        self.input_file = input_file
        self.sheet_name = sheet_name
        self.code_country = code_country
        self.code_country_column = code_country_column
        self.code_country = self.code_country

    def load_file(self, tabula_columns):
        xl_file = pd.ExcelFile(self.input_file)
        df = xl_file.parse(self.sheet_name)
        national_df = df[(df[self.code_country_column] == self.code_country)]
        filtered_df = national_df.loc[:, tabula_columns]
        return filtered_df

    def add_tabula_info(self, gdf_columns, tabula_columns):
        tabula_df = self.load_file(tabula_columns)
        for idx, elem in enumerate(self.gdf[gdf_columns[7]]):
            prov_df = tabula_df[(tabula_df[tabula_columns[1]] == elem)]
            year_elem = self.gdf[gdf_columns[2]].iloc[idx]
            if year_elem != "-1919" and year_elem != "2005-":
                year_range_inf, year_range_sup = map(int, year_elem.split("-"))
            elif year_elem == "-1919":
                year_range_inf = 1800  # default value
                year_range_sup = 1918
            else:
                year_range_inf = 2006
                year_range_sup = int(time.strftime("%Y"))  # current year
            construction_year = random.randint(year_range_inf, year_range_sup)
            self.gdf[gdf_columns[2]].iloc[idx] = int(construction_year)
            for i in prov_df.index:
                if prov_df.loc[i, tabula_columns[2]] <= construction_year <= prov_df.loc[i, tabula_columns[3]]:
                    self.gdf[gdf_columns[11]].iloc[idx] = prov_df.loc[i, tabula_columns[0]]
        return self.gdf, tabula_df

