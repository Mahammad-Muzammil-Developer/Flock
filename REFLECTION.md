# Reflection

The assignment references five reflection prompts but does not include their
exact wording. This document addresses five common reflection areas without
presenting unverified portal behavior as fact.

## 1. Assumptions made

The adapter defaults follow the route and form examples in the assignment:
`POST /login`, `GET /meters`, `GET /meters/{id}`, and
`GET /meters/{id}/consumption`. The real portal might use different paths,
payloads, CSRF tokens, or response formats. All route and form-field defaults
are configurable. Credentials are supplied through environment variables, not
embedded in source code.

## 2. Most difficult part

The main challenge is separating a stable public API contract from a legacy
protocol whose actual network behavior has not been inspected. The implementation
therefore normalizes only safely observable structure (JSON pass-through and
HTML table rows) and makes unknown assumptions explicit in `PROTOCOL.md`.

## 3. Mistakes and adjustments

The example snippets suggest likely portal routes and HTML selectors, but
copying them as confirmed facts would make the integration brittle. Instead,
the implementation treats the route names as defaults, exposes configuration,
and does not fabricate missing values or silently return empty records for
unrecognized responses.

## 4. Trade-offs

A single shared synchronous HTTP client is simple and retains cookies across
requests, but is suitable only for a trusted, single-instance deployment. It
does not isolate end-user sessions or coordinate session state across workers.
HTML parsing uses the first table's first row as column headings; this is
predictable for basic tables but cannot resolve nested or multi-header tables.
Numbers and dates are preserved as strings until their meaning is verified.

## 5. Future improvements

After authorized protocol discovery, document confirmed requests and edge cases,
implement any CSRF or token exchange, add fixtures from sanitized responses,
validate real response schemas and units, and test an authorized integration
environment. Before production, extend the shared API key to per-caller
identity, add session isolation and rate limiting, and add structured
observability with secret redaction and deployment configuration suitable for
multiple workers.
