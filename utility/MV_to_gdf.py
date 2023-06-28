import pickle
import pandas as pd

with open('ding0-output/ding0_grids_example.pkl', 'rb') as file:
    data = pickle.load(file)

dfs = {}

for key, value in data.static_data.items():
    df = pd.DataFrame(value)
    df_name = key
    dfs[df_name] = df


