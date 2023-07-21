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

            energy = {
            "+energy-buildingType": bld_elem[self.headers[6]],
            "+energy-constructionWeight": constr_weight,
            "+energy-volume": [{
                "energy-type": "grossVolume",
                "energy-value":  round((float(bld_elem[self.headers[5]]) * float(bld_elem[self.headers[0]])), 2),
                "uom": "m3"
            }],
            "+energy-floorArea": [{
                "energy-type": "grossFloorArea",
                "energy-value": float(bld_elem[self.headers[5]]),
                "uom": "m2"
            }],
            "+energy-heightAboveGround": [{
                "energy-heightReference": "generalEave",
                "energy-value": float(bld_elem[self.headers[0]]),
                "uom": "m"
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