import numpy as np
from PIL import Image


def greyscale_to_binary_image(img, thresshold=127):
    return img.point(lambda p: 255 if p > np.uint8(thresshold) else 0).convert("1")


def isolate_building(buildImg):
    """Given a greyscale image centered on a shape it returns a binary image of
    only the shape.
    """
    if buildImg.mode != "L":
        buildImg = buildImg.convert("L")
    arr = np.asarray(buildImg).copy()
    x, y = arr.shape
    x, y = x // 2, y // 2
    points = set([(x, y)])
    while len(points) > 0:
        x, y = points.pop()
        arr[x][y] = np.uint8(255)
        _checkNeighbours(arr, x, y, points)
    return greyscale_to_binary_image(Image.fromarray(arr), thresshold=254)


def _checkNeighbours(arr, x, y, points):
    threshold = 50
    x_limit, y_limit = arr.shape
    neighbors = [[x + 1, y], [x - 1, y], [x, y - 1], [x, y + 1]]
    # filter neighbors that are out or range or below threshold
    neighbors = [
        (x, y)
        for x, y in neighbors
        if ((x >= 0 and y >= 0) and (x < x_limit and y < y_limit))
        and arr[x][y] > threshold
        and arr[x][y] < 255
    ]
    for neighbor in neighbors:
        points.add(neighbor)


def combine_images(img1, img2):
    """ Takes two greyscale images and combines them. """
    if (img1.mode, img2.mode) != ("L", "L"):
        raise ValueError("Not a grayscale image")

    img1 = np.asarray(img1).copy()
    img2 = np.asarray(img2).copy()

    img1 = img1 / 2
    img2 = img2 / 2

    combined_img = (img1 + img2).astype(np.uint8)
    return Image.fromarray(combined_img, mode="L")
