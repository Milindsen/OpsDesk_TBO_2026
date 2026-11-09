# OpsDesk — TBO Problem Statement Traceability

This repository implements the **OpsDesk for TBO (Zendesk)** challenge in Part A / Part B of the supplied brief. The separate **AI-Native HR Services Platform (DarwinBox)** challenge in the same pasted document is a different problem statement and is not in scope for this codebase.

## Must-have MVP checklist

- [x] MVP-1: Create tickets with title, description, agency identity, TBOH, priority, intent/category, check-in and LCD.
- [x] MVP-1: First-class links by TBOH, agency and intent; Case 360 history and contact count.
- [x] MVP-1: Manual intent selection and lightweight ML auto-suggest; documented model/fallback.
- [x] MVP-1: Status flow and timeline for status, assignment, links, escalation and comments.
- [x] MVP-2: Assign, reassign and unassign with clear ownership/audit trail.
- [x] MVP-2: Routing uses region, local shift window, priority, availability and workload ranking; no eligible agent returns ticket to Triage.
- [x] MVP-2: Triage, My Queue, region, intent, linked-case and escalation views.
- [x] MVP-2: Human-readable routing reason.
- [x] MVP-3: Side conversations have explicit recipients independent of ticket group.
- [x] MVP-3: Recipients survive reassignment and the event is recorded.
- [x] MVP-3: Internal notes and external replies are distinct; ticket comments are separately persisted.
- [x] MVP-4: SLA uses priority plus check-in/LCD proximity; at-risk and breached states are visible.
- [x] MVP-4: First-class escalation assigns to an Escalation Manager and records a timeline event.
- [x] MVP-5: Theme tagging and weekly theme insights with sample tickets; tags refresh from ticket text, public comments and external side-conversation messages (internal notes excluded).
- [x] MVP-5: Optional suggested product/bug link field.
- [x] MVP-6: PostgreSQL persistence survives refresh/restart when the named volume is retained.
- [x] MVP-6: CSV export is streamed with keyset pagination and no artificial 3K cap; bulk seed supports 50K rows.
- [x] MVP-6: Closed tickets older than 90 days are archived with ticket history snapshots.
- [x] MVP-7: Requester, Agent, Escalation Manager and Lead permissions are enforced at API level; requester data is agency-scoped.
- [x] Technical: README/run steps, demo accounts, 5-minute demo script, empty/loading/error states, Pydantic validation and security controls.

## Explicit limitations / stretch features

- Regional holiday calendars and cross-team dependency calendars are not implemented; the must-have SLA uses priority and check-in/LCD proximity.
- Queue freshness uses 15-second polling. WebSocket/CDC push is documented as a production scale path, not claimed as implemented.
- Side-conversation recipients/messages are persisted in OpsDesk; outbound email delivery is not wired to an external mail provider.
- Supplier portal UX, webhooks, CSAT, macros, full omnichannel, production SSO and multi-tenancy are not implemented; these are optional/out of scope in the supplied brief.
- Demo agents are seeded with a 00:00–23:59 shift to make routing demos deterministic at any presentation time. Change `shift_start`, `shift_end` and `availability` in the seeded users to exercise off-shift routing.

## Verification status in this build environment

- Python source syntax compilation: passed (`python -m compileall -q backend/app backend/tests`).
- Backend pytest execution (34 test functions): not completed here because runtime packages including `psycopg2`, `APScheduler`, `python-jose` and `passlib` are not installed in this environment. Install `backend/requirements.txt` or use Docker before treating the test suite as passed.
- Frontend build: not completed here because npm dependencies were not available offline. Run `npm ci && npm run build` in `frontend/` or use Docker with network access.
