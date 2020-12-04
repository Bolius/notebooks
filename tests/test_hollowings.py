import base64
import unittest
import imagehash
from code.lib import (
    address_to_house_data,
    coordinates_to_holllowing_images,
    generate_image_summary,
    get_hollowing_img,
    get_hollowing_response,
    house_percentage_hollowing,
)
from io import BytesIO
from os import path

import numpy as np
from PIL import Image


class TestHollowings(unittest.TestCase):
    def test_get_img_building(self):
        office_address = address_to_house_data("Jarmers Pl. 2, 1551 København")[
            "coordinates"
        ]
        actual_image = get_hollowing_img(office_address, "buildings")
        expected_image = Image.open(
            path.join("tests", "test_images", "get_img_buildings.png")
        ).convert("L")

        actual_hash = imagehash.average_hash(actual_image)
        expected_hash = imagehash.average_hash(expected_image)
        self.assertEqual(actual_hash, expected_hash)

    def test_get_img_hollowings(self):
        office_address = address_to_house_data("Jarmers Pl. 2, 1551 København")[
            "coordinates"
        ]
        actual_image = get_hollowing_img(office_address, "hollowings")
        expected_image = Image.open(
            path.join("tests", "test_images", "get_img_hollowings.png")
        ).convert("L")
        self.assertEqual(actual_image, expected_image)

    def test_get_img_buildings(self):
        office_address = address_to_house_data("Jarmers Pl. 2, 1551 København")[
            "coordinates"
        ]
        actual_images = coordinates_to_holllowing_images(office_address)
        expected_images = [
            Image.open(
                path.join("tests", "test_images", "get_img_buildings.png")
            ).convert("L"),
            Image.open(
                path.join("tests", "test_images", "get_img_hollowings.png")
            ).convert("L"),
        ]
        actual_hashes = [imagehash.average_hash(img) for img in actual_images]
        expected_hashes = [imagehash.average_hash(img) for img in expected_images]
        self.assertEqual(actual_hashes, expected_hashes)

    def test_house_percentage_hollowing(self):
        imgSize = (100, 100)
        hollowImg = np.zeros(imgSize).astype(np.uint8)
        hollowImg[0:50, 0:50] = np.uint8(127)
        hollowImg = Image.fromarray(hollowImg, mode="L")

        buildImg = np.zeros(imgSize).astype(np.uint8)
        buildImg[25:75, 25:75] = np.uint8(127)
        buildImg = Image.fromarray(buildImg, mode="L")
        percentage = house_percentage_hollowing(hollowImg, buildImg)
        self.assertEqual(percentage, 25.0)

    def test_generate_image_summery(self):
        shape = (100, 100)
        mapImg = np.ndarray((100, 100, 4), dtype=np.uint8)
        mapImg[:][:] = [np.uint8(n) for n in [68, 193, 104, 255]]  # Green background
        mapImg = Image.fromarray(mapImg, mode="RGBA")
        hollowingImg = np.zeros(shape, dtype=np.uint8)
        hollowingImg[0:50, 0:50] = np.uint8(200)
        hollowingImg = Image.fromarray(hollowingImg)
        hollowingImg
        buldingImg = np.zeros(shape, dtype=np.uint8)
        buldingImg[25:75, 25:75] = np.uint8(200)
        buldingImg = Image.fromarray(buldingImg)

        actual_image = generate_image_summary(mapImg, buldingImg, hollowingImg)
        expected_image = Image.open(
            path.join("tests", "test_images", "image_summary.png")
        ).convert("RGBA")
        self.assertEqual(actual_image, expected_image)

    def test_get_hollowing_response(self):
        office_address = address_to_house_data("Jarmers Pl. 2, 1551 København")[
            "coordinates"
        ]
        resp = get_hollowing_response(office_address)
        actual_image = Image.open(BytesIO(base64.b64decode(resp["image"])))
        expected_image = Image.open(
            path.join("tests", "test_images", "jarmars_hollwing_response.png")
        ).convert("RGB")

        actual_hash = imagehash.average_hash(actual_image)
        expected_hash = imagehash.average_hash(expected_image)
        self.assertTrue(actual_hash, expected_hash)
        resp.pop("image")
        self.assertAlmostEqual(resp["house_percentage"], 0.19)
        self.assertAlmostEqual(resp["area_percentage"], 6.83)


if __name__ == "__main__":
    unittest.main()
