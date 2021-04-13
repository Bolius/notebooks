import unittest
import requests
from code.lib import bounding_box
import os


# Test class for checking the service providers we use for the calculator
# Test parameters are chosen based on values that are know to work,
# and has no importance here.
# These test are only to check if the providers are up, and that our credentials
# are accepted.
class TestServices(unittest.TestCase):
    def test_datafordeleren(self):
        user, password = os.environ["DATAFORDELEREN"].split("@")
        params = {
            "username": user,
            "password": password,
            "request": "GetMap",
            "CRS": "EPSG:3857",
            "SRS": "EPSG:3857",
            "styles": "default",
            "VERSION": "1.1.1",
            "FORMAT": "image/png",
            "LAYERS": "orto_foraar",
            "BBOX": bounding_box((55.67946496, 12.56466489), ESPG="3857"),
            "WIDTH": str(400),
            "HEIGHT": str(400),
        }
        response = requests.request(
            "GET",
            "https://services.datafordeler.dk/GeoDanmarkOrto/orto_foraar/1.0.0/WMS?",
            params=params,
        )
        message = "Datafordeleren returnede status kode " + str(response.status_code)
        self.assertTrue(
            (response.status_code >= 200) and (response.status_code <= 299), msg=message
        )

    def test_dawa(self):
        response = requests.request(
            "GET",
            "https://dawa.aws.dk/adresser",
            params={
                "q": "Jarmers Pl. 2, 1551 København",
                "struktur": "mini",
                "fuzzy": "",
            },
        )
        message = "Dawa returnede status kode " + str(response.status_code)
        self.assertTrue(
            (response.status_code >= 200) and (response.status_code <= 299), msg=message
        )

    def test_conzoom(self):
        response = requests.request(
            "GET",
            "https://apps.conzoom.eu/api/v1/values/dk/unit/",
            headers={"authorization": f"Basic {os.environ['GEO_KEY']}"},
            params={
                "where": "acadr_bbrid=40eb1f85-9c53-4581-e044-0003ba298018",
                "vars": "bld_area_basement",
            },
        )
        message = "Conzoom returnede status kode " + str(response.status_code)
        self.assertTrue(
            (response.status_code >= 200) and (response.status_code <= 299), msg=message
        )

    def test_dataforsyningen(self):
        params = {
            "request": "GetMap",
            "service": "WMS",
            "token": os.environ["DATAFORSYNINGEN"],
            "TRANSPARENT": "True",
            "VERSION": "1.1.1",
            "REQUEST": "GetMap",
            "FORMAT": "image/png",
            "SRS": "EPSG:3857",
            "BBOX": bounding_box((55.67946496, 12.56466489), ESPG="3857"),
            "WIDTH": str(400),
            "HEIGHT": str(400),
            "LAYERS": "BU.Building",
            "servicename": "building_inspire",
        }
        response = requests.request(
            "GET", "https://api.dataforsyningen.dk/service?", params=params
        )
        message = "Dataforsyningen returnede status kode " + str(response.status_code)
        self.assertTrue(
            (response.status_code >= 200) and (response.status_code <= 299), msg=message
        )
