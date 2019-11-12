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


def getFloodImg(x, y, imageSize=100, depth=200):
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


def getRisks(x, y):
    result = {
        "high_limit": 400,
        "medium_limit": 300,
        "low_limit": 200,
        "ground_height": getGroundHeight(x, y),
        "risk": "low",
    }
    if result["low_limit"] / 100 >= result["ground_height"]:
        flood = computeFloodPecentage(getFloodImg(x, y, depth=result["low_limit"]))
        result["risk"] = "high" if flood > 0.1 else result["risk"]
    elif result["medium_limit"] / 100 >= result["ground_height"]:
        flood = computeFloodPecentage(getFloodImg(x, y, depth=result["medium_limit"]))
        result["risk"] = "medium" if flood > 0.1 else result["risk"]
    return result
