import requests
from io import BytesIO
from PIL import Image
from pyproj import Transformer
from data_retrival import boundingBox, convertEPSG, getImg
import numpy as np
import pandas as pd
import base64


def getConductivityImg(x, y, imageSize=800):
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
            "LAYERS": "theme-klimatilp-raster-hydrauliskledningsevne25",
            "WIDTH": str(imageSize),
            "HEIGHT": str(imageSize),
            "SRS": "EPSG:25832",
            "BBOX": f"{minX},{minY},{maxX},{maxY}",
        },
    )

    img = Image.open(BytesIO(response.content))
    return img


# conductivityMapping = pd.DataFrame(
#     {
#         "50": np.array([1, 44, 120, 255]),
#         "100": np.array([0, 64, 126, 255]),
#         "125": np.array([0, 79, 128, 255]),
#         "150": np.array([0, 100, 133, 255]),
#         "200": np.array([0, 118, 139, 255]),
#         "250": np.array([0, 118, 139, 255]),
#         "275": np.array([0, 150, 141, 255]),
#         "325": np.array([0, 161, 133, 255]),
#         "375": np.array([0, 171, 120, 255]),
#         "425": np.array([0, 181, 103, 255]),
#         "475": np.array([0, 195, 86, 255]),
#         "525": np.array([0, 205, 61, 255]),
#         "600": np.array([0, 215, 45, 255]),
#         "650": np.array([0, 223, 44, 255]),
#         "725": np.array([0, 228, 46, 255]),
#         "800": np.array([55, 233, 48, 255]),
#         "900": np.array([123, 241, 51, 255]),
#         "975": np.array([174, 247, 53, 255]),
#         "1075": np.array([226, 252, 56, 255]),
#         "1175": np.array([253, 246, 57, 255]),
#         "1300": np.array([253, 231, 54, 255]),
#         "1400": np.array([251, 214, 52, 255]),
#         "1550": np.array([251, 200, 50, 255]),
#         "1700": np.array([247, 182, 46, 255]),
#         "1850": np.array([245, 170, 46, 255]),
#         "2050": np.array([243, 158, 45, 255]),
#         "2200": np.array([236, 140, 47, 255]),
#         "2400": np.array([228, 124, 49, 255]),
#         "2650": np.array([224, 113, 52, 255]),
#         "2900": np.array([217, 101, 57, 255]),
#         "3350": np.array([204, 84, 64, 255]),
#     },
#     index=["Red", "Green", "Blue", "Alpha"],
# ).transpose()



conductivityMapping_ = np.array([
                            [1, 44, 120, 255],
                            [0, 64, 126, 255],
                            [0, 79, 128, 255],
                            [0, 100, 133, 255],
                            [0, 118, 139, 255],
                            [0, 150, 141, 255],
                            [0, 161, 133, 255],
                            [0, 171, 120, 255],
                            [0, 181, 103, 255],
                            [0, 195, 86, 255],
                            [0, 205, 61, 255],
                            [0, 215, 45, 255],
                            [0, 223, 44, 255],
                            [0, 228, 46, 255],
                            [55, 233, 48, 255],
                            [123, 241, 51, 255],
                            [174, 247, 53, 255],
                            [226, 252, 56, 255],
                            [253, 246, 57, 255],
                            [253, 231, 54, 255],
                            [251, 214, 52, 255],
                            [251, 200, 50, 255],
                            [247, 182, 46, 255],
                            [245, 170, 46, 255],
                            [243, 158, 45, 255],
                            [236, 140, 47, 255],
                            [228, 124, 49, 255],
                            [224, 113, 52, 255],
                            [217, 101, 57, 255],
                            [204, 84, 64, 255]
                        ])


def imageToMatrix(img, size=25):
    colMat = np.array(img.resize((size, size)))
    values = np.zeros(shape=(colMat.shape[0], colMat.shape[1]))
    for i in range(size):
        for j in range(size):
            values[i][j] = np.argmin(np.sum(np.abs(conductivityMapping_ - colMat[i][j]), axis=1))
            # values[i][j] = int(
            #     (conductivityMapping - colMat[i][j]).abs().sum(axis=1).idxmin()
            # )
    return values


def mapImg(condImg, x, y):
    mapImg = getImg(x, y, "map", mode="RGB")
    alpImg = condImg.copy()
    alpImg.putalpha(170)
    mapImg.paste(alpImg, (0, 0), alpImg)
    return mapImg


def getConductivity(x, y, return_base64=True):
    condImg = getConductivityImg(x, y)
    map = mapImg(condImg, x, y)
    df = imageToMatrix(condImg)
    buffered = BytesIO()
    map.save(buffered, format="PNG")
    w, _ = df.shape
    step = w // 4

    return {
        "total_area_conductivity": np.mean(df),
        "house_area_conductivity": df[step : w - step]
        .transpose()[step : w - step]
        .mean()
        .mean(),
        "image": base64.urlsafe_b64encode(buffered.getvalue())
        if return_base64
        else map,
    }
