# API Conventions

What every endpoint in Pulse looks like. This is the document the team reads daily; if an endpoint disagrees with this file, the endpoint is wrong.

Resolved in [#14](https://github.com/moneytosms/Pulse/issues/14).

## Shape

`/api/v1/...`, plural resource nouns. Nest only where the child cannot exist without the parent.

```
/api/v1/patients/{id}
/api/v1/patients/{id}/entries       entries are meaningless without a patient
/api/v1/entries/{id}                but addressable directly once you have the id
/api/v1/consents?patientId=…        flat, filtered
/api/v1/audit-events?patientId=…
```

Versioned from the first commit. One path segment now; a migration later.

## Casing

**JSON is camelCase. Python stays snake_case.** Pydantic converts at the boundary, configured once on a shared base model:

```python
class PulseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
        json_schema_serialization_defaults_required=True,
    )
```

> **`populate_by_name` is deprecated as of Pydantic 2.11** — use `validate_by_name` / `validate_by_alias`. Every tutorial still shows the old one.

## Errors

Every non-2xx response has this body:

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Consent was already revoked.",
    "details": [{ "field": "body.entryTypes", "code": "enum" }],
    "requestId": "3f2b8c1e-9a47-4d6e-b0c5-7e1d2a9f4c68"
  }
}
```

- **`code`** is the contract. `SCREAMING_SNAKE_CASE`, stable forever, never reworded.
- **`message`** is an English default for developers and logs. **The frontend never renders it** — it renders from `code`. That is what makes four locales possible.
- **`details`** carries field-level validation failures so forms can highlight inputs.
- **`requestId`** is a UUID generated per request (a client-supplied `X-Request-Id` matching `[A-Za-z0-9._:-]{1,64}` is accepted instead), returned in the body and in `X-Request-Id`, logged, and recorded on audit events.

FastAPI's default `{"detail": ...}` is replaced by a global exception handler — including for `RequestValidationError`, or validation responses become the one endpoint shape that differs.

Codes live in a single Python enum, exported through OpenAPI and generated into a TypeScript union at build time. Neither side hand-maintains a list. An unrecognised code falls back to a generic message rather than rendering blank.

## Status codes

| Code | Meaning |
|---|---|
| 400 | malformed request |
| 401 | not authenticated |
| 403 | authenticated, role forbids it — reveals no resource existence. Also covers `STEP_UP_REQUIRED`, `EMAIL_NOT_VERIFIED` and cross-origin writes |
| **404** | role allows it, but no consent covers this record |
| 409 | conflict — re-revoking a consent, duplicate resolution race |
| 405 | method not allowed (`VALIDATION_ERROR`) |
| 413 | upload too large |
| 422 | validation failed |
| 429 | rate limited |
| 500 | unexpected server error |
| 503 | not ready (`/ready`) |

**404, not 403, for consent denials.** A 403 on a specific patient's record confirms the record exists, which reveals that the person is a patient. In a health system, that is the disclosure that matters.

## Pagination

Keyset cursors on persisted collections, default `limit` 50, maximum 100. The UI uses "load more".

```
GET /api/v1/patients/{id}/entries?cursor=…&limit=50
→ { "items": [...], "nextCursor": "…" }
```

Offset pagination is more familiar and is wrong here: the patient timeline and the audit log are both append-heavy, and offset paging silently skips or duplicates rows when new data lands mid-scroll. It corrupts precisely the two views that must be trustworthy, and it does so invisibly.

The cost is no page numbers. Computed chart endpoints are the exception: they return arrays bounded by `fromDate` / `toDate` and a 5,000-row ceiling (`ANALYTICS_WINDOW_TOO_LARGE`).

## Filtering and sorting

Order is fixed (`occurredAt` descending). Filters are explicit named parameters, never a generic query DSL. The filters that exist are `entryType`, `fromDate`, `toDate`, `providerId`, `q` (max 100 characters), `view`, `action`, `since`, `until` and `actorRole`.

## Uploads

`multipart/form-data`, one file per request.

- Size cap enforced, MIME **allowlist** never a blocklist
- Content sniffed server-side — the declared `Content-Type` and the file extension are both attacker-controlled
- SHA-256 computed on receipt and stored, and re-verified on download, so corruption is detectable

Routes never touch the filesystem. They hand bytes to `StorageProvider` and store the returned path.

## Stub endpoints

Stubs exist so frontend work never blocks on backend work, which means they will be forgotten.

A stub is decorated `@stub`: it returns fixture data, sets `X-Pulse-Stub: true`, and registers itself. CI prints the stub inventory on every run, so the count is visible in every PR instead of discovered the week of submission. No stubs remain; the inventory prints zero.

The full endpoint inventory is in the generated OpenAPI (`/api/v1/docs` at runtime; `frontend/src/lib/generated/api.ts`).
