from geopy.geocoders import Nominatim

''' Bounding box generator based on specified address and distance. '''
class BboxGenerator:
    def __init__(self, address, distance, app_name):
        self.address = address
        self.distance = distance
        self.app_name = app_name
    def generate_bbox(self):
        geolocator = Nominatim(user_agent=self.app_name)
        location = geolocator.geocode(self.address)
        lon = location.longitude
        lat = location.latitude
        delta = self.distance/(1000*111.32) # the distance is expressed in m and must be corrected
        bounding_box = (lon-delta, lat-delta, lon+delta, lat+delta)
        return bounding_box