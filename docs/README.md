# Pulse documentation

Project site and guide: <https://moneytosms.github.io/Pulse/> (guide at <https://moneytosms.github.io/Pulse/guide/>). Repository overview: [`../README.md`](../README.md).

This folder is organized around the questions a reader is trying to answer. The source code remains authoritative for current behavior; workflow pages describe the user journey and link to the implementation, while plans and design documents may describe work that is not shipped yet.

## Start here

| If you are… | Read this first | Then read |
|---|---|---|
| New to Pulse | [`../CONTEXT.md`](../CONTEXT.md) | [Workflow map](workflows/README.md), [Architecture](architecture.md) |
| Learning what each person can do | [Workflow map](workflows/README.md) | [Demo walkthrough](demo.md), [Domain model](domain-model.md) |
| Implementing a feature | [Architecture](architecture.md) | [API conventions](api-conventions.md), [Domain model](domain-model.md), [ADRs](adr/) |
| Preparing a presentation or demo | [Demo walkthrough](demo.md) | [Video script](video-script.md), [Seed data](seed-data.md), [`../seed/README.md`](../seed/README.md), [`../RUNNING.md`](../RUNNING.md) |
| Running or verifying the project | [Verification and operations](verification-and-operations.md) | [`../RUNNING.md`](../RUNNING.md), [Frontend reliability](frontend-reliability.md) |
| Understanding design direction | [`../DESIGN.md`](../DESIGN.md) | [Design direction](design-direction.md) (typography research) |
| Reviewing delivery and team ownership | [Delivery plan](delivery-plan.md) | [`agents/`](agents/): [issue tracker](agents/issue-tracker.md), [triage labels](agents/triage-labels.md), [domain docs](agents/domain.md) |

## Document map

| Area | What belongs here |
|---|---|
| [`workflows/`](workflows/README.md) | Actor journeys, feature boundaries, and links from screens to backend behavior |
| [`adr/`](adr/) | Accepted architectural decisions and their trade-offs |
| [`agents/`](agents/) | Repository collaboration and issue-tracking conventions ([issue tracker](agents/issue-tracker.md), [triage labels](agents/triage-labels.md), [domain docs](agents/domain.md)) |
| [`archive/`](archive/) | Superseded drafts retained for historical context; not current specifications |
| Root docs | Architecture, domain/API contracts, delivery, demo, operations, design, and implementation learnings |

## Source of truth and status

- **Implemented behavior:** verify against `frontend/src/`, `backend/app/`, and the relevant tests. Workflow pages call out UI gaps and backend-only capabilities explicitly.
- **Architecture and domain rules:** [`architecture.md`](architecture.md), [`domain-model.md`](domain-model.md), and the numbered ADRs.
- **Plans:** [`delivery-plan.md`](delivery-plan.md) is planning material, not proof that a feature is shipped. The old status tracker is archived at [`archive/next-steps.md`](archive/next-steps.md).
- **Historical material:** [`archive/`](archive/) is intentionally retained but superseded.
- **Demo specifics:** [`demo.md`](demo.md) and [`../RUNNING.md`](../RUNNING.md) include local setup and seeded test identities. Do not use seeded identities as real patient data.

The practical invariant that connects the whole product is: a Clinician's role alone never grants clinical access; each read is filtered through the patient's active permission and written to the audit trail. See [record access and consent](workflows/README.md#4-patient-shares-a-record-with-a-clinician).
