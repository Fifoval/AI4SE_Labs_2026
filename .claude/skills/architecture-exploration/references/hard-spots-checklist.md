# Hard-spots checklist

Use in Phase 1. For each category: does it apply (cite user stories)? If yes, it must be solved
explicitly in Round 1 of every architecture and probed in Round 2.

| # | Category | Cues in requirements | Questions to answer for every architecture |
|---|---|---|---|
| H1 | **Contended limited resources** (concert tickets, hotel rooms, flash-sale items, appointment slots) | "buy", "reserve", "hold", quantities, "last item", "sold out", peaks | How is double allocation prevented? Lock order for multi-item requests (deadlocks)? All-or-nothing vs. partial success? Where is the hot row and how long is it locked? When is the resource reserved (cart vs. checkout)? |
| H2 | **Money flows** | payment, checkout, refund, commission, payout, multiple sellers | Who is merchant of record? Does the platform hold third parties' money (licensing)? How is one payment split across recipients? When are recipients paid (before/after fulfilment)? Refunds, disputes, reconciliation? Sync redirect vs. webhook as source of truth? |
| H3 | **Workflows with human approval** | "accept / decline", "request", "approve" | Deadline for the human? What is reserved/charged before approval? What happens on silence? Payment validity vs. lead time? |
| H4 | **Time-driven behaviour** | expiry, deadlines, "valid until", auto-confirm, auto-cancel, reminders | Full inventory of timers: trigger, owner, action. Safe if run twice or late? Stored state vs. derived from timestamps? How is time tested? |
| H5 | **Fan-out / notifications** | subscribe, follow, notify, notification centre | N recipients × channels: rate limits, per-recipient retry, duplicates, ordering/fairness, digest, preferences/unsubscribe? |
| H6 | **Assignment / matching** | assign, claim a task, available agents/technicians, nearest free, scheduling | Two takers at once? Takes and never shows up? Nobody takes it (terminal state)? Capacity per worker? |
| H7 | **Multi-role identity & external login** | "upgrade my status", roles, OAuth, social login | Roles on one account (data model)? Stale roles in tokens? Account linking by e-mail (verified?)? Revocation? |
| H8 | **Ownership-based authorization** | "my", "owner of", "only buyers can" | Where is ownership enforced (query vs. controller)? 403 vs. 404? Purchase-based permissions? |
| H9 | **Integrations & webhooks** | payment gateway, e-mail, push, maps, external APIs | Signature verification, idempotency, retries, outages, rate limits, sandbox/local testing, vendor limits [verify]. |
| H10 | **Search & geo** | search, filter, nearby, distance, map | Full-text, geo queries, staleness tolerance, extra services needed? |
| H11 | **Realtime UX** | live, instant, status updates, chat | Durable or signal-only? Reconnect and missed events? Authorization of channels? Connection counts? |
| H12 | **Personal data & compliance** | accounts, addresses, payments, EU users | Which law applies and why? Region, processors/DPAs, erasure across all stores, records that must be kept, logs, backups. |
| H13 | **Load profile & scale** | ticket on-sale moment, flash sales, campaigns, "everyone at 9:00" | Average vs. peak, concentration on the same items, growth expectations – as explicit assumptions. |
| H14 | **Clients & API evolution** | mobile app, offline, third-party API | Old clients living for months, versioning, offline sync. |
| H15 | **Operations & back-office** | admin, support, reports | Reconciliation with external systems, admin tooling, stuck-state detection, audit trail. |

Also capture **non-functional assumptions** explicitly (scale, peaks, team size and skills, budget,
deadline, regions, compliance). Ask the user to confirm them – they decide between styles.
