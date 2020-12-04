import base64
import imagehash
import unittest
from code.lib import (
    address_to_house_data,
    fastning_image_to_value,
    get_fastning_img,
    get_fastning_response,
)
from io import BytesIO
from os import path


from PIL import Image


class TestFastning(unittest.TestCase):
    def test_get_fastning_img(self):
        office_address = address_to_house_data("Jarmers Pl. 2, 1551 København")[
            "coordinates"
        ]
        actual_image = get_fastning_img(coordinates=office_address)
        expected_image = Image.open(
            path.join("tests", "test_images", "get_fastning_office.png")
        ).convert("RGB")

        self.assertEqual(actual_image, expected_image)

    def test_fastning_img_to_value(self):
        office_address = address_to_house_data("Kjærmarken 103, 6771 gredstedbro")[
            "coordinates"
        ]
        fastning_image = get_fastning_img(coordinates=office_address)
        fastning_image_to_value(fastning_image)

        self.assertEqual(fastning_image_to_value(fastning_image), 44.75)

    def test_get_fasting_response_high(self):
        office_address = address_to_house_data("Jarmers Pl. 2, 1551 København")[
            "coordinates"
        ]
        resp = get_fastning_response(office_address)

        self.assertEqual(resp["value"], 51.53)
        self.assertEqual(resp["risk"], "medium")

        actual_image = Image.open(BytesIO(base64.b64decode(resp["image"])))
        expected_image = Image.open(
            path.join("tests", "test_images", "fastning_map_office.png")
        ).convert("RGB")

        expected_hash = imagehash.average_hash(expected_image)
        actual_hash = imagehash.average_hash(actual_image)
        self.assertTrue(expected_hash, actual_hash)

    def test_get_fasting_response_medium(self):
        home_coordinates = address_to_house_data("Kjærmarken 103, 6771 gredstedbro")[
            "coordinates"
        ]
        resp = get_fastning_response(home_coordinates)

        self.assertEqual(resp["risk"], "low")
        self.assertEqual(resp["value"], 44.75)


if __name__ == "__main__":
    unittest.main()
