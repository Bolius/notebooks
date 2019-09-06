import requests
from io import BytesIO
from PIL import Image
from pyproj import Transformer
from data_retrival import boundingBox, convertEPSG
import numpy as np
import pandas as pd


def getFastningImg(x, y, imageSize=400):
    x, y = convertEPSG(x, y)
    bbox = boundingBox(x, y)
    minX, minY, maxX, maxY = [float(coord) for coord in bbox.split(",")]

    transformer = Transformer.from_crs("epsg:3857", "epsg:25832")
    minX, minY = transformer.transform(minX, minY)
    maxX, maxY = transformer.transform(maxX, maxY)
    response = requests.request(
        "GET",
        "http://7.tilecache2-miljoegis.mim.dk/gwc/service/wms",
        params={
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetMap",
            "FORMAT": "image/png",
            "TRANSPARENT": "true",
            "LAYERS": "theme-klimatilp-raster-arealanvendelse",
            "WIDTH": str(imageSize),
            "HEIGHT": str(imageSize),
            "SRS": "EPSG:25832",
            "BBOX": f"{minX},{minY},{maxX},{maxY}",
        },
    )
    img = Image.open(BytesIO(response.content))
    return img


fastningMapping = pd.DataFrame(
    {
        "100": np.array([207, 20, 22, 255]),
        "80": np.array([212, 42, 35, 255]),
        "70": np.array([220, 67, 53, 255]),
        "60": np.array([224, 95, 73, 255]),
        "50": np.array([232, 121, 94, 255]),
        "35": np.array([236, 145, 114, 255]),
        "20": np.array([242, 170, 139, 255]),
        "10": np.array([246, 193, 163, 255]),
        "0": np.array([255, 236, 215, 255]),
    },
    index=["Red", "Green", "Blue", "Alpha"],
).transpose()


def imageToMatrix(img, size=25):
    colMat = np.array(img.resize((size, size)))
    values = np.zeros(shape=(colMat.shape[0], colMat.shape[1]))
    for i in range(size):
        for j in range(size):
            values[i][j] = int(
                (fastningMapping - colMat[i][j]).abs().sum(axis=1).idxmin()
            )
    return pd.DataFrame(values)
