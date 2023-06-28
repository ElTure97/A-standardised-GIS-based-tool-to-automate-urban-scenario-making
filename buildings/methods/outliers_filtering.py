class OutliersFilter:

    def __init__(self, gdf):
        self.gdf = gdf

    def filter_outliers(self, columns, z_score):
        # outliers are dropped according to building gross floor area and height
        miu_height = self.gdf[columns[1]].mean()
        sigma_height = self.gdf[columns[1]].std()

        miu_area = self.gdf[columns[5]].mean()
        sigma_area = self.gdf[columns[5]].std()
        self.gdf = self.gdf.drop(self.gdf[(self.gdf[columns[1]] < (miu_height - (z_score[0] * sigma_height))) | (self.gdf[columns[5]] < (miu_area - (z_score[1] * sigma_area)))].index, axis=0)  # buildings too short and with too small area

        return self.gdf
