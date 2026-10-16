# test_app.py  -  Step 9: automatic checks for the web app (the "taste tester")
import unittest

from app import app, DEPARTMENTS

GOOD_INPUT = {
    "Gender": "Male",
    "Department": "CSE",
    "Attendance_Pct": 80,
    "Study_Hours": 4,
    "Previous_Score": 60,
    "Assignments_Completed": 7,
}


class StudentAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    # ----- pages and info routes -----
    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Student Performance Predictor", response.data)

    def test_health_says_model_is_loaded(self):
        data = self.client.get("/health").get_json()
        self.assertTrue(data["model_loaded"])

    def test_metrics_has_both_models(self):
        data = self.client.get("/api/metrics").get_json()
        self.assertIn("Linear Regression", data["results"])
        self.assertIn("Random Forest", data["results"])

    # ----- good predictions -----
    def test_valid_prediction(self):
        response = self.client.post("/predict", json=GOOD_INPUT)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreaterEqual(data["predicted_grade"], 0)
        self.assertLessEqual(data["predicted_grade"], 20)
        self.assertEqual(data["out_of"], 20)
        self.assertIn(data["category"],
                      ["Excellent", "Good", "Average", "Needs Improvement"])
        self.assertTrue(len(data["suggestions"]) >= 1)
        self.assertIn("Linear Regression", data["metrics"])

    def test_every_department_works(self):
        for dept in DEPARTMENTS:
            response = self.client.post("/predict", json={**GOOD_INPUT, "Department": dept})
            self.assertEqual(response.status_code, 200, dept)

    def test_extreme_values_stay_between_0_and_20(self):
        best = {**GOOD_INPUT, "Attendance_Pct": 100, "Study_Hours": 16,
                "Previous_Score": 100, "Assignments_Completed": 10}
        worst = {**GOOD_INPUT, "Attendance_Pct": 0, "Study_Hours": 0,
                 "Previous_Score": 0, "Assignments_Completed": 0}
        for row in (best, worst):
            grade = self.client.post("/predict", json=row).get_json()["predicted_grade"]
            self.assertTrue(0 <= grade <= 20, grade)

    def test_better_student_gets_higher_grade(self):
        weak = {**GOOD_INPUT, "Study_Hours": 1, "Previous_Score": 30, "Assignments_Completed": 2}
        strong = {**GOOD_INPUT, "Study_Hours": 6, "Previous_Score": 85, "Assignments_Completed": 10}
        weak_grade = self.client.post("/predict", json=weak).get_json()["predicted_grade"]
        strong_grade = self.client.post("/predict", json=strong).get_json()["predicted_grade"]
        self.assertGreater(strong_grade, weak_grade)

    # ----- bad input must be refused politely (status 400) -----
    def test_missing_field_is_rejected(self):
        bad = dict(GOOD_INPUT)
        del bad["Study_Hours"]
        response = self.client.post("/predict", json=bad)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Study_Hours", response.get_json()["fields"])

    def test_out_of_range_is_rejected(self):
        for field, value in [("Attendance_Pct", 150), ("Attendance_Pct", -1),
                             ("Study_Hours", 24), ("Previous_Score", 101),
                             ("Assignments_Completed", 11)]:
            response = self.client.post("/predict", json={**GOOD_INPUT, field: value})
            self.assertEqual(response.status_code, 400, f"{field}={value}")

    def test_text_instead_of_number_is_rejected(self):
        response = self.client.post("/predict", json={**GOOD_INPUT, "Study_Hours": "abc"})
        self.assertEqual(response.status_code, 400)

    def test_unknown_department_or_gender_is_rejected(self):
        for field, value in [("Department", "Magic"), ("Gender", "Robot"), ("Gender", "")]:
            response = self.client.post("/predict", json={**GOOD_INPUT, field: value})
            self.assertEqual(response.status_code, 400, f"{field}={value}")

    def test_nan_is_rejected(self):
        raw = ('{"Gender":"Male","Department":"CSE","Attendance_Pct":NaN,'
               '"Study_Hours":4,"Previous_Score":60,"Assignments_Completed":7}')
        response = self.client.post("/predict", data=raw, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_non_json_is_rejected(self):
        response = self.client.post("/predict", data="hello", content_type="text/plain")
        self.assertEqual(response.status_code, 400)

    def test_empty_json_object_is_rejected(self):
        response = self.client.post("/predict", json={})
        self.assertEqual(response.status_code, 400)

    # ----- wrong addresses -----
    def test_unknown_page_gives_404(self):
        self.assertEqual(self.client.get("/does-not-exist").status_code, 404)

    def test_get_on_predict_gives_405(self):
        self.assertEqual(self.client.get("/predict").status_code, 405)


if __name__ == "__main__":
    unittest.main(verbosity=2)