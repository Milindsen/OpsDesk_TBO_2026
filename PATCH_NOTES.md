# OpsDesk — Implementation Patch Notes

This build is aligned to the **OpsDesk for TBO (Zendesk)** problem statement (the first challenge in the supplied text). The separate DarwinBox HR Services challenge is not part of this application.

## Changes made

- Fixed frontend/backend API contract mismatches for `/me`, `/insights/themes`, `/users`, and side-conversation message posting.
- Added a staff-only `/users` directory endpoint used by assignment and escalation pickers.
- Implemented backend priority and linked-case filters; aligned region selectors with the actual seeded regions (`IN-West`, `IN-East`, `ME`).
- Corrected the Alembic migration that redundantly attempted to add/drop `archived_tickets.product_bug_link`.
- Tightened requester and Escalation Manager access scopes; redacted cross-agency links, staff routing details, internal comments, side-thread metadata, escalation details and internal product/bug links from requester responses.
- Added requester-safe timeline serialization and dynamic timeline events for ticket links.
- Aligned timeline UI event names/payloads with the backend (`from`/`to`, `agent_name`, `em_name`, `side_convo`, `ticket_link`, comments, unassignment and recipient-preservation events).
- Made queue SLA indicators refresh dynamically when ticket lists are loaded.
- Fixed routing workload scoring to use the actual open-ticket counts, excluded unavailable/off-shift agents, logged no-eligible-agent outcomes and returned those tickets to Triage.
- Corrected assignment workload counters for terminal tickets and prevented repeated decrements on Resolved → Closed.
- Added request validation for ticket and side-conversation inputs.
- Added and enforced durable ticket comments with public/internal visibility.
- Added timeline events for automatic ticket links and aligned all timeline descriptions with the backend event payloads.
- Fixed insights response typing and sample-ticket fields to match the actual backend schema; weekly themes now use recent ticket activity and are refreshed from public comments/external side-conversation messages (internal notes excluded).
- Fixed 50K bulk seeding so Docker invokes it only when `SEED_BULK=true`; generation is resumable/idempotent and does not duplicate rows on restart.
- Made demo shifts deterministic and corrected the seeded TBO12345 contact count so the newest ticket is actually the third contact.
- Added loading/error feedback to ticket creation and corrected the no-agent routing success message.
- Updated README, demo script, and `PS_TRACEABILITY.md`.

## Verification

- `python -m compileall -q backend/app backend/tests` passes.
- The backend suite now contains 34 test functions, including RBAC, timeline privacy, routing eligibility, queue SLA refresh, unassignment, side-recipient transfer, and ticket-link timeline coverage.
- The backend pytest suite was **not executed** in this environment because the runtime dependencies are not installed here.
- The frontend full build was **not executed** because npm packages could not be downloaded in this environment. A global TypeScript parse/type scan showed no syntax or property-contract errors in the modified files, but this is not a substitute for `npm ci && npm run build`.
- Docker is not installed in this environment, so clean Compose startup and database migrations still need to be run on your machine.

## Run locally

1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. Open `http://localhost`.
4. API docs: `http://localhost:8000/docs`.
5. To wipe and reseed the database: `docker compose down -v`, then `docker compose up --build`.
6. For the 50K export demo, set `SEED_BULK=true` in `.env` before starting Compose.
