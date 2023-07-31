"""This script creates a sample weather data collection if not previously provided"""

import pandas as pd
import random
import json

with open("config/weather_config.json", "r") as f:
    weather_data = json.load(f)
mean_dict = weather_data["distribution_parameters"]["expected_value"]
std_dev = weather_data["distribution_parameters"]["std_deviation"]

columns = ['temperature']
days_in_a_year = 365
df = pd.DataFrame(index=range(days_in_a_year), columns=columns)

j = 1

for d in range(days_in_a_year):
    if j <= 31:  # jan
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["january"], std_dev), 1)
    elif 31 < j <= 59:  # feb
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["february"], std_dev), 1)
    elif 59 < j <= 90:  # mar
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["march"], std_dev), 1)
    elif 90 < j <= 120:  # apr
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["april"], std_dev), 1)
    elif 120 < j <= 151:  # may
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["may"], std_dev), 1)
    elif 151 < j <= 181:  # june
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["june"], std_dev), 1)
    elif 181 < j <= 212:  # july
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["july"], std_dev), 1)
    elif 212 < j <= 243:  # august
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["august"], std_dev), 1)
    elif 243 < j <= 273:  # september
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["september"], std_dev), 1)
    elif 273 < j <= 304:  # october
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["october"], std_dev), 1)
    elif 304 < j <= 334:  # november
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["november"], std_dev), 1)
    elif 334 < j <= 365:  # december
        df['temperature'].iloc[d] = round(random.gauss(mean_dict["december"], std_dev), 1)

    j += 1

df.to_csv("weather_data/temperature_data.csv", index=False)






