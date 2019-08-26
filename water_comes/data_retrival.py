from pyproj import Proj, transform
from PIL import Image
from io import BytesIO
import pandas as pd
import os
import requests
import json


def addressToLatLong(address):
    response = requests.request(
        "GET",
        "https://dawa.aws.dk/adgangsadresser",
        params={"q": address, "struktur": "mini"},
    )
    data = json.loads(response.content)[0]
    return data["x"], data["y"]


def convertEPSG(x, y):
    return transform(Proj(init="epsg:4326"), Proj(init="epsg:3857"), x, y)


def boundingBox(x, y, boxSize=200):
    minx = x - boxSize / 2
    miny = y - boxSize / 2
    maxx = x + boxSize / 2
    maxy = y + boxSize / 2
    return f"{minx},{miny},{maxx},{maxy}"


def getImg(x, y, feature, mode="L", imageSize=800):
    params = {
        "service": "WMS",
        "login": "rotendahl",
        "password": os.environ["KORTFORSYNINGEN_KEY"],
        "TRANSPARENT": "True",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "FORMAT": "image/png",
        "SRS": "EPSG:3857",
        "BBOX": boundingBox(x, y),
        "WIDTH": str(imageSize),
        "HEIGHT": str(imageSize),
    }
    if feature == "buildings":
        params["LAYERS"] = "BU.Building"
        params["servicename"] = "building_inspire"

    elif feature == "hollowings":
        params["servicename"] = ("dhm",)
        params["LAYERS"] = "dhm_bluespot_ekstremregn"
        params["STYLES"] = "bluespot_ekstremregn_0_015"

    elif feature == "map":
        params["servicename"] = ("orto_foraar",)
        params["LAYERS"] = "orto_foraar"

    response = requests.request("GET", "https://kortforsyningen.kms.dk/", params=params)
    img = Image.open(BytesIO(response.content))
    return img.convert(mode)