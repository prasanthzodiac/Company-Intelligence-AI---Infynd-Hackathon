import unittest

from backend.api.app import app


class ApiSessionTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_session_protected_routes_return_401_without_header(self):
        routes = [
            ("get", "/api/companies", None),
            ("get", "/api/companies/example.com/profile", None),
            ("get", "/api/companies/example.com/chunks", None),
            ("get", "/api/proofs/example.com", None),
            ("post", "/api/chat", {"domain": "example.com", "question": "hello"}),
        ]

        for method, path, body in routes:
            with self.subTest(path=path):
                request = getattr(self.client, method)
                response = request(path, json=body) if body else request(path)
                self.assertEqual(response.status_code, 401)
                self.assertIn("error", response.get_json())

    def test_create_session_lists_empty_companies_and_deletes(self):
        response = self.client.post("/api/session")
        self.assertEqual(response.status_code, 200)
        session_id = response.get_json()["session_id"]

        try:
            companies = self.client.get(
                "/api/companies",
                headers={"X-Session-Id": session_id},
            )
            self.assertEqual(companies.status_code, 200)
            self.assertEqual(companies.get_json(), [])
        finally:
            deleted = self.client.delete(
                "/api/session",
                headers={"X-Session-Id": session_id},
            )
            self.assertEqual(deleted.status_code, 200)

    def test_invalid_domain_returns_400_inside_valid_session(self):
        response = self.client.post("/api/session")
        self.assertEqual(response.status_code, 200)
        session_id = response.get_json()["session_id"]
        headers = {"X-Session-Id": session_id}

        try:
            profile = self.client.get(
                "/api/companies/not_a_domain/profile",
                headers=headers,
            )
            self.assertEqual(profile.status_code, 400)

            chat = self.client.post(
                "/api/chat",
                headers=headers,
                json={"domain": "../secret", "question": "what is this company?"},
            )
            self.assertEqual(chat.status_code, 400)
        finally:
            self.client.delete("/api/session", headers=headers)


if __name__ == "__main__":
    unittest.main()
