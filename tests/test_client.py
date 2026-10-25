import unittest

import httpx

from app.client import PortalError, UrjaPortalClient, parse_response, records_from
from app.config import Settings


class ClientParsingTests(unittest.TestCase):
    def test_parse_html_table_collapses_whitespace(self):
        response = httpx.Response(
            200,
            headers={"content-type": "text/html"},
            text="<table><tr><th> Meter  ID </th><th>Status</th></tr>"
            "<tr><td> M-1 </td><td> Active\n now </td></tr></table>",
        )
        self.assertEqual(
            parse_response(response),
            [{"Meter ID": "M-1", "Status": "Active now"}],
        )

    def test_parse_json(self):
        response = httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"items": [{"id": "M-1"}]},
        )
        self.assertEqual(parse_response(response), {"items": [{"id": "M-1"}]})

    def test_records_rejects_unexpected_shapes(self):
        with self.assertRaises(PortalError):
            records_from({"items": "not a list"}, "meters")

    def test_detail_accepts_html_table_records(self):
        def handler(request):
            return httpx.Response(
                200,
                request=request,
                headers={"content-type": "text/html"},
                text="<table><tr><th>Property</th><th>Value</th></tr>"
                "<tr><td>Status</td><td>Active</td></tr></table>",
            )

        client = httpx.Client(transport=httpx.MockTransport(handler))
        portal = UrjaPortalClient(
            Settings(
                portal_base_url="https://portal.test",
                portal_username="operator",
                portal_password="secret",
            ),
            client=client,
        )
        try:
            self.assertEqual(
                portal.get_meter("M-1"),
                {"records": [{"Property": "Status", "Value": "Active"}]},
            )
        finally:
            portal.close()
            client.close()


class ClientSessionTests(unittest.TestCase):
    def test_reauthenticates_once_after_unauthorized_response(self):
        calls = []

        def handler(request):
            calls.append((request.method, request.url.path))
            if request.url.path == "/login":
                return httpx.Response(200, request=request)
            if len([call for call in calls if call[1] == "/meters"]) == 1:
                return httpx.Response(401, request=request)
            return httpx.Response(
                200,
                request=request,
                headers={"content-type": "application/json"},
                json=[{"id": "M-1"}],
            )

        transport = httpx.MockTransport(handler)
        client = httpx.Client(transport=transport, follow_redirects=False)
        settings = Settings(
            portal_base_url="https://portal.test",
            portal_username="operator",
            portal_password="secret",
        )
        portal = UrjaPortalClient(settings, client=client)
        try:
            self.assertEqual(portal.get_meters(), [{"id": "M-1"}])
            self.assertEqual(
                [path for _, path in calls],
                ["/login", "/meters", "/login", "/meters"],
            )
        finally:
            portal.close()
            client.close()

    def test_explicit_login_credentials_are_reused_after_session_expiry(self):
        calls = []

        def handler(request):
            calls.append((request.method, request.url.path))
            if request.url.path == "/login":
                return httpx.Response(200, request=request)
            if len([call for call in calls if call[1] == "/meters"]) == 1:
                return httpx.Response(401, request=request)
            return httpx.Response(
                200,
                request=request,
                headers={"content-type": "application/json"},
                json=[],
            )

        client = httpx.Client(
            transport=httpx.MockTransport(handler), follow_redirects=False
        )
        portal = UrjaPortalClient(
            Settings(portal_base_url="https://portal.test"), client=client
        )
        try:
            portal.login("operator", "secret")
            self.assertEqual(portal.get_meters(), [])
            self.assertEqual(
                [path for _, path in calls],
                ["/login", "/meters", "/login", "/meters"],
            )
        finally:
            portal.close()
            client.close()

    def test_login_requires_credentials(self):
        portal = UrjaPortalClient(Settings(portal_base_url="https://portal.test"))
        try:
            with self.assertRaises(PortalError):
                portal.get_meters()
        finally:
            portal.close()


if __name__ == "__main__":
    unittest.main()
