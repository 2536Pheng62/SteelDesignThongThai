"""
API Integration Tests
Tests Netlify functions/calculate.py handler
"""
import unittest
import json
import sys
import os

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netlify.functions.calculate import handler

class TestCalculateAPI(unittest.TestCase):
    def test_sections_api(self):
        event = {"body": json.dumps({"module": "sections", "inputs": {}})}
        response = handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        data = json.loads(response["body"])
        self.assertIn("h_beams", data)

    def test_beam_api(self):
        payload = {
            "module": "beam",
            "inputs": {
                "section_name": "H200x200x8x12",
                "span": 6.0,
                "method": "LRFD",
                "dead_load": 5.0,
                "live_load": 10.0
            }
        }
        event = {"body": json.dumps(payload)}
        response = handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        data = json.loads(response["body"])
        self.assertIn("calc_steps", data)
        self.assertEqual(data["method"], "LRFD")

    def test_footing_api(self):
        payload = {
            "module": "footing",
            "inputs": {
                "width": 1.5,
                "length": 1.5,
                "thickness": 0.3,
                "allowable_bearing_kPa": 150.0,
                "axial_load_D": 100.0,
                "axial_load_L": 50.0
            }
        }
        event = {"body": json.dumps(payload)}
        response = handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        data = json.loads(response["body"])
        self.assertTrue(data["is_ok"])

    def test_invalid_module(self):
        event = {"body": json.dumps({"module": "non_existent", "inputs": {}})}
        response = handler(event, None)
        self.assertEqual(response["statusCode"], 400)

if __name__ == '__main__':
    unittest.main()
