# Flock Energy - Urja Meter Ops API

A small FastAPI REST wrapper that maintains an HTTP session with the legacy
Urja Meter Ops portal and presents meter, consumption, and hierarchy routes.
Portal behavior is not assumed to be verified; see [PROTOCOL.md](./PROTOCOL.md).

## Requirements and setup

- Python 3.10+

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:URJA_EMAIL = "your-authorized-portal-email"
$env:URJA_PASSWORD = "your-authorized-portal-password"
python -m uvicorn app.main:app --reload
```

The service listens at `http://127.0.0.1:8000`. Interactive API documentation
is available at `/docs`; the generated OpenAPI schema is at `/openapi.json`.
`openapi.json` in the repository is a checked-in schema snapshot. Refresh it
after changing routes with:

```powershell
python -c "import json; from app.main import app; open('openapi.json','w',encoding='utf-8').write(json.dumps(app.openapi(), indent=2) + '\n')"
```

The API starts without portal credentials so `/health` and documentation remain
available. Portal operations return `503` until `URJA_EMAIL` and
`URJA_PASSWORD` are configured. API routes do not require an API key. This means
anyone who can reach a public deployment can request meter and hierarchy data;
deploy only if that exposure is acceptable. Never commit portal credentials or
a `.env` file.

## API

- `GET /health`
- `POST /api/v1/auth/login` with `{"email":"...","password":"..."}`
- `GET /api/v1/meters` returns `{"items":[...]}`
- `GET /api/v1/meters/{meter_id}` returns `{"meter":{...}}`
- `GET /api/v1/meters/{meter_id}/consumption` returns
  `{"meter_id":"...","records":[...]}`
- `GET /api/v1/hierarchy` returns `{"hierarchy":...}`

Example requests:

```powershell
curl.exe http://127.0.0.1:8000/health
curl.exe -X POST http://127.0.0.1:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"your-authorized-portal-email\",\"password\":\"your-password\"}'
curl.exe http://127.0.0.1:8000/api/v1/meters
curl.exe http://127.0.0.1:8000/api/v1/meters/METER-001/consumption
```

The login endpoint establishes the shared portal session. Other portal routes
also log in automatically from the configured environment credentials when
needed. The shared session is intended for a single trusted service instance;
it is not a multi-tenant user-session store.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `URJA_BASE_URL` | `https://urja-ops.flockenergy.tech` | Portal origin |
| `URJA_EMAIL` / `URJA_PASSWORD` | unset | Authorized portal credentials |
| `URJA_LOGIN_PATH` | `/login` | Login route |
| `URJA_METERS_PATH` | `/meters` | Meter list route |
| `URJA_METER_DETAIL_PATH` | `/meters/{meter_id}` | Detail route template |
| `URJA_CONSUMPTION_PATH` | `/meters/{meter_id}/consumption` | Consumption route template |
| `URJA_HIERARCHY_PATH` | `/hierarchy` | Hierarchy route |
| `URJA_REQUEST_TIMEOUT` | `10` | Upstream timeout in seconds |

The portal login form field names were confirmed from browser Network
information. The default paths are still assumptions; configure them to match
observed authorized portal traffic. The API login request and the upstream
portal form both use `email` and `password`.

## Deploy to Render

The included [render.yaml](./render.yaml) defines a Render web service. To
publish it:

1. Push this project to a GitHub repository you control. The workspace must be
   a Git repository before it can be pushed.
2. In Render, choose **New** > **Blueprint**, connect that repository, and
   deploy the `render.yaml` blueprint.
3. In the Blueprint prompts or the service's **Environment** settings, set
   `URJA_EMAIL` and `URJA_PASSWORD` to authorized portal credentials. Never put
   secrets in `render.yaml` or Git.
4. After deployment, use the Render service URL with `/health` and `/docs`.

Render may require you to supply values for the `sync: false` secrets. The
`/health` endpoint intentionally remains public for the hosting platform's
health check. **All `/api/v1` endpoints are also public and do not require an
API key.** Anyone with the service URL can query the portal data available to
the configured account. Do not deploy publicly unless that data exposure is
acceptable.

## Design choices and limitations

- FastAPI supplies validation and a generated OpenAPI schema.
- A persistent `httpx.Client` retains cookies; a failed authenticated request
  triggers one re-login and retry.
- The adapter handles JSON and basic HTML tables. It does not infer numeric
  units or dates without verified portal semantics.
- Upstream route names, login form behavior, CSRF handling, and response
  structures are not known until inspected. No live portal test is represented
  as having passed.
- This example has one shared cookie session, no persistence, no API
  authentication, and no rate limiting. It is not suitable for public exposure
  when the configured portal account can access sensitive data.

## Validation

Install dependencies and run the local tests:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```
