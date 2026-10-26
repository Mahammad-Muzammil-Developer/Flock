# Urja Meter Ops protocol notes

## Verification status

Browser Network information confirmed the login form field names and a
successful login response. Other routes and response formats remain
**configurable starting assumptions taken from the assignment examples** and
should be verified with an authorized account before production use.

## Current protocol details

| Purpose | Method | Default path | Request/response |
| --- | --- | --- | --- |
| Login | POST | `/login` | Form fields `email` and `password` (confirmed); a successful response sets a session cookie. |
| Meter list | GET | `/meters` | JSON list/object or an HTML table |
| Meter detail | GET | `/meters/{meter_id}` | JSON object or an HTML table |
| Consumption | GET | `/meters/{meter_id}/consumption` | JSON list/object or an HTML table |
| Hierarchy | GET | `/hierarchy` | JSON or HTML |

The client retains cookies in a shared `httpx.Client`, detects 401/403 and
redirects to the configured login path, and retries one time after logging in.
The login path is still an assumption, and whether the portal requires CSRF
tokens or additional headers has not been verified.

## Parsing and normalization

- JSON responses are passed through without changing portal field names or
  values. The API wraps meter lists and consumption records in stable top-level
  response objects.
- HTML tables are converted to records using the first row as column headings;
  whitespace is collapsed. HTML-only content without a table is returned as
  `{"text": "..."}`.
- Numeric and date strings are deliberately not coerced: their units, locale,
  and formats have not been verified.
- An unexpected record shape or upstream error becomes an explicit `502`
  response instead of a success-shaped empty result.

## How to verify and update

With authorization, use browser DevTools Network panel to inspect the login
request, redirects, cookies, any CSRF mechanism, and the meter and consumption
requests. Confirm response formats and representative edge cases. Update the
table and parsing rules above, then set the corresponding `URJA_*` environment
variables described in `README.md`. Do not add live credentials or session
cookies to this document or source control.
