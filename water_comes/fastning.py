import requests
from io import BytesIO
from PIL import Image
from pyproj import Transformer
from data_retrival import boundingBox, convertEPSG, getImg
import numpy as np
import pandas as pd
import base64
from time import time


def getFastningImg(x, y, imageSize=800):
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


# fastningMapping = pd.DataFrame(
#     {
#         "100": np.array([207, 20, 22, 255]),
#         "80": np.array([212, 42, 35, 255]),
#         "70": np.array([220, 67, 53, 255]),
#         "60": np.array([224, 95, 73, 255]),
#         "50": np.array([232, 121, 94, 255]),
#         "35": np.array([236, 145, 114, 255]),
#         "20": np.array([242, 170, 139, 255]),
#         "10": np.array([246, 193, 163, 255]),
#         "0": np.array([255, 236, 215, 255]),
#     },
#     index=["Red", "Green", "Blue", "Alpha"],
# ).transpose()


fastningMapping_ = np.array(
    [
        [207, 20, 22, 255],
        [212, 42, 35, 255],
        [220, 67, 53, 255],
        [224, 95, 73, 255],
        [232, 121, 94, 255],
        [236, 145, 114, 255],
        [242, 170, 139, 255],
        [246, 193, 163, 255],
        [255, 236, 215, 255],
    ]
)

val_map = {
    "0": 100,
    "1": 80,
    "2": 70,
    "3": 60,
    "4": 50,
    "5": 40,
    "6": 30,
    "7": 20,
    "8": 10,
    "9": 0,
}


def imageToMatrix(img, size=25):
    colMat = np.asarray(img.resize((size, size)))
    values = np.zeros(shape=(colMat.shape[0], colMat.shape[1]))
    for i in range(size):
        for j in range(size):
            values[i][j] = val_map.get(
                str(np.argmin(np.sum(np.abs(fastningMapping_ - colMat[i][j]), axis=1)))
            )

    return values


def mapImg(fatImg, x, y):
    mapImg = getImg(x, y, "map", mode="RGB")
    alpImg = fatImg.copy()
    alpImg.putalpha(170)
    mapImg.paste(alpImg, (0, 0), alpImg)
    return mapImg


def getFastning(x, y, return_base64=True):
    fatImg = getFastningImg(x, y)
    map = mapImg(fatImg, x, y)
    df = imageToMatrix(fatImg)

    buffered = BytesIO()
    map.save(buffered, format="PNG")
    w, _ = df.shape
    step = w // 4

    return {
        "total_area_fastning": np.mean(df),
        "image": base64.b64encode(buffered.getvalue()) if return_base64 else map,
        "house_area_fastning": df[step : w - step]
        .transpose()[step : w - step]
        .mean()
        .mean(),
    }
