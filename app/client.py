import json
import re
import threading
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import Settings


class PortalError(Exception):
    """An upstream portal request failed or returned an unexpected response."""


class PortalConfigurationError(PortalError):
    """Required portal credentials have not been configured."""


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_response(response: httpx.Response) -> Any:
    content_type = response.headers.get("content-type", "").lower()
    if "json" in content_type:
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise PortalError("The portal returned invalid JSON.") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    tables = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [_clean_text(cell.get_text(" ", strip=True)) for cell in rows[0].find_all(["th", "td"])]
        if not headers or not any(headers):
            continue
        records = []
        for row in rows[1:]:
            values = [_clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
            if values:
                records.append(
                    {
                        headers[index] or f"column_{index + 1}": values[index]
                        for index in range(min(len(headers), len(values)))
                    }
                )
        tables.append(records)

    if tables:
        return tables[0] if len(tables) == 1 else {"tables": tables}
    text = _clean_text(soup.get_text(" ", strip=True))
    if not text:
        return {}
    return {"text": text}


def records_from(data: Any, label: str) -> list[dict[str, Any]]:
    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        return data
    if isinstance(data, dict):
        for key in ("items", "data", "results", "meters", "records"):
            value = data.get(key)
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                return value
    raise PortalError(f"The portal returned an unexpected {label} response shape.")


class UrjaPortalClient:
    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self.settings = settings
        self._client = client or httpx.Client(
            timeout=settings.request_timeout,
            follow_redirects=False,
            headers={"Accept": "application/json, text/html"},
        )
        self._owns_client = client is None
        self._authenticated = False
        self._username: str | None = settings.portal_username or None
        self._password: str | None = settings.portal_password or None
        self._lock = threading.RLock()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def login(self, username: str | None = None, password: str | None = None) -> bool:
        with self._lock:
            user = username if username is not None else self._username
            secret = password if password is not None else self._password
            if not user or not secret:
                raise PortalConfigurationError(
                    "Set URJA_USERNAME and URJA_PASSWORD before using portal endpoints."
                )

            login_url = self._url(self.settings.login_path)
            try:
                response = self._client.post(
                    login_url,
                    data={
                        self.settings.username_field: user,
                        self.settings.password_field: secret,
                    },
                )
            except httpx.HTTPError as exc:
                raise PortalError("Could not reach the portal login endpoint.") from exc

            if not 200 <= response.status_code < 400:
                raise PortalError(
                    f"Portal login failed with HTTP {response.status_code}."
                )
            if self._redirects_to_login(response):
                raise PortalError(
                    "The portal redirected back to login; credentials may be invalid."
                )
            self._username = user
            self._password = secret
            self._authenticated = True
            return True

    def _url(self, path: str) -> str:
        return urljoin(f"{self.settings.portal_base_url}/", path.lstrip("/"))

    def _redirects_to_login(self, response: httpx.Response) -> bool:
        location = response.headers.get("location")
        if not location:
            return False
        target = urlparse(urljoin(str(response.url), location))
        login = urlparse(self._url(self.settings.login_path))
        return target.path.rstrip("/") == login.path.rstrip("/")

    def _request(self, path: str) -> Any:
        with self._lock:
            if not self._authenticated:
                self.login()

            for attempt in range(2):
                try:
                    response = self._client.get(self._url(path))
                except httpx.HTTPError as exc:
                    raise PortalError("Could not reach the portal.") from exc

                expired = response.status_code in (401, 403) or self._redirects_to_login(
                    response
                )
                if expired and attempt == 0:
                    self._authenticated = False
                    self.login()
                    continue
                if expired:
                    raise PortalError("Portal session expired or access was denied.")
                if response.is_redirect:
                    raise PortalError(
                        "The portal redirected unexpectedly instead of returning data."
                    )
                if not response.is_success:
                    raise PortalError(
                        f"Portal request failed with HTTP {response.status_code}."
                    )
                return parse_response(response)

            raise PortalError("Portal request failed after re-authentication.")

    def get_meters(self) -> list[dict[str, Any]]:
        return records_from(self._request(self.settings.meters_path), "meters")

    def get_meter(self, meter_id: str) -> dict[str, Any]:
        path = self.settings.meter_detail_path.format(
            meter_id=quote(meter_id, safe="")
        )
        data = self._request(path)
        if isinstance(data, dict):
            if isinstance(data.get("meter"), dict):
                return data["meter"]
            return data
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return {"records": data}
        raise PortalError("The portal returned an unexpected meter detail response shape.")

    def get_consumption(self, meter_id: str) -> list[dict[str, Any]]:
        path = self.settings.consumption_path.format(
            meter_id=quote(meter_id, safe="")
        )
        return records_from(self._request(path), "consumption")

    def get_hierarchy(self) -> Any:
        return self._request(self.settings.hierarchy_path)
