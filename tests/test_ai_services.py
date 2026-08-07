import unittest
import json
from unittest.mock import patch
from app import create_app

class AIServicesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

    def test_farming_assistant_missing_question(self):
        res = self.client.post("/api/ai/farming-assistant", json={})
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data["success"])

    def test_disease_explanation_missing_fields(self):
        res = self.client.post("/api/ai/disease-explanation", json={"crop": "Tomato"})
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data["success"])

    def test_translate_missing_text(self):
        res = self.client.post("/api/ai/translate", json={})
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data["success"])

    @patch("app.services.gemini_service.GeminiService.generate_content")
    def test_farming_assistant_success(self, mock_generate):
        mock_generate.return_value = "Water chilli plants 2-3 times per week."
        res = self.client.post("/api/ai/farming-assistant", json={
            "question": "How often should I water chilli plants?",
            "language": "English"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertIn("answer", data)
        self.assertEqual(data["answer"], "Water chilli plants 2-3 times per week.")

    @patch("app.services.gemini_service.GeminiService.generate_content")
    def test_disease_explanation_success(self, mock_generate):
        mock_generate.return_value = "📌 Disease Explanation: Early Blight is a fungal infection."
        res = self.client.post("/api/ai/disease-explanation", json={
            "crop": "Tomato",
            "disease": "Early Blight",
            "analysis": "Brown spots detected on leaves",
            "language": "English"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertIn("explanation", data)

    @patch("app.services.gemini_service.GeminiService.generate_content")
    def test_translate_success(self, mock_generate):
        mock_generate.return_value = "உங்கள் பயிரை தவறாமல் நனைக்கவும்"
        res = self.client.post("/api/ai/translate", json={
            "text": "Water your crop regularly",
            "target_language": "Tamil"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertIn("translated_text", data)
        self.assertEqual(data["translated_text"], "உங்கள் பயிரை தவறாமல் நனைக்கவும்")

if __name__ == "__main__":
    unittest.main()
