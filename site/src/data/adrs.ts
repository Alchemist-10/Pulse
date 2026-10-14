// Chapter 16 data. Hand-written from the ADR texts in docs/adr/ (read in full
// on 2026-10-14). `slug` is the guide slug (file name without .md). Each entry
// cites the ADR section its "over" and "consequence" lines paraphrase.

export type Adr = {
  n: string; // ADR number as printed in the file name
  slug: string;
  claim: string; // the decision, as a short claim
  over: string; // what it was chosen over (or what it replaced)
  overLabel?: string; // defaults to "Chosen over"
  consequence: string; // what it costs or forces, as the ADR states it
};

export type AdrGroup = { id: string; title: string; blurb: string; adrs: Adr[] };

export const adrGroups: AdrGroup[] = [
  {
    id: "read",
    title: "Who may read",
    blurb: "Sessions, route guards, the one query builder, and the people the model refuses to trust.",
    adrs: [
      {
        n: "0003",
        slug: "adr/0003-opaque-redis-sessions-not-jwt",
        claim: "Sessions are opaque tokens in Redis, not JWTs.",
        over: "JWTs, which stay valid until they expire. Immediate revocation would need a server-side denylist, which is session state again.", // 0003 "Why", para 1
        consequence: "Redis becomes load-bearing for login: wipe it and everyone logs in again. The token is stored under its SHA-256, so a dump yields no usable sessions.", // 0003 "Consequences"
      },
      {
        n: "0004",
        slug: "adr/0004-default-deny-route-authorization",
        claim: "Every route declares a permission or an explicit public marker, and a test fails CI if one declares neither.",
        over: "Convention and code review. The realistic failure is a missing check on an endpoint added late, which only a red build always catches.", // 0004 "Why"
        consequence: "The test had to exist before the modules did: introduced against three endpoints it is free, retrofitted against sixty it invites marking things public.", // 0004 "Consequences"
      },
      {
        n: "0006",
        slug: "adr/0006-consent-enforced-by-one-query-builder",
        claim: "Consent is part of the SQL, built in one function: accessible_entries(actor, patient_id).",
        over: "Scattered checks, and Postgres row-level security, which needs per-request SET LOCAL variables that interact badly with connection pooling.", // 0006 "Why", para 3
        consequence: "Enforcement is a lint plus negative integration tests, not a formal guarantee. No permission decision may be cached, and analytics must compose from the same builder.", // 0006 "Consequences"
      },
      {
        n: "0007",
        slug: "adr/0007-administrators-cannot-read-clinical-data",
        claim: "The Administrator role grants no access to Medical Entries or Documents at all.",
        over: "Administrator as superuser. That is how hundreds of staff end up able to read one person's file, and it makes the consent model decorative.", // 0007 "Why"
        consequence: "No administrative override exists. The emergency path is break-glass, invoked by a clinician, time-boxed, justified and visible to the patient.", // 0007 "Consequences"
      },
      {
        n: "0010",
        slug: "adr/0010-consent-is-granted-to-individuals",
        claim: "A Patient consents to a named Clinician, never to a Provider organisation.",
        over: "Organisation-level grants, where consenting to a hospital means thousands of people can read the record.", // 0010 "Why"
        consequence: "A Clinician who changes Provider keeps their consents. A patient seen by several doctors at one hospital grants several consents, which the ADR accepts.", // 0010 "Consequences"
      },
    ],
  },
  {
    id: "stored",
    title: "How clinical data is stored",
    blurb: "The shape of the record, and what is deliberately not stored.",
    adrs: [
      {
        n: "0001",
        slug: "adr/0001-medical-entry-joined-table-inheritance",
        claim: "One medical_entry trunk table plus one table per entry kind.",
        over: "A single wide table with about 25 nullable columns, and a JSONB payload, which makes lab trends a cast and lets \"120/80\" land where a number belongs.", // 0001 "Considered options"
        consequence: "Timeline reads cost one query for the trunk plus one per kind present: at most six indexed queries for a 50-entry page, flat in page size.", // 0001 "Consequences"
      },
      {
        n: "0002",
        slug: "adr/0002-patient-is-the-aggregate-root",
        claim: "Patient is the aggregate root. There is no separate Patient Record entity.",
        over: "The earlier design, a strict one-to-one Patient Record, which cost a join on every read and gave one concept two names.",
        overLabel: "Replaces", // 0002 first paragraph
        consequence: "patient.user_id is nullable and load-bearing: it is what lets a Provider file for someone who has never registered. It must not be tidied into a required column.", // 0002 "Consequences"
      },
      {
        n: "0009",
        slug: "adr/0009-analytics-computed-on-read",
        claim: "Analytics are computed per request, through the consent filter. There is no Summary Insight table.",
        over: "A stored insight row, which is computed once without an actor and so is either unfiltered or recomputed per actor anyway.", // 0009 "Why"
        consequence: "Every analytics query composes from accessible_entries. If a chart is ever slow, the answer is a Postgres materialised view, not Redis.", // 0009 "Consequences"
      },
      {
        n: "0015",
        slug: "adr/0015-synthea-plus-indian-overlay-seed-data",
        claim: "Seed data is Synthea output with a deterministic Indian identity overlay, committed to the repo.",
        over: "Hand-written histories, and regenerating on setup, which would need a JDK on every machine before git clone and docker compose up could work.", // 0015 "Why"
        consequence: "The dataset is megabytes of CSV that diff review will not inspect. Regeneration is pinned to a Synthea version and seeds. Planted near-misses make detection precision measurable.", // 0015 "Consequences"
      },
    ],
  },
  {
    id: "history",
    title: "Keeping history honest",
    blurb: "The audit log, merges, and what happens inside a transaction.",
    adrs: [
      {
        n: "0008",
        slug: "adr/0008-audit-log-is-append-only-by-grant",
        claim: "The application's database role holds INSERT and SELECT on audit_event and nothing else.",
        over: "\"We simply don't update that table\", which is an intention that lasts until someone writes a cleanup script.", // 0008 "Why"
        consequence: "Two database roles exist from the first migration. Audit corrections are impossible by design: a wrong event is fixed by writing a new one.", // 0008 "Consequences"
      },
      {
        n: "0011",
        slug: "adr/0011-merges-are-human-only-and-reversible",
        claim: "Duplicate detection only creates a review item. A person merges, and every merge records enough to be undone.",
        over: "Merging automatically above a similarity score. A missed duplicate is an inconvenience; a wrong merge is a patient-safety incident.", // 0011 "Why"
        consequence: "The losing Patient is tombstoned with merged_into_id, never deleted. ADR-0016 later made reversal conditional on nothing having been built on the merge.", // 0011 "Consequences", last line
      },
      {
        n: "0016",
        slug: "adr/0016-transactional-audit-and-safe-identity-merges",
        claim: "A clinical operation commits its change, its audit event and its in-app notification together, and a clinical read commits its audit event first.",
        over: "The unconditional reversibility wording of ADR-0011: reversal now fails with a coded 409 if later corrections or documents depend on the merge.",
        overLabel: "Tightens", // 0016 "Supported merges and reversals", last paragraph
        consequence: "If the audit write fails, the read fails. Email still runs after the commit and is best effort, because guaranteed delivery would need a durable outbox.", // 0016 intro paragraph
      },
    ],
  },
  {
    id: "fit",
    title: "How the pieces fit",
    blurb: "Infrastructure and contract choices that look like plumbing and are not.",
    adrs: [
      {
        n: "0005",
        slug: "adr/0005-redis-is-never-a-source-of-truth",
        claim: "Redis holds sessions, rate limits and short-lived tokens. Never a source of truth.",
        over: "Letting a cache grow into patient lists and denormalised timelines, each of which looks reasonable alone.", // 0005 "Why"
        consequence: "Anything that must survive a restart lives in PostgreSQL. Consent stays in Postgres even though checking it from a cache would be faster.", // 0005 "Consequences"
      },
      {
        n: "0012",
        slug: "adr/0012-same-origin-reverse-proxy",
        claim: "Caddy serves the frontend and the API from one origin, everywhere.",
        over: "Next.js and FastAPI on separate ports with CORS written to paper over it. Cross-origin cookies force SameSite=None, then Secure, then HTTPS on a laptop.", // 0012 "Why"
        consequence: "Caddy is in the request path even locally, and the next-intl middleware matcher must exclude /api or every API call breaks.", // 0012 "Consequences"
      },
      {
        n: "0013",
        slug: "adr/0013-error-codes-not-messages",
        claim: "The API returns error codes, never user-facing strings.",
        over: "Returning renderable English, which is untranslatable across four locales without touching every endpoint.", // 0013 "Why"
        consequence: "Codes are a permanent contract and are never reworded. The enum is exported through OpenAPI and generated into a TypeScript union.", // 0013 "Consequences"
      },
      {
        n: "0014",
        slug: "adr/0014-code-first-api-with-stub-endpoints",
        claim: "Pydantic schemas are the contract, and stub endpoints ship before implementations.",
        over: "A hand-maintained OpenAPI file, which drifts from the code within a fortnight, and a frontend waiting on finished handlers.", // 0014 "Why"
        consequence: "The schema merge becomes the real integration gate, so schemas get reviewed harder than handlers. CI prints the stub inventory on every run.", // 0014 "Consequences"
      },
    ],
  },
];
