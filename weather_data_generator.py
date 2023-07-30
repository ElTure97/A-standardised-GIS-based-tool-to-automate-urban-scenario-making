"""This script creates a sample weather data collection if not previously provided"""
import pandas as pd
import random

columns = ['temperature']
days_in_a_year = 365
df = pd.DataFrame(index=range(days_in_a_year), columns=columns)

j = 1

std_dev = 1.5  # standard deviation in degrees

for d in range(days_in_a_year):
    if j <= 31:  # jan
        df['temperature'].iloc[d] = round(random.gauss(3, std_dev), 1)
    elif 31 < j <= 59:  # feb
        df['temperature'].iloc[d] = round(random.gauss(7, std_dev), 1)
    elif 59 < j <= 90:  # mar
        df['temperature'].iloc[d] = round(random.gauss(11, std_dev), 1)
    elif 90 < j <= 120:  # apr
        df['temperature'].iloc[d] = round(random.gauss(16, std_dev), 1)
    elif 120 < j <= 151:  # may
        df['temperature'].iloc[d] = round(random.gauss(21, std_dev), 1)
    elif 151 < j <= 181:  # june
        df['temperature'].iloc[d] = round(random.gauss(26, std_dev), 1)
    elif 181 < j <= 212:  # july
        df['temperature'].iloc[d] = round(random.gauss(31, std_dev), 1)
    elif 212 < j <= 243:  # august
        df['temperature'].iloc[d] = round(random.gauss(25, std_dev), 1)
    elif 243 < j <= 273:  # september
        df['temperature'].iloc[d] = round(random.gauss(20, std_dev), 1)
    elif 273 < j <= 304:  # october
        df['temperature'].iloc[d] = round(random.gauss(15, std_dev), 1)
    elif 304 < j <= 334:  # november
        df['temperature'].iloc[d] = round(random.gauss(10, std_dev), 1)
    elif 334 < j <= 365:  # december
        df['temperature'].iloc[d] = round(random.gauss(5, std_dev), 1)

    j += 1

df.to_csv("weather_data/temperature_data.csv", index=False)






