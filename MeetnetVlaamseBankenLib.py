import requests
from datetime import datetime, timedelta
import folium
import pytz

# API url
API_URL = "https://api.meetnetvlaamsebanken.be"

class VlaamseMeetbank():
    # Login at Meetnet Vlaamse Banken
    def __init__(self, username, password):
        self.username = username
        self.password = password
        data = {"grant_type": "password", \
                "username": self.username, \
                "password": self.password}
        r = requests.post(API_URL + "/Token", data)
        if r.status_code == 200:
            content = r.json()
            self.access_token = content["access_token"]
            self.expires_in = content["expires_in"]
            self.issued = content[".issued"]
            self.expires = content[".expires"]
        else:
            print('Authentication was not successful!')

    # Ping request to see if the system is up and running
    # Returns true if the content contains the username
    def TestConnection(self):
        headers = {"Authorization": "Bearer " + self.access_token}
        r = requests.get(API_URL + "/V2/ping", headers=headers)
        if r.status_code == 200:
            content = r.json()
            if content["Customer"]['Login'] == self.username:
                connection_ok_b = True
            else:
                connection_ok_b = False
        else:
            # Ping was not successful
            connection_ok_b = False
        return connection_ok_b

    # Get catalog of with description of all data
    # Catalog contains
    # - Locations: ID, Name (dict -> name in nl, fr and en), description (dict -> description in nl, fr and en), position
    # - Parameters: ID, Name (dict -> name in nl, fr and en), unit, Parameter type ID,
    # - Parameter types: ID, Name (dict -> name in nl, fr and en)  (waves, tide and current, wind, meteo, varia)
    # - Available data: ID, Location ID, Parameter, CurrentInterval
    def getCatalog(self):
        headers = {"Authorization": "Bearer " + self.access_token}
        r = requests.get(API_URL + "/V2/catalog", headers = headers)
        if r.status_code == 200:
            catalog = r.json()
        else:
            # Request was not successful, return empty dictionary
            catalog = {}
        return catalog

    # Get current data
    # Dictionary contains:
    # - DataId
    # - Timestamp
    # - Value
    def getCurrentData(self):
        headers = {"Authorization": "Bearer " + self.access_token}
        r = requests.get(API_URL + "/V2/currentData", headers = headers)
        if r.status_code == 200:
            currentdata = r.json()
        else:
            # Request was not successful
            currentdata = {}
        return currentdata

    # Get data
    # From -> from timestamp, example: 2021-03-29T07:47:51.199Z (in GMT -> Greenwich Mean Time)
    # Till -> till timestamp, example: 2021-04-05T07:47:51.199Z (in GMT -> Greenwich Mean Time)
    # IDs -> list of data IDs, example: ["A2BHLF","BVHGH1","KWIGTZ"]
    # Content contains:
    # - StartTime
    # - EndTime
    # - Intervals
    # - Values: list with IDs
    #   - For each data ID:
    #       - StartTime
    #       - EndTime
    #       - MinValue
    #       - MaxValue
    #       - Values: list of dicts -> Timestamp, Value
    def getData(self, From, Till, IDs):
        headers = {"Authorization": "Bearer " + self.access_token}
        data = {"StartTime": From, \
                "EndTime": Till, \
                "IDs": IDs}
        r = requests.post(API_URL + "/V2/getData", headers = headers, data = data)
        if r.status_code == 200:
            content = r.json()
        else:
            content = {}
        return content

    # Get data of the last X hours for data IDs
    # - hours: int
    # - IDs -> list of data IDs, example: ["A2BHLF","BVHGH1","KWIGTZ"]
    def getDataLastXhours(self, hours, IDs):
        tz = pytz.timezone('GMT')
        Now = datetime.now(tz)
        delta = timedelta(hours=hours)
        From = Now - delta
        Now_timestamp = Now.strftime("%Y-%m-%dT%H:%M:%SZ")
        From_timestamp = From.strftime("%Y-%m-%dT%H:%M:%SZ")
        data = self.getData(From_timestamp, Now_timestamp, IDs)
        return data

    # Generate map with all data locations
    # - language (int): 0 = nl, 1 = fr, 2 = en
    # Returns Folium map object
    def generateMap(self, language):
        catalog = self.getCatalog()
        # Start latitude and longitude for the map (In the sea near Oostende)
        latitude_start = 51.291888
        longitude_start = 2.865830
        # Create map with Folium
        m = folium.Map(location=[latitude_start, longitude_start], tiles="OpenStreetMap", zoom_start=10)
        for location in catalog["Locations"]:
            coordinates = location['PositionWKT'][location['PositionWKT'].find("(")+1:location['PositionWKT'].find(")")].split(" ")
            coordinates = [float(i) for i in coordinates]
            coordinates = coordinates[::-1]
            popup_text = "ID: "+ location['ID'] + "\n" "Name: " + location['Name'][language]["Message"]
            folium.Marker(location=coordinates, popup=popup_text).add_to(m)
        return m

    # Get available data at location
    # - LocationID (string): use generated map to determine locationID
    # - - language (int): 0 = nl, 1 = fr, 2 = en
    # Result: dictionary with data at location (parameter ID, parameter description and interval time
    def getAvailableDataAtLocation(self, locationID, language):
        catalog = self.getCatalog()
        AvailableData = {}
        for data in catalog["AvailableData"]:
            if(data['Location'] == locationID):
                for parameter in catalog['Parameters']:
                    if data['Parameter'] == parameter['ID']:
                        AvailableData[data['ID']] = {"ParameterID": data['Parameter'], \
                                                     "ParameterDescription": parameter["Name"][language]["Message"], \
                                                     "CurrentInterval": data["CurrentInterval"]}
        return AvailableData