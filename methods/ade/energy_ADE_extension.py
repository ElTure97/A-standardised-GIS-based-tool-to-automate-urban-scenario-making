class EnergyADE:

    def __init__(self, gdf):
        self.gdf = gdf
        self.headers = list(self.gdf.columns)
        self.energy_ext = []
        self.energy_dict = {}

    def map_ext(self, city, energy_acquisition_method, energy_interpolation_method):
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
                    "energy-energyAmount": f"totalEnergyConsumptionBuilding{idx + 1}",  # to be built
                    "energy-endUse": "otherOrCombination"
                }
            ],
            # "+energy-function": [bld_elem[self.headers[2]]],
            "+energy-referencePoint": None
            }

            self.energy_ext.append(energy)

            thermal_zone = {
                f"thermalZone{idx + 1}": {
                    "type": "+Energy-ThermalZone",
                    "attributes": {
                        "energy-floorArea": [
                            {
                                "energy-value": bld_elem[self.headers[4]],
                                "energy-uom": "m2"
                            }
                        ],
                        "energy-infiltrationRate": float(bld_elem[self.headers[12]]),
                        "energy-isCooled": bool(bld_elem[self.headers[13]]),
                        "energy-isHeated": bool(bld_elem[self.headers[14]]),
                        "energy-weatherData": [
                            {
                                "energy-weatherElement": "airTemperature",
                                "energy-values": f"temperatureData{city}"  # to be built
                            }
                        ],
                        "energy-energyDemand": [
                            {
                                "energy-energyAmount": f"electricityConsumptionBuilding{idx + 1}",  # to be built
                                "energy-endUse": "electricalAppliances"
                            },
                            {
                                "energy-energyAmount": f"coolingConsumptionBuilding{idx + 1}",  # to be built
                                "energy-endUse": "spaceCooling"
                            },
                            {
                                "energy-energyAmount": f"heatingConsumptionBuilding{idx + 1}",  # to be built
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
                        "energy-usageZoneType": [bld_elem[self.headers[2]]],
                    },
                    "energy-occupiedBy":
                        [
                            f"occupantsBuilding{idx + 1}"  # to be built
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
                        "energy-occupancyRate": int(bld_elem[self.headers[8]])
                    }
                }
            }

            self.energy_dict.update(occupants)

            total_consumption = {
                f"totalEnergyConsumptionBuilding{idx + 1}": {
                    "type": "+Energy-RegularTimeSeries",
                    "attributes": {
                        "energy-acquisitionMethod": energy_acquisition_method,
                        "energy-interpolationType": energy_interpolation_method,
                        "energy-temporalExtent": {
                            "energy-startPeriod": 0,
                            "energy-endPeriod": 0,
                        }
                    }
                }
            }



        return self.energy_ext, self.energy_dict