import pandapower as pp
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

network = pp.from_pickle("utility/utility_network_data/network_PV.p")

network = {dataframe_name: dataframe for dataframe_name, dataframe in network.items() if not isinstance(dataframe, pd.DataFrame) or not dataframe.empty}

