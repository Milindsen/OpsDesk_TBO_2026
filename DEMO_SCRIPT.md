# OpsDesk — 5-Minute Demo Script

> Hand this to the presenter. Each section is timed. Total ≈ 4m 45s.

---

## 0:00 — Opening (20s)

> "OpsDesk replaces isolated Zendesk-style tickets with context-rich, travel-aware operations cases.
> One self-hosted React + FastAPI + PostgreSQL stack; no paid add-on API dependency in the demo.
> Let me walk you through five journeys that map to the six problems in the brief."

Login as **agent1@tbo.com / Demo@1234**

---

## 0:20 — Journey A: Context & Linkage (Problem 1) — 1 min

1. Click **Triage** tab → open ticket `TBO12345` (refund, P2, Horizons Travel).
2. Point to the **amber banner**: *"3rd contact about refund from Horizons Travel"*  
   → This is `contact_count = 3` — no manual stitching.
3. Point to **Linked Tickets** sidebar:  
   - 2 strong links (same TBOH, score 1.0) — reason: "Same TBOH: TBO12345"  
   - Click one link → opens prior ticket in a new tab.
4. Point to **Intent** badge: `refund` — auto-classified.  
   → Go to **Create Ticket** → type "need a refund for my hotel booking" → click **Suggest Intent**  
   → Top-3 appears: **refund 65%**, cancellation 20%, payment 10%.  
   → Click to auto-select.

**Key line:** *"Three contacts, one TBOH — no third-party app, no manual linking."*

---

## 1:20 — Journey B: Routing (Problem 2) — 55s

1. Click **Create Ticket**.
2. Fill: Title = "Urgent flight cancellation", TBOH = `TBO-DEMO`, Priority = **P1**, Region = **IN-West**, Intent = `cancellation`.
3. Submit → ticket is created.
4. Open the new ticket → **Routing Info** card on the right:  
   > *"Assigned to Agent One with the score breakdown for region, shift, availability, priority and current open workload."*
5. Point to **assignee** = `Agent One`.
6. Click **Reassign** → change to Agent Two → timeline shows "Assigned to Agent Two by Agent One".

**Key line:** *"Region, priority, shift window, availability, and load — scored and audited on every assignment."*

---

## 2:15 — Journey C: Side Conversation (Problem 3) — 55s

1. Navigate to ticket `TBO77777` (Peak Adventures, supplier issue).
2. Click **Side Conversations** tab.
3. Point to recipients: `supplier@hotelpeak.com`, `agent2@tbo.com` — **not the ticket group**.
4. Reassign the ticket to `agent1` via the **Assign** action.
5. Check **Timeline** tab → event: *"Side conversation recipients preserved after transfer"*  
   → Recipients are unchanged.
6. Add a reply to the side convo — select `External` kind → shows in thread. (Messages are persisted in OpsDesk; no external email is sent in this demo.)

**Key line:** *"Recipients are set explicitly and survive any ticket transfer — no broken supplier threads."*

---

## 3:10 — Journey D: SLA & Escalation (Problem 4) — 55s

1. Return to ticket `TBO12345` (check-in tomorrow, P2).
2. Point to **SLA chip**: 🔴 **At Risk** — SLA window was compressed from 8h to 2h because check-in is <24h away.  
   Formula: `8h × 0.25 = 2h`.
3. Click **Escalate to Escalation Manager** → select `em@tbo.com` → type reason → confirm.
4. Ticket status → `Escalated`. Assignee → `Escalation Manager`.
5. Log out → log in as **em@tbo.com / Demo@1234**.
6. Click **Escalation Queue** tab → ticket is there, SLA chip still visible.

**Key line:** *"Check-in proximity drives the SLA clock. Escalation is a first-class action — not an email trigger."*

---

## 4:05 — Journey E: Insights & Export (Problems 5 & 6) — 40s

1. Log out → log in as **lead@tbo.com / Demo@1234**.
2. Navigate to **Insights**.
3. Point to the top theme and its current count, with up to 5 sample tickets shown.  
   → *"Product teams can see recurring issues directly from ops data, without reading tickets."*
4. Navigate to **Export**.
5. Click **Export CSV** → progress counter ticks up in real time.
6. Download completes: *"X actual rows in Y seconds — no artificial 3K cap."*
7. (Optional if SEED_BULK=true) show 50K row timing.

**Key line:** *"No per-add-on API billing in this MVP, no artificial export row cap; hosting and storage remain infrastructure costs."*

---

## 4:45 — Closing (15s)

> "All of this runs on a single `docker compose up`.
> No third-party apps, no paid AI add-ons, no incremental API costs.
> The same operational complexity Zendesk charges you per add-on for —
> OpsDesk ships as one coherent vertical slice."

---

## Fallback Notes (if anything breaks)

| Issue | Fallback |
|---|---|
| Docker not running | Show `localhost:8000/docs` for API live demo |
| Seed not loaded | Run `python -m app.seed.seed` manually |
| Frontend blank | Use API docs at `/docs` to demonstrate all endpoints |
| Export slow | Pre-downloaded CSV file as backup |
