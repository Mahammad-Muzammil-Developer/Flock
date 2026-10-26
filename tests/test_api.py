import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class PortalStub:
    def close(self):
        pass

    def login(self, email, password):
        return True

    def get_meters(self):
        return [{"meter_id": "M-1"}]

    def get_meter(self, meter_id):
        return {"meter_id": meter_id}

    def get_consumption(self, meter_id):
        return [{"reading": "12.5"}]

    def get_hierarchy(self):
        return {"regions": []}


class ApiRouteTests(unittest.TestCase):
    def test_email_environment_variable_configures_portal_email(self):
        with patch.dict(
            "os.environ", {"URJA_EMAIL": "email@example.test"}, clear=True
        ):
            self.assertEqual(
                Settings.from_env().portal_email,
                "email@example.test",
            )

    def test_portal_route_reports_missing_credentials(self):
        app = create_app(Settings(portal_base_url="https://portal.test"))
        with TestClient(app) as client:
            response = client.get("/api/v1/meters")
            self.assertEqual(response.status_code, 503)
            self.assertIn("URJA_EMAIL", response.json()["detail"])

    def test_meter_and_consumption_routes_return_documented_shapes(self):
        app = create_app(Settings(portal_base_url="https://portal.test"))
        with patch("app.main.UrjaPortalClient", return_value=PortalStub()):
            with TestClient(app) as client:
                self.assertEqual(
                    client.get("/api/v1/meters").json(),
                    {"items": [{"meter_id": "M-1"}]},
                )
                self.assertEqual(
                    client.get("/api/v1/meters/M-1").json(),
                    {"meter": {"meter_id": "M-1"}},
                )
                self.assertEqual(
                    client.get(
                        "/api/v1/meters/M-1/consumption"
                    ).json(),
                    {"meter_id": "M-1", "records": [{"reading": "12.5"}]},
                )

    def test_login_route_accepts_email_and_password(self):
        app = create_app(Settings(portal_base_url="https://portal.test"))
        with patch("app.main.UrjaPortalClient", return_value=PortalStub()):
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/auth/login",
                    json={"email": "operator@example.test", "password": "secret"},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"authenticated": True})

    def test_health_and_openapi_routes_are_available_without_portal_access(self):
        app = create_app(Settings(portal_base_url="https://portal.test"))
        with patch("app.main.UrjaPortalClient", return_value=PortalStub()):
            with TestClient(app) as client:
                self.assertEqual(client.get("/health").json(), {"status": "ok"})
                schema = client.get("/openapi.json").json()
                self.assertIn("/api/v1/meters", schema["paths"])
                self.assertNotIn("security", schema["paths"]["/api/v1/meters"]["get"])


if __name__ == "__main__":
    unittest.main()
