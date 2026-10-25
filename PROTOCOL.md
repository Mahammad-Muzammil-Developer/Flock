# Urja Meter Ops protocol notes

## Verification status

No authenticated browser or network inspection of the live portal was performed
for this implementation. The routes and login form below are **configurable
starting assumptions taken from the assignment examples**, not confirmed
observations. Verify them with an authorized account and record changes here
before relying on this adapter in production.

## Current assumptions (unverified)

| Purpose | Method | Default path | Assumed request/response |
| --- | --- | --- | --- |
| Login | POST | `/login` | Form fields `username` and `password`; an HTTP success response establishes a cookie session |
| Meter list | GET | `/meters` | JSON list/object or an HTML table |
| Meter detail | GET | `/meters/{meter_id}` | JSON object or an HTML table |
| Consumption | GET | `/meters/{meter_id}/consumption` | JSON list/object or an HTML table |
| Hierarchy | GET | `/hierarchy` | JSON or HTML |

The client retains cookies in a shared `httpx.Client`, detects 401/403 and
redirects to the configured login path, and retries one time after logging in.
It does not claim to know whether the portal requires CSRF tokens, a JSON login
body, additional headers, or different route names.

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
