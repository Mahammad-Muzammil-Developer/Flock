import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class PortalStub:
    def close(self):
        pass

    def login(self, username, password):
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
    def test_portal_route_reports_missing_credentials(self):
        app = create_app(
            Settings(portal_base_url="https://portal.test", api_key="test-key")
        )
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/meters", headers={"X-API-Key": "test-key"}
            )
            self.assertEqual(response.status_code, 503)
            self.assertIn("URJA_USERNAME", response.json()["detail"])

    def test_api_routes_reject_missing_or_invalid_api_key(self):
        app = create_app(
            Settings(portal_base_url="https://portal.test", api_key="test-key")
        )
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/v1/meters").status_code, 401)
            self.assertEqual(
                client.get(
                    "/api/v1/meters", headers={"X-API-Key": "wrong-key"}
                ).status_code,
                401,
            )

    def test_api_routes_fail_closed_when_api_key_is_unconfigured(self):
        app = create_app(Settings(portal_base_url="https://portal.test"))
        with TestClient(app) as client:
            response = client.get("/api/v1/meters")
            self.assertEqual(response.status_code, 503)
            self.assertIn("API_KEY", response.json()["detail"])

    def test_meter_and_consumption_routes_return_documented_shapes(self):
        app = create_app(
            Settings(portal_base_url="https://portal.test", api_key="test-key")
        )
        with patch("app.main.UrjaPortalClient", return_value=PortalStub()):
            with TestClient(app) as client:
                headers = {"X-API-Key": "test-key"}
                self.assertEqual(
                    client.get("/api/v1/meters", headers=headers).json(),
                    {"items": [{"meter_id": "M-1"}]},
                )
                self.assertEqual(
                    client.get("/api/v1/meters/M-1", headers=headers).json(),
                    {"meter": {"meter_id": "M-1"}},
                )
                self.assertEqual(
                    client.get(
                        "/api/v1/meters/M-1/consumption", headers=headers
                    ).json(),
                    {"meter_id": "M-1", "records": [{"reading": "12.5"}]},
                )

    def test_health_and_openapi_routes_are_available_without_portal_access(self):
        app = create_app(
            Settings(portal_base_url="https://portal.test", api_key="test-key")
        )
        with patch("app.main.UrjaPortalClient", return_value=PortalStub()):
            with TestClient(app) as client:
                self.assertEqual(client.get("/health").json(), {"status": "ok"})
                schema = client.get("/openapi.json").json()
                self.assertIn("/api/v1/meters", schema["paths"])
                self.assertEqual(
                    schema["components"]["securitySchemes"]["APIKeyHeader"]["name"],
                    "X-API-Key",
                )
                self.assertIn(
                    {"APIKeyHeader": []},
                    schema["paths"]["/api/v1/meters"]["get"]["security"],
                )


if __name__ == "__main__":
    unittest.main()
