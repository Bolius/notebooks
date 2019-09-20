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
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

def worker(s, x, y, mode=None):
    """thread worker function"""
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

    return(
        t0.join(),
        t1.join(),
        t2.join()
    )
    # return (
    #     getImg(x, y, "buildings"),
    #     getImg(x, y, "hollowings"),
    #     getImg(x, y, "map", mode="RGB"),
    # )


def numberPixelHollowings(hollowImg, isolateImg):
    combined = combineImages(
        imageToBlackWhite(hollowImg, thresshold=10), imageToBlackWhite(isolateImg)
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
        imageToBlackWhite(hollowImg, thresshold=10).convert("RGBA"),
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
        imageToBlackWhite(hollowImg, thresshold=10), imageToBlackWhite(isolateImg)
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
        raise Exception('No address given')

    building, hollow, map = addressToImages(address) if address is not None else addressToImages(x=x, y=y)
    isolateBuild = isolateBuilding(building)

    binBuild = imageToBlackWhite(isolateBuild, retArray=True)
    binHollow = imageToBlackWhite(hollow, 10, True)

    h = np.where(np.array(binHollow) == 255, np.array(binHollow), 1)
    b = np.where(np.array(binBuild) == 255, np.array(binBuild), 1)
    combined = combineImages(
        h, b
    )

    img = prettyPng(map, isolateBuild, hollow, combined)
    buffered = BytesIO()
    img.save(buffered, format="PNG")

    return {
        "house_percentage": round(
            np.sum(np.bitwise_and(binBuild, binHollow)) / np.sum(binBuild) * 100, 2
        ),
        "area_percentage": round(getHollowing(binHollow, 400) * 100, 2),
        "image": base64.urlsafe_b64encode(buffered.getvalue()),
    }
