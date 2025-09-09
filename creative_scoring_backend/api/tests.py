from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth.models import User

class HealthTests(APITestCase):
    def test_health(self):
        url = reverse('Health')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"message": "Server is up!"})


class ApiFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass1234")
        self.client = APIClient()
        self.client.login(username="tester", password="pass1234")

    def test_upload_score_recommend_export_flow(self):
        # Upload creative
        upload_url = reverse('upload')
        payload = {
            "title": "My Video Ad",
            "description": "A test video",
            "creative_type": "mp4",
            "metadata": {"length": 15}
        }
        resp = self.client.post(upload_url, data=payload, format='json')
        self.assertEqual(resp.status_code, 201)
        creative_id = resp.data["id"]

        # Create audience
        audience_url = reverse('audience')
        aresp = self.client.post(audience_url, data={"name": "Adults 25-54", "size": 12000, "traits": {"interest": "tech"}}, format='json')
        self.assertEqual(aresp.status_code, 200)
        audience_id = aresp.data["id"]

        # Score
        score_url = reverse('score')
        sresp = self.client.post(score_url, data={"creative_id": creative_id, "audience_id": audience_id}, format='json')
        self.assertEqual(sresp.status_code, 200)
        self.assertIn("composite", sresp.data)

        # Recommendations
        rec_url = reverse('recommendations')
        rresp = self.client.get(rec_url, {"creative_id": creative_id, "audience_id": audience_id})
        self.assertEqual(rresp.status_code, 200)
        self.assertGreaterEqual(len(rresp.data), 1)

        # Export CSV
        export_url = reverse('export')
        ex_resp = self.client.get(export_url, {"creative_id": creative_id, "audience_id": audience_id, "format": "csv"})
        self.assertEqual(ex_resp.status_code, 200)
        self.assertEqual(ex_resp["Content-Type"], "text/csv")
