import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    portal_base_url: str = "https://urja-ops.flockenergy.tech"
    portal_email: str = ""
    portal_password: str = ""
    login_path: str = "/login"
    meters_path: str = "/meters"
    meter_detail_path: str = "/meters/{meter_id}"
    consumption_path: str = "/meters/{meter_id}/consumption"
    hierarchy_path: str = "/hierarchy"
    request_timeout: float = 10.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            portal_base_url=os.getenv(
                "URJA_BASE_URL", "https://urja-ops.flockenergy.tech"
            ).rstrip("/"),
            portal_email=os.getenv("URJA_EMAIL", ""),
            portal_password=os.getenv("URJA_PASSWORD", ""),
            login_path=os.getenv("URJA_LOGIN_PATH", "/login"),
            meters_path=os.getenv("URJA_METERS_PATH", "/meters"),
            meter_detail_path=os.getenv(
                "URJA_METER_DETAIL_PATH", "/meters/{meter_id}"
            ),
            consumption_path=os.getenv(
                "URJA_CONSUMPTION_PATH", "/meters/{meter_id}/consumption"
            ),
            hierarchy_path=os.getenv("URJA_HIERARCHY_PATH", "/hierarchy"),
            request_timeout=float(os.getenv("URJA_REQUEST_TIMEOUT", "10")),
        )
