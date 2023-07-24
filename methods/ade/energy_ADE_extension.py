class EnergyADE:

    def __init__(self, gdf):
        self.gdf = gdf
        self.headers = list(self.gdf.columns)
        self.energy_ext = []

    def map_ext(self):
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
            "+energy-weatherData": [{
                "energy-weatherElement": "airTemperature",
                "energy-values": "temperatureData"
            }],
            "+energy-energyDemand": [{
                "energy-energyAmount": "electricityData",
                "energy-endUse": "spaceHeating"
            }],
            "+energy-function": [bld_elem[self.headers[2]]],
            "+energy-referencePoint": None
            }

            self.energy_ext.append(energy)

        return self.energy_ext