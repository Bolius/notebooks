import os, sys

sys.path.append(os.path.pardir)
from data_retrival import addressToLatLong, convertEPSG, getImg
from image_handling import (
    combineImages,
    imageToBlackWhite,
    isolateBuilding,
    replaceColor,
)
import numpy as np
import base64
from io import BytesIO
from threading import Thread
from time import time


class ThreadValue(Thread):
    def __init__(
        self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None
    ):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


def worker(s, x, y, mode=None):
    """thread worker function"""
    return (
        getImg(x, y, s)
        if not mode
        else getImg(x, y, s, mode="RGB")
    )

    return getImg(x, y, s) if not mode else getImg(x, y, s, mode="RGB")


def addressToImages(address=None, x=None, y=None):
    if address is None and (x is None or y is None):
        raise ValueError("No input specified")

    if x is None or y is None:
        x, y = addressToLatLong(address)
    x, y = convertEPSG(x, y)

    t0 = ThreadValue(target=worker, args=("buildings", x, y))
    t1 = ThreadValue(target=worker, args=("hollowings", x, y))
    t2 = ThreadValue(target=worker, args=("map", x, y, "RGB"))

    t0.start()
    t1.start()
    t2.start()

    return (t0.join(), t1.join(), t2.join())


def numberPixelHollowings(hollowImg, isolateImg):
    combined = combineImages(
        imageToBlackWhite(hollowImg, threshold=10), imageToBlackWhite(isolateImg)
    )
    return np.asarray(imageToBlackWhite(combined)).sum()


def prettyPng(mapImg, isolateImg, hollowImg, combined):
    houseImg = replaceColor(
        imageToBlackWhite(isolateImg).convert("RGBA"),
        (255, 255, 255, 255),
        (247, 114, 30, 128),
    )
    mapImg.paste(houseImg, (0, 0), houseImg)
    hollowImg = replaceColor(
        imageToBlackWhite(hollowImg, threshold=10).convert("RGBA"),
        (255, 255, 255, 255),
        (1, 1, 128, 128),
    )
    combined = replaceColor(
        imageToBlackWhite(combined).convert("RGBA"),
        (255, 255, 255, 255),
        (1, 1, 255, 128),
    )
    mapImg.paste(hollowImg, (0, 0), hollowImg)
    mapImg.paste(combined, (0, 0), combined)
    return mapImg


def checkHollowing(address):
    buildImg, hollowImg, mapImg = addressToImages(address)
    isolateImg = isolateBuilding(buildImg)
    combined = combineImages(
        imageToBlackWhite(hollowImg, threshold=10), imageToBlackWhite(isolateImg)
    )
    numberPixels = numberPixelHollowings(hollowImg, isolateImg)
    img = prettyPng(mapImg, isolateImg, hollowImg, combined)
    return numberPixels, img


def getHollowing(img, width=None):
    x, y = img.shape[:2]
    if width is None:
        width = min(x, y)

    minx = int(x / 2 - width / 2)
    maxx = int(x / 2 + width / 2)
    miny = int(y / 2 - width / 2)
    maxy = int(y / 2 + width / 2)

    return np.sum(img[minx:maxx, miny:maxy]) / ((x - width) * (y - width))


def getHollowingResponse(address=None, x=None, y=None):
    if address is None and (x is None or y is None):
        raise Exception("No address given")

    building, hollow, map = (
        addressToImages(address) if address is not None else addressToImages(x=x, y=y)
    )

    isolateBuild = isolateBuilding(building)

    binBuild = imageToBlackWhite(isolateBuild, retArray=True)
    binHollow = imageToBlackWhite(hollow, 10, True)

    build = np.where(np.array(binBuild) == 0, np.array(binBuild), 255)
    hollow = np.where(np.array(binHollow) == 0, np.array(binHollow), 255)

    combined = combineImages(hollow, build)

    img = prettyPng(map, isolateBuild, hollow, combined)

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    house_percentage = round(
        np.sum(np.bitwise_and(binBuild, binHollow)) / np.sum(binBuild) * 100, 2
    )
    return {
        "house_percentage": house_percentage,
        "risk": "high" if house_percentage > 5 else "low",
        "area_percentage": round(
            getHollowing(binHollow, binHollow.shape[0] / 2) * 100, 2
        ),
        "image": base64.b64encode(buffered.getvalue()),
    }
