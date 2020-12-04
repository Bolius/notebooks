import unittest
import imagehash
from code.lib import (
    address_to_house_data,
    bbr_id_to_house_data,
    bounding_box,
    get_basement_response,
    get_satelite_img,
)
from os import path

from PIL import Image


class TestDataRetrieval(unittest.TestCase):
    def test_address_to_id_and_coordinates(self):
        data = address_to_house_data("Jarmers Pl. 2, 1551 København")
        self.assertEqual(data["coordinates"], (55.67946496, 12.56466489))
        self.assertEqual(data["id"], "0a3f507a-9dcc-32b8-e044-0003ba298018")
        self.assertEqual(data["isAppartment"], False)
        self.assertEqual(data["navn"], "Jarmers Plads 2, 1551 København V")

    def test_bbr_id_to_coordinates(self):
        data = bbr_id_to_house_data("40eb1f85-9c53-4581-e044-0003ba298018")
        self.assertEqual(data["coordinates"], (55.40156089, 8.74228813))
        self.assertEqual(data["navn"], "Kjærmarken 103, 6771 Gredstedbro")

    def test_bounding_box_size(self):
        box = bounding_box((0, 0), boxSize=200, ESPG="3857")
        self.assertEqual(box, "-100.0,-100.0,100.0,100.0")

    def test_bounding_box_espg_3857(self):
        data = address_to_house_data("Jarmers Pl. 2, 1551 København")
        box = bounding_box(data["coordinates"], boxSize=200, ESPG="3857")
        self.assertEqual(
            box,
            "1398592.0975429227,7494769.030811637,1398792.0975429227,7494969.030811637",
        )

    def test_has_basement(self):
        no_basement_id = address_to_house_data("Kjærmarken 103, 6771 gredstedbro")["id"]
        basement_id = address_to_house_data("Kiærsvej 2, 6760 Ribe")["id"]
        self.assertEqual(get_basement_response(no_basement_id)["risk"], "low")
        self.assertEqual(get_basement_response(basement_id)["risk"], "high")

    def test_bounding_box_espg_25832(self):
        data = address_to_house_data("Kjærmarken 103, 6771 Gredstedbro")
        box = bounding_box(data["coordinates"], ESPG="25832")
        self.assertEqual(
            box,
            "483622.52053322777,6139451.855766358,483736.7176466355,6139564.964581124",
        )

    def test_get_satelite_img(self):
        data = address_to_house_data("Jarmers Pl. 2, 1551 København")
        actual_image = get_satelite_img(data["coordinates"])
        actual_hash = imagehash.average_hash(actual_image)
        expected_image = Image.open(
            path.join("tests", "test_images", "get_img_map.png")
        ).convert("RGB")
        expected_hash = imagehash.average_hash(expected_image)
        self.assertEqual(actual_hash, expected_hash)


if __name__ == "__main__":
    unittest.main()
