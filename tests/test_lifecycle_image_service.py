import unittest
import json
from app import create_app
from app.extensions import db
from app.models.crop_lifecycle_image import CropLifecycleImage
from app.services.gemini_image_service import GeminiImageService

class CropLifecycleImageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_lifecycle_image_endpoint_missing_params(self):
        res = self.client.post("/api/crops/lifecycle-image", json={})
        self.assertEqual(res.status_code, 400)

    def test_lifecycle_image_generation_and_caching(self):
        with self.app.app_context():
            # 1. First request for Green Chilli Flowering stage (generates & caches in DB)
            res1 = self.client.post("/api/crops/lifecycle-image", json={
                "crop_name": "Green Chilli",
                "stage": "Flowering",
                "crop_age": 45
            })
            self.assertEqual(res1.status_code, 200)
            data1 = json.loads(res1.data)
            self.assertTrue(data1["success"])
            self.assertIn("image_url", data1["data"])

            # Verify DB record was saved
            db_record = CropLifecycleImage.query.filter_by(crop_name="Green Chilli", stage="flowering").first()
            self.assertIsNotNone(db_record)

            # 2. Second request retrieves cached image from DB
            res2 = self.client.post("/api/crops/lifecycle-image", json={
                "crop_name": "Green Chilli",
                "stage": "Flowering",
                "crop_age": 45
            })
            self.assertEqual(res2.status_code, 200)
            data2 = json.loads(res2.data)
            self.assertEqual(data1["data"]["image_url"], data2["data"]["image_url"])

    def test_distinct_crop_visuals(self):
        # Verify Green Chilli, Brinjal, Okra, Tomato return their own distinct visual imagery
        img_chilli = GeminiImageService.get_crop_specific_visual("Green Chilli", "Flowering")
        img_brinjal = GeminiImageService.get_crop_specific_visual("Brinjal", "Flowering")
        img_okra = GeminiImageService.get_crop_specific_visual("Okra", "Flowering")
        img_tomato = GeminiImageService.get_crop_specific_visual("Tomato", "Flowering")

        self.assertNotEqual(img_chilli, img_brinjal)
        self.assertNotEqual(img_chilli, img_tomato)
        self.assertNotEqual(img_brinjal, img_okra)

if __name__ == "__main__":
    unittest.main()
