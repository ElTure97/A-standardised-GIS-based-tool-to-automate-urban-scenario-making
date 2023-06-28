import pandas as pd
import chardet

class CSV2DF:

    def __init__(self, csv_file, provincia, comune, fields, crs):
        self.csv_file = csv_file
        self.provincia = provincia
        self.comune = comune
        self.fields = fields
        self.crs = crs

    def load_csv(self, ref_gdf, columns_name):
        with open(self.csv_file, 'rb') as f:
            result = chardet.detect(f.read())
        df = pd.read_csv(self.csv_file, encoding=result['encoding'], delimiter=';')
        filtered_df = df[(df["PROVINCIA"] == self.provincia) & (df["COMUNE"] == self.comune)]
        df_def = filtered_df[self.fields]
        df_def_bbox = df_def[df_def[columns_name[0]].isin(ref_gdf[columns_name[1]])]
        if 'geometry' in df_def.columns:
            df_def_bbox = df_def.to_crs(self.crs)
        return df_def_bbox
