import requests
from io import BytesIO
from PIL import Image
from pyproj import Transformer
from data_retrival import boundingBox, convertEPSG, getImg
import numpy as np
import pandas as pd
import base64
from time import time
import os


def getFloodImg(x, y, imageSize=400, depth=200):
    x, y = convertEPSG(x, y)
    bbox = boundingBox(x, y)
    minX, minY, maxX, maxY = [float(coord) for coord in bbox.split(",")]

    transformer = Transformer.from_crs("epsg:3857", "epsg:25832")
    minX, minY = transformer.transform(minX, minY)
    maxX, maxY = transformer.transform(maxX, maxY)
    response = requests.request(
        "GET",
        "http://9.tilecache2-miljoegis.mim.dk/gwc/service/wms",
        params={
            "SERVICENAME": "miljoegis-klimatilpasningsplaner",
            "LAYERS": f"theme-klimatilp-raster-hav{depth}cm",
            "VERSION": "1.1.1",
            "REQUEST": "GetMap",
            "FORMAT": "image/png",
            "TRANSPARENT": "true",
            "WIDTH": str(imageSize),
            "HEIGHT": str(imageSize),
            "SRS": "EPSG:25832",
            "BBOX": f"{minX},{minY},{maxX},{maxY}",
        },
    )
    img = Image.open(BytesIO(response.content))
    return img


def computeFloodPecentage(img):
    return (np.array(img.convert("L").resize((10, 10))) > 10).mean().mean()


def getGroundHeight(x, y):
    user, password = os.environ["KORTFORSYNINGEN"].split("@")
    response = requests.request(
        "GET",
        "https://services.kortforsyningen.dk/",
        params={
            "servicename": "RestGeokeys_v2",
            "elevationmodel": "dtm",
            "method": "hoejde",
            "georef": "EPSG:4326",
            "geop": f"{y},{x}",
            "login": user,
            "password": password,
        },
    )
    return np.round(response.json()["hoejde"], decimals=1)


def isFlooded(x, y, limit):
    percentage = computeFloodPecentage(getFloodImg(x, y, depth=limit))
    return percentage > 0.1

def mapImg(Img, x, y):
    mapImg = getImg(x, y, "map", mode="RGB")
    alpImg = Img.copy()
    alpImg.putalpha(170)
    mapImg.paste(Img, (0, 0), alpImg)
    return mapImg


def getRisks(x, y):

    result = {
        "medium_limit": 190,
        "low_limit": 140,
        "ground_height": getGroundHeight(x, y),
        "risk": "low",
        "image": mapImg(getFloodImg(x, y), x, y),  
    }
    if isFlooded(x, y, result["low_limit"]):
        result["risk"] = "high"

    elif isFlooded(x, y, result["medium_limit"]):
        result["risk"] = "medium"
    return result
