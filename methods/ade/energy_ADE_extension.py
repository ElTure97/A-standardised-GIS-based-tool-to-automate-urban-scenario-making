import csv
from datetime import datetime
from geopy.geocoders import Nominatim
from meteostat import Point, Daily

class EnergyADE:

    def __init__(self, gdf):
        self.gdf = gdf
        self.headers = list(self.gdf.columns)
        self.energy_ext = []
        self.energy_dict = {}

    # Mapping energy data according to the Energy extension schema
    def map_ext(self, city, city_address, energy_acquisition_method, energy_interpolation_method, energy_measurement_period, weather_config_data):
        for idx, bld_elem in self.gdf.iterrows():

            no_of_floors = int(bld_elem[self.headers[3]])
            if no_of_floors <= 1:
                constr_weight = "veryLight"
            elif 1 < no_of_floors <= 2:
                constr_weight = "light"
            elif 2 < no_of_floors <= 5:
                constr_weight = "medium"
            else:
                constr_weight = "heavy"

            bld_type = bld_elem[self.headers[6]]
            if bld_type == "AB":
                bld_type_str = "apartmentBlock"
            elif bld_type == "SFH":
                bld_type_str = "singleFamilyHouse"
            elif bld_type == "MFH":
                bld_type_str = "multiFamilyHouse"
            elif bld_type_str == "TH":
                bld_type_str = "terracedHouse"
            else:
                bld_type_str = bld_type

            energy = {
            "+energy-buildingType": bld_type_str,
            "+energy-constructionWeight": constr_weight,
            "+energy-volume": [{
                "energy-type": "grossVolume",
                "energy-value":  round((float(bld_elem[self.headers[5]]) * float(bld_elem[self.headers[0]])), 2),
                "energy-uom": "m3"
            }],
            "+energy-floorArea": [{
                "energy-type": "grossFloorArea",
                "energy-value": float(bld_elem[self.headers[5]]),
                "energy-uom": "m2"
            }],
            "+energy-heightAboveGround": [{
                "energy-heightReference": "generalEave",
                "energy-value": float(bld_elem[self.headers[0]]),
                "energy-uom": "m"
            }],
            "+energy-energyDemand": [
                {
                    "energy-energyAmount": f"totalEnergyConsumptionBuilding{idx + 1}",
                    "energy-endUse": "otherOrCombination"
                }
            ],
            # "+energy-function": [bld_elem[self.headers[2]]],
            "+energy-referencePoint": None
            }

            self.energy_ext.append(energy)

            measured_element = weather_config_data["weather_object_config"]["measured_element"]
            weather_element = weather_config_data["weather_object_config"]["weather_element"]

            thermal_zone = {
                f"thermalZone{idx + 1}": {
                    "type": "+Energy-ThermalZone",
                    "attributes": {
                        "energy-infiltrationRate": float(bld_elem[self.headers[12]]),
                        "energy-isCooled": bool(bld_elem[self.headers[13]]),
                        "energy-isHeated": bool(bld_elem[self.headers[14]]),
                        "energy-weatherData": [
                            {
                                "energy-weatherElement": weather_element,
                                "energy-values": f"{measured_element}Data{city}"
                            }
                        ],
                        "energy-energyDemand": [
                            {
                                "energy-energyAmount": f"electricityConsumptionBuilding{idx + 1}",
                                "energy-endUse": "electricalAppliances"
                            },
                            {
                                "energy-energyAmount": f"coolingConsumptionBuilding{idx + 1}",
                                "energy-endUse": "spaceCooling"
                            },
                            {
                                "energy-energyAmount": f"heatingConsumptionBuilding{idx + 1}",
                                "energy-endUse": "spaceHeating"
                            }
                        ]
                    },
                    "parents": [f"building{idx + 1}"],
                    "children": [f"usageZone{idx + 1}"]
                }
            }

            self.energy_dict.update(thermal_zone)

            usage_zone = {
                f"usageZone{idx + 1}": {
                    "type": "+Energy-UsageZone",
                    "attributes": {
                        "energy-usageZoneType": bld_elem[self.headers[2]],
                    },
                    "energy-occupiedBy":
                        [
                            f"occupantsBuilding{idx + 1}"
                        ],
                    "parents":
                        [
                            f"thermalZone{idx + 1}", f"building{idx + 1}"
                        ]
                }
            }

            self.energy_dict.update(usage_zone)

            occupants = {
                f"occupantsBuilding{idx + 1}": {
                    "type": "+Energy-Occupants",
                    "attributes": {
                        "energy-numberOfOccupants": int(bld_elem[self.headers[8]])
                    }
                }
            }

            self.energy_dict.update(occupants)

            delta_interval = datetime.strptime(energy_measurement_period["end_date"], "%Y-%m-%d") - datetime.strptime(energy_measurement_period["start_date"], "%Y-%m-%d")
            time_interval = ((delta_interval.days + delta_interval.seconds / (60 * 60 * 24))/365)
            no_of_years = round(time_interval, 1)
            no_of_months = round((time_interval * 12), 1)
            no_of_weeks = round((time_interval * 52), 1)
            no_of_days = round((time_interval * 365), 1)

            if time_interval >= 1:
                time_uom = "years"
                time_interval = no_of_years
            elif 1/12 <= time_interval < 1:
                time_uom = "months"
                time_interval = no_of_months
            elif 1/52 <= time_interval < 1/12:
                time_uom = "weeks"
                time_interval = no_of_weeks
            else:
                time_uom = "days"
                time_interval = no_of_days

            total_consumption = {
                f"totalEnergyConsumptionBuilding{idx + 1}": {
                    "type": "+Energy-RegularTimeSeries",
                    "attributes": {
                        "energy-acquisitionMethod": energy_acquisition_method,
                        "energy-interpolationType": energy_interpolation_method,
                        "energy-temporalExtent": {
                            "energy-startPeriod": energy_measurement_period["start_date"],
                            "energy-endPeriod": energy_measurement_period["end_date"],
                        },
                        "energy-timeInterval": {
                            "energy-value": time_interval,
                            "energy-uom": time_uom
                        },
                        "energy-values": [bld_elem[self.headers[15]]],
                        "energy-uom": "kWh"
                    }
                }
            }

            self.energy_dict.update(total_consumption)


            electrical_consumption = {
                f"electricityConsumptionBuilding{idx + 1}": {
                    "type": "+Energy-RegularTimeSeries",
                    "attributes": {
                        "energy-acquisitionMethod": energy_acquisition_method,
                        "energy-interpolationType": energy_interpolation_method,
                        "energy-temporalExtent": {
                            "energy-startPeriod": energy_measurement_period["start_date"],
                            "energy-endPeriod": energy_measurement_period["end_date"],
                        },
                        "energy-timeInterval": {
                            "energy-value": time_interval,
                            "energy-uom": time_uom
                        },
                        "energy-values": [bld_elem[self.headers[16]]],
                        "energy-uom": "kWh"
                    }
                }
            }

            if bld_elem[self.headers[7]] > 0:
                self.energy_dict.update(electrical_consumption)
            else:
                self.energy_dict[f"thermalZone{idx + 1}"]["attributes"]["energy-energyDemand"].remove({
                                "energy-energyAmount": f"electricityConsumptionBuilding{idx + 1}",
                                "energy-endUse": "electricalAppliances"
                            })

            cooling_consumption = {
                f"coolingConsumptionBuilding{idx + 1}": {
                    "type": "+Energy-RegularTimeSeries",
                    "attributes": {
                        "energy-acquisitionMethod": energy_acquisition_method,
                        "energy-interpolationType": energy_interpolation_method,
                        "energy-temporalExtent": {
                            "energy-startPeriod": energy_measurement_period["start_date"],
                            "energy-endPeriod": energy_measurement_period["end_date"],
                        },
                        "energy-timeInterval": {
                            "energy-value": time_interval,
                            "energy-uom": time_uom
                        },
                        "energy-values": [bld_elem[self.headers[17]]],
                        "energy-uom": "kWh"
                    }
                }
            }

            if bld_elem[self.headers[13]]:
                self.energy_dict.update(cooling_consumption)
            else:
                self.energy_dict[f"thermalZone{idx + 1}"]["attributes"]["energy-energyDemand"].remove({
                                "energy-energyAmount": f"coolingConsumptionBuilding{idx + 1}",
                                "energy-endUse": "spaceCooling"
                            })

            heating_consumption = {
                f"heatingConsumptionBuilding{idx + 1}": {
                    "type": "+Energy-RegularTimeSeries",
                    "attributes": {
                        "energy-acquisitionMethod": energy_acquisition_method,
                        "energy-interpolationType": energy_interpolation_method,
                        "energy-temporalExtent": {
                            "energy-startPeriod": energy_measurement_period["start_date"],
                            "energy-endPeriod": energy_measurement_period["end_date"],
                        },
                        "energy-timeInterval": {
                            "energy-value": time_interval,
                            "energy-uom": time_uom
                        },
                        "energy-values": [bld_elem[self.headers[18]]],
                        "energy-uom": "kWh"
                    }
                }
            }

            if bld_elem[self.headers[14]]:
                self.energy_dict.update(heating_consumption)
            else:
                self.energy_dict[f"thermalZone{idx + 1}"]["attributes"]["energy-energyDemand"].remove({
                                "energy-energyAmount": f"heatingConsumptionBuilding{idx + 1}",
                                "energy-endUse": "spaceHeating"
                            })

        weather_file_path = weather_config_data["weather_file_path"]
        weather_uom = weather_config_data["uom"]

        # values_list = []
        # with open(weather_file_path, 'r') as file_csv:
        #     csv_reader = csv.reader(file_csv)
        #     for row in csv_reader:
        #         value = round(float(row[0]), 1)
        #         values_list.append(value)

        weather_acq_method = weather_config_data["weather_object_config"]["energy_acquisition_method"]
        weather_interpol_method = weather_config_data["weather_object_config"]["energy_interpolation_method"]
        weather_start_date = weather_config_data["weather_object_config"]["energy_measurement_period"]["start_date"]
        weather_end_date = weather_config_data["weather_object_config"]["energy_measurement_period"]["end_date"]

        start_date = datetime.strptime(weather_start_date, "%Y-%m-%d")
        end_date = datetime.strptime(weather_end_date, "%Y-%m-%d")

        geolocator = Nominatim(user_agent="myGeocoder")

        address = geolocator.geocode(city_address)

        location = Point(address.latitude, address.longitude)

        wea_data = Daily(location, start_date, end_date)
        wea_data = wea_data.fetch()

        values_list = wea_data[wea_data.columns[0]].tolist()

        wea_delta_interval = end_date - start_date
        wea_time_interval = ((wea_delta_interval.days + wea_delta_interval.seconds / (60 * 60 * 24)) / 365) / len(values_list)
        wea_no_of_years = round(wea_time_interval, 1)
        wea_no_of_months = round((wea_time_interval * 12), 1)
        wea_no_of_weeks = round((wea_time_interval * 52), 1)
        wea_no_of_days = round((wea_time_interval * 365), 1)

        if wea_time_interval >= 1:
            wea_uom = "years"
            wea_time_interval = wea_no_of_years
        elif 1 / 12 <= wea_time_interval < 1:
            wea_uom = "months"
            wea_time_interval = wea_no_of_months
        elif 1 / 52 <= wea_time_interval < 1 / 12:
            wea_uom = "weeks"
            wea_time_interval = wea_no_of_weeks
        else:
            wea_uom = "days"
            wea_time_interval = wea_no_of_days

        weather = {
            f"{measured_element}Data{city}": {
                "type": "+Energy-RegularTimeSeries",
                "attributes": {
                    "energy-acquisitionMethod": weather_acq_method,
                    "energy-interpolationType": weather_interpol_method,
                    "energy-temporalExtent": {
                        "energy-startPeriod": weather_start_date,
                        "energy-endPeriod": weather_end_date,
                    },
                    "energy-timeInterval": {
                        "energy-value": wea_time_interval,
                        "energy-uom": wea_uom
                    },
                    "energy-values": values_list,
                    "energy-uom": weather_uom
                }
            }
        }

        self.energy_dict.update(weather)

        return self.energy_ext, self.energy_dict