# Task 1 – Architecture discussion notes (E-Farmers)

Running notes from the discussion between the student and the coding assistant.
Not a 1:1 transcript – key proposals, questions, answers and decisions.

Source requirements: [../Tasks/data/EFarmers.txt](../Tasks/data/EFarmers.txt)

**How to read these notes**
- Discussion items are numbered per architecture: **Q1–Q15** (A1 monolith), **A2.x + F1–F9**
  (A2 microservices), **A3.x + S1–S4 + L1–L6** (A3 Supabase/BaaS). Later items may refine earlier
  ones – refinements are marked *(superseded → …)* or *Correction*.
- Each architecture ends with a **Final assessment**; the overall result is in
  **[Comparison & conclusion](#comparison--conclusion)** at the end (input for Task 2 – ADR).

**Contents**
0. Requirements analysis
1. Architecture 1 – Modular monolith (Q1–Q15, final assessment)
2. Architecture 2 – Microservices, event-driven (A2.1–A2.6, F1–F9, final assessment)
3. Architecture 3 – Serverless / BaaS on Supabase (A3.1–A3.5, S1–S4, L1–L6, final assessment)
4. Comparison & conclusion (hybrid critique H1, comparison table, recommendation,
   architecture-independent decisions, open questions)

---

## 0. Requirements analysis (assistant, before proposing architectures)

### Actors / roles
- **Visitor** – unauthenticated; can register (email / OAuth) and search insertions (US 1, 8, 29).
- **User** – any logged-in account; profile, home, notifications, comments (US 2, 3, 5, 6, 30, 36).
- **Customer** – default role; cart, orders, payment, booking, subscriptions (US 14–20, 22, 27, 33, 35).
- **Farmer** – customer who upgraded; insertions, boxes, accepting bookings, badges (US 4, 9, 10, 12, 21, 28, 31).
- **Rider** – customer who upgraded; availability, deliveries, order status (US 24–26, 34).

→ Roles are **additive on one account** (a customer can become a farmer and/or a rider), not separate user types.

### Core domain concepts
| Concept | Notes |
|---|---|
| Insertion | Farmer's listing (product, description, photos). Has many Boxes. |
| Box | Sellable unit of an insertion with quantity, price, **expiry date** ("expiring boxes", US 11). |
| Seasonal calendar | Products by season; customer can **book** future boxes from it (US 7, 18). |
| Booking request | Customer books → farmer **accepts / declines** (US 21, 32). Asynchronous, human-in-the-loop. |
| Cart / Order | Classic e-commerce: cart → order → checkout via payment gateway (US 14–17, 22, 33). |
| Delivery | Optional; order is assigned to an available rider who updates its status (US 25–27, 34). |
| Subscription + Notification | Customer follows farmer → notified on new insertion; notification center (US 19, 20, 35, 36). |
| Comment, Badge | Comment only after purchase (US 23); badges as achievements (US 28). |

### Technically "painful" spots identified up front
1. **Stock consistency** – two customers buying the last box at the same time (overselling).
2. **Two purchase flows** – immediate cart/checkout vs. booking that needs farmer approval.
3. **Payment** – external gateway, webhooks, idempotency, what happens to reserved stock when payment fails.
4. **Time-driven behaviour** – boxes expire, bookings may time out → need scheduled jobs.
5. **Notification fan-out** – one new insertion → N subscribers (in-app, possibly e-mail).
6. **Rider dispatch** – choosing an available rider, order status lifecycle.
7. **Multi-role accounts + OAuth** – authorization per role on one identity.

### Non-functional assumptions (not in requirements – confirmed by student, Q3)
- Scale: regional marketplace, low thousands of users, low hundreds of farmers.
- **Seasonal peaks ~10× normal load** (strawberries, Saturday morning), everyone buying the same boxes.
- Small team (student project / startup), limited ops capacity.
- Must handle money correctly → data consistency more important than extreme scalability.

---

## Architecture 1 – Modular monolith (layered, single relational DB)

*(proposed by assistant – discussion below)*

**Idea:** one deployable backend application, internally split into modules by domain
(Identity, Catalog, Booking, Ordering, Payment, Delivery, Notification, Engagement).
One PostgreSQL database (schema per module), a background-job worker, a web frontend.

```
[Browser SPA / SSR]  ──HTTPS──▶  [Backend app (monolith)]
                                   ├─ identity      (auth, roles, OAuth)
                                   ├─ catalog       (insertions, boxes, calendar, search)
                                   ├─ booking       (requests, accept/decline)
                                   ├─ ordering      (cart, orders)
                                   ├─ payment       ──▶ Stripe (checkout + webhook)
                                   ├─ delivery      (riders, assignment, status)
                                   ├─ notification  (in-app, e-mail)
                                   └─ engagement    (subscriptions, comments, badges)
                                         │
                       [PostgreSQL]  [Job worker: expiry, emails, fan-out]  [Object storage: photos]
```

**Key mechanisms** *(initial proposal – refined in the discussion below)*
- Stock: `UPDATE box SET qty = qty - :n WHERE id = :id AND qty >= :n` inside a transaction → no
  overselling (*refined → Q1: sorted lock order, all-or-nothing*).
- Order + stock reservation in one DB transaction; reservation released by a job if unpaid after N
  minutes (*superseded → Q4/Q6: released only after the Stripe session is dead*).
- Payment: Stripe Checkout, order marked paid only by **webhook** (idempotent by event id).
- Modules talk via in-process interfaces + domain events (e.g. `InsertionPublished` → notification
  module) (*refined → Q9: transactional outbox via PG job queue*).
- Scheduled jobs: expire boxes, cancel stale bookings/reservations, award badges
  (*refined → Q11: box expiry needs no job; full timer list T1–T9*).

**Pros:** simplest to build/test/deploy; ACID transactions across cart–stock–order; cheap hosting; good fit for a small team.
**Cons:** scales as one unit; module boundaries can erode without discipline; one bad deploy takes down everything.

### Discussion log

<a id="q1"></a>
**Q1 – Atomic `UPDATE ... WHERE qty >= n` (student explained it correctly)**
- Student: under READ COMMITTED the UPDATE locks the row, a concurrent txn waits and re-evaluates
  WHERE on the new row version → 0 rows affected if stock ran out. `SELECT ... FOR UPDATE` only
  needed when a decision depends on several reads. ✔ Confirmed.
- Follow-up – **deadlock with multi-box cart** (A locks box1→box2, B locks box2→box1):
  - Real risk. A single multi-row `UPDATE` does **not** guarantee lock order in PostgreSQL.
  - **Decision:** always decrement boxes in **ascending `box_id` order** (loop of single-row UPDATEs,
    or `SELECT ... FOR UPDATE ORDER BY id` first). Consistent lock order ⇒ no cycle ⇒ no deadlock.
  - Safety net: catch SQLSTATE `40P01` (deadlock) / `40001` and retry the whole txn (max 3×).
- Follow-up – **partial success** (2 of 3 boxes available):
  - **Decision:** reservation is **all-or-nothing** in one transaction. If any UPDATE hits 0 rows →
    ROLLBACK, return the list of unavailable boxes, customer adjusts cart and retries.
  - Rejected: silently creating a partial order (surprising for the customer, complicates payment).

<a id="q2"></a>
**Q2 – Booking from the seasonal calendar**
- Student proposal: booking does not touch stock nor pre-authorize; after farmer accepts → order
  `AWAITING_PAYMENT` with 24 h deadline, otherwise expires and stock returns. Rejected Stripe manual
  capture because authorization holds ~7 days while bookings can be weeks ahead. ✔ Reasoning correct
  (extended authorizations up to ~30 days exist only for specific merchant categories – not us).
- Assistant counter-proposal (improvement, not a rejection):
  - At booking time create a Stripe **SetupIntent** → save the customer's card with consent for an
    off-session charge. No money held, no expiry problem.
  - On farmer acceptance → charge **off-session** (PaymentIntent with saved method).
  - If the bank requires SCA/3DS (off-session charge fails with `authentication_required`) →
    **fall back to the student's flow**: order `AWAITING_PAYMENT` + payment link, 24 h deadline.
  - Benefit: fewer no-shows, the happy path needs no further customer action.
- Added: farmer must answer the booking within a deadline (e.g. 48 h), otherwise auto-decline
  (scheduled job) – so the customer is never stuck in `PENDING`.
- **Decision:** hybrid = SetupIntent at booking + off-session charge on accept + student's 24 h
  payment-link flow as fallback.

<a id="q3"></a>
**Q3 – Seasonal peaks (10× load, everyone buys the same boxes)**
- Absolute numbers stay small (10× of low thousands of users ≈ tens–low hundreds of req/s) →
  a stateless monolith with 2–3 replicas behind a load balancer handles it.
- The real bottleneck is the **hot row**: all purchases of the same box serialize on one row lock.
  Throughput then depends purely on how long the transaction holds the lock.
- Rules that follow:
  - **Never call Stripe (or any network I/O) inside the stock transaction** – txn must be ms-short.
  - Reserve stock at "go to checkout", not at "add to cart" (cart is just a wish list).
  - Connection pooling (PgBouncer); catalog/search reads cached (read-heavy, tolerant to staleness);
    photos via CDN / object storage.
- Only if it ever got far worse: queue-based checkout or splitting stock of one box into N buckets.
  Not needed at this scale – noted as an escape hatch.

<a id="q4"></a>
**Q4 – Reconciling reservation TTL with Stripe Checkout session expiry**
- Fact: Checkout Session `expires_at` must be between **30 min and 24 h** from creation.
- Race: our job releases stock → someone else buys it → original customer pays on the still-open session.
- **Decision (three layers):**
  1. One timer, not two: set `expires_at` = reservation TTL (30 min).
  2. Release stock **only after the session is dead**: on the `checkout.session.expired` webhook, or
     the job first calls Stripe "expire session"; if Stripe says the session is already completed,
     do **not** release.
  3. *(superseded → Q6: manual capture dropped)* Use `capture_method=manual` in Checkout: payment is only authorized. On
     `checkout.session.completed` → if reservation still valid → **capture**; if not → try to
     re-reserve → capture, else **cancel the authorization** (money never actually moves, no refund
     fees, no angry customer with a charged card and no goods).
  - Note: here manual capture is fine – we capture within minutes, unlike the booking case in Q2.

<a id="q5"></a>
**Q5 – Marketplace money flow (cart with boxes from 3 farmers)**
- Option A – platform collects everything and pays farmers itself: platform holds third parties'
  money → in the EU this falls under payment services (PSD2), possibly needs a licence + AML/KYC
  obligations. **Rejected** for a small team.
- Option B – **Stripe Connect** (farmers and riders as *Express* connected accounts; Stripe does
  KYC, onboarding and payouts under its own licence).
  - Charge type: **separate charges and transfers** – one charge to the customer, then one Transfer
    per farmer (linked by `transfer_group`), platform keeps its commission; rider gets a transfer for
    the delivery fee.
  - *Destination charges* rejected: one charge → only one destination, does not fit a multi-farmer cart.
- Implementation consequences:
  - Data model: `Order` → `FarmerOrder` (sub-order per farmer) → `OrderItem`. Fulfilment,
    acceptance, refunds and transfers all work per `FarmerOrder`.
  - Farmer cannot publish sellable insertions until Connect onboarding is complete
    (`charges_enabled` / `payouts_enabled`) → affects US 12 "upgrade to Farmer".
  - Refund of one farmer's part = partial refund + **transfer reversal** for that farmer.
  - Platform remains liable for disputes/chargebacks → needs a policy.
  - Invoicing/VAT: who is the seller (farmer) vs. platform service (commission) – must be confirmed
    with an accountant/lawyer. *Assistant's statements here are not legal advice.*
- **Decision:** Stripe Connect Express + separate charges and transfers.

<a id="delivery-model"></a>
**Delivery model (student proposal – accepted with additions)**
- Student: one `Delivery` per `FarmerOrder` (one pickup, one drop-off). Farmers prepare independently,
  one late farmer does not block others, no route planning needed. Price = distance farm → customer.
  Dispatch = offer to all available riders in a radius, first to accept wins via
  `UPDATE delivery SET rider_id = ? WHERE id = ? AND rider_id IS NULL`. Downside accepted: 3 farmers
  = 3 delivery fees; bundling postponed.
- Assistant agrees; additions:
  - **Rider who accepts and never comes**: states `OFFERED → ASSIGNED → PICKED_UP → DELIVERED`;
    if not `PICKED_UP` within X min after the farmer marks "ready" → reset `rider_id = NULL`, re-offer.
  - **Nobody accepts**: after T min widen radius; after a further T → tell customer, offer self-pickup
    or refund the delivery fee. Dispatch must have a terminal state, not hang forever.
  - **One rider, many deliveries?** Decide explicitly. If max 1 active: partial unique index
    `ON delivery(rider_id) WHERE status IN ('ASSIGNED','PICKED_UP')` – DB enforces it, same atomic style.
  - **Distance**: start with haversine × correction factor (≈1.3) instead of a paid routing API;
    requires geocoded farm and customer addresses (geocode once on save).
  - UX: per-farmer delivery fee shown in the cart *before* checkout; customer may choose self-pickup
    per `FarmerOrder` (mixing allowed).

<a id="q6"></a>
**Q6 – Is manual capture needed at all? (student challenged layer 3 – student is right)**
- With layers 1+2 (one timer, release only after the session is dead) Stripe guarantees that an
  expired session cannot be completed, and "expire session" fails on an already-completed session →
  the "paid after release" race **cannot happen** for synchronous methods.
- **Decision: drop manual capture** (needless complexity, not supported by all payment methods).
  Keep only a defensive handler: `completed` webhook for an order whose reservation is gone
  (bug / manual intervention) → try re-reserve, else automatic refund + alert to ops.
- **Async methods (SEPA Direct Debit etc.)**: Checkout completes with `payment_status = unpaid`,
  result comes days later (`checkout.session.async_payment_succeeded/failed`).
  - Holding perishable stock for days is unacceptable (boxes expire); confirming optimistically
    means shipping before money is certain (and SEPA can be disputed for 8 weeks).
  - **Decision:** immediate purchases (cart → checkout) allow **only instantly confirmed methods**
    (cards, wallets). **SEPA Direct Debit only for calendar bookings** – it fits the SetupIntent /
    mandate flow from Q2 because the harvest date is weeks away and there is time for processing.

<a id="q7"></a>
**Q7 – When do transfers to farmer and rider happen?**
- Immediately after payment → farmer paid for undelivered goods → reversal; with Express accounts
  the platform is liable for the farmer's negative balance. Rejected.
- Long holding on the platform balance → we drift back towards "safekeeping third-party funds"
  (regulatory concern from Q5) and Stripe limits how long/how separate charges and transfers may be
  delayed. Must stay short (days).
- **Decision: pay each party when *their* part is done:**
  - **Farmer** → transfer when the box is handed over (`PICKED_UP` by rider, or picked up by the
    customer). A failed delivery afterwards is not the farmer's fault.
  - **Rider** → transfer on `DELIVERED`.
  - Transfers use `source_transaction` (linked to the original charge, works even while funds are
    pending) + `transfer_group` = order id.
- Trust issue of US 34 (rider marks "delivered" himself): customer can confirm or complain within
  24 h, otherwise auto-confirm. Complaint → refund + transfer reversal from the rider.

<a id="q8"></a>
**Q8 – Module boundaries: who owns `box`?**
- **Catalog owns `box` and its quantity.** Ordering never writes to it; it calls catalog's public API:
  `catalog.api.reserve_stock(items, reservation_ref, uow)` / `release_stock(reservation_ref, uow)`.
  The sorted-UPDATE logic from Q1 lives *inside* catalog.
- Atomicity with order creation: in a monolith the module API may participate in the **caller's
  transaction** (unit of work passed in). Pragmatic compromise – documented as a deliberate coupling;
  a future service split would turn it into a saga (→ Architecture 2).
- Enforcement:
  - **DB**: one PostgreSQL schema per module (`catalog.*`, `ordering.*`, …). No cross-schema
    foreign keys; `order_item` stores `box_id` + **snapshot of name and price at purchase time**
    (needed anyway for order history, US 22).
  - **Code**: each module = package with a public `api` and private `internal`. Only `api` may be
    imported by other modules.
  - **CI**: architecture tests – `import-linter` contracts (Python) / ArchUnit (Java) /
    dependency-cruiser (TS) fail the build on a forbidden import. Optional SQL check: queries in
    `ordering/` must not reference the `catalog.` schema.
  - Optional stricter variant: separate DB role per module with `GRANT`s only on its own schema –
    rejected for now (complicates connection pooling).

<a id="q9"></a>
**Q9 – `InsertionPublished`: in-process or queue? Transactional outbox**
- Synchronous in-process dispatch → either runs inside the request txn (slow fan-out, failure of
  notifications rolls back the insertion) or after commit (crash between commit and enqueue →
  event **lost**). Neither acceptable.
- **Transactional outbox**: event row written in the **same transaction** as the business change;
  a relay worker delivers it afterwards. Commit ⇒ event guaranteed to exist.
  ```sql
  CREATE TABLE outbox (
    id           bigserial PRIMARY KEY,
    event_id     uuid NOT NULL UNIQUE,
    type         text NOT NULL,           -- 'InsertionPublished'
    payload      jsonb NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz
  );
  CREATE INDEX outbox_pending ON outbox (id) WHERE processed_at IS NULL;
  ```
  ```python
  # catalog: publish insertion
  with uow.transaction():
      insertion = repo.insert(...)
      outbox.add("InsertionPublished", {"insertion_id": insertion.id, "farmer_id": farmer_id})

  # relay worker (can run as N instances)
  rows = SELECT * FROM outbox WHERE processed_at IS NULL
         ORDER BY id LIMIT 100 FOR UPDATE SKIP LOCKED
  for row in rows:
      dispatch(row)                        # call subscribed handlers / enqueue jobs
      UPDATE outbox SET processed_at = now() WHERE id = row.id

  # notification handler – must be idempotent (at-least-once delivery)
  INSERT INTO notification.notification (event_id, user_id, ...)
  SELECT :event_id, s.customer_id, ...
  FROM engagement.subscription s WHERE s.farmer_id = :farmer_id   -- via engagement API in real code
  ON CONFLICT (event_id, user_id) DO NOTHING;
  ```
  - Delivery semantics: **at-least-once** (crash after dispatch, before `processed_at`) → every
    handler idempotent (unique `(event_id, user_id)`).
  - Fan-out: one set-based INSERT for in-app notifications; e-mails sent by a separate job in batches.
- **Simplification adopted:** use a **PostgreSQL-backed job queue** (Procrastinate / pg-boss /
  Oban / Solid Queue, depending on language). Enqueuing the job in the same transaction *is* the
  outbox – no separate relay needed. Separate outbox table only if we later publish to an external
  broker (Architecture 2).

<a id="q10"></a>
**Q10 – Concurrent deliveries per rider**
- **MVP decision (student): max 1 active delivery** → partial unique index is enough.
- If later max 3: unique index can't count. Options considered:
  - `SELECT ... FROM rider_profile WHERE user_id = ? FOR UPDATE`, then count, then assign –
    correct (serializes per rider), but read-then-write logic spread in code.
  - `SERIALIZABLE` – correct, but every txn on these tables needs a retry loop and gets false-positive
    serialization failures. Overkill for one invariant. Rejected.
  - **Chosen: counter column + same atomic pattern as stock:**
    `active_deliveries int NOT NULL DEFAULT 0 CHECK (active_deliveries BETWEEN 0 AND 3)`;
    assignment txn = `UPDATE rider_profile SET active_deliveries = active_deliveries + 1
    WHERE user_id = ? AND active_deliveries < 3` (0 rows → refuse) + delivery UPDATE;
    decrement in the same txn as `DELIVERED` / cancel. Nightly reconciliation job compares the
    counter with `COUNT(*)` of active deliveries (guards against drift from bugs).

<a id="q11"></a>
**Q11 – All time-driven behaviour and how to run it exactly-once-in-effect**

| # | Trigger | Deadline | Action |
|---|---|---|---|
| T1 | Stock reservation (checkout) | 30 min | expire Checkout session → release stock (primary trigger = `checkout.session.expired` webhook, job is fallback) |
| T2 | Booking waiting for farmer | 48 h | auto-decline, notify customer |
| T3 | Accepted booking `AWAITING_PAYMENT` (SCA fallback) | 24 h | expire order, release capacity |
| T4 | Delivery offered, nobody accepts | T min | widen radius |
| T5 | Delivery still unassigned after widening | T2 min | give up → offer self-pickup / refund delivery fee |
| T6 | Rider assigned, not `PICKED_UP` | X min after farmer "ready" | unassign, re-offer |
| T7 | `DELIVERED`, customer silent | 24 h | auto-confirm → rider transfer |
| T8 | Badges | periodic / on event | evaluate achievements |
| T9 | Reconciliation | nightly | Stripe vs DB, rider counters |
| T10 | Notification e-mails | event-driven (not a timer) | see Q14 |

- **Two kinds of jobs:**
  - **Per-entity deadlines (T1–T7)** → a **delayed job** (`run_at = deadline`) enqueued in the same
    txn that creates the entity (PG job queue = outbox, Q9). No polling.
  - **Periodic sweeps (T8, T9 + safety-net sweep for T1–T7)** → periodic tasks of the job library,
    which dedupes runs (unique job key per period / `pg_advisory_lock`) → runs once even with 2 instances.
- **The real guarantee is not "the job runs once" but "running it twice is harmless":** every job is a
  **conditional state transition**, e.g.
  `UPDATE booking SET status='DECLINED' WHERE id=? AND status='PENDING' AND respond_by <= now()`.
  Second run / late run after the farmer already accepted → 0 rows → no-op.
- **Expiring boxes (US 11) need no job.** "Expired" is derived, not stored:
  - sellable = `expires_at > now()`; "expiring soon" = `expires_at BETWEEN now() AND now() + interval '48 h'`
    (index on `expires_at`).
  - A job only if we want to *notify* (e.g. farmer "your box expires tomorrow") – optional.
- **Expired box in a cart:** cart is only a wish list → shown greyed out as unavailable.
  `reserve_stock` UPDATE also has `AND expires_at > now() + interval '<reservation TTL>'` → cannot buy a
  box that would expire during checkout. `expires_at` defined as **last sellable moment** (farmer sets it).

<a id="q12"></a>
**Q12 – Roles, payouts and authorization**
- DB model: every `user` is a customer; extra roles = **1:1 profile tables** (different data per role,
  not an enum/array):
  - `farmer_profile(user_id PK/FK, farm_name, address, geo, ...)`
  - `rider_profile(user_id PK/FK, availability, geo, active_deliveries, ...)`
  - `payout_account(user_id PK/FK, stripe_account_id, charges_enabled, payouts_enabled)` – **one
    connected account per person**, shared if the person is both farmer and rider.
- **Yes, rider needs Connect onboarding** too (receives transfers). Rider can switch to "available"
  (US 26) only with `payouts_enabled`; farmer can publish sellable boxes only with it (Q5).
- **Authorization in two layers:**
  1. Route/middleware: coarse role check ("has `farmer_profile`").
  2. **Ownership inside the module's domain service, enforced in the query itself:**
     `UPDATE catalog.insertion SET ... WHERE id = ? AND farmer_id = :actor` – 0 rows → 404
     (404 rather than 403 → does not reveal that the insertion exists). Same for delete (US 9),
     edit (US 10), adding boxes (US 31: insert box only if the insertion belongs to the actor).
     Never trust a check done only in the controller/frontend.
- **Comments (US 23):** comment is tied to a purchase: `comment(farmer_order_id UNIQUE, author_id, ...)`.
  Engagement calls `ordering.api.get_completed_farmer_order(farmer_order_id, customer_id)`;
  allowed only for the buyer and only after `PICKED_UP`/`DELIVERED`. UNIQUE → one comment per purchase.
- PostgreSQL Row-Level Security considered as a second net – not now (hard to combine with
  connection pooling and a single app role).

<a id="q13"></a>
**Q13 – E-mail + OAuth with the same address (account linking)**
- Identity model: `user` + `user_identity(provider, provider_subject, user_id)`,
  `UNIQUE(provider, provider_subject)`. Key by provider `sub`, **not by e-mail** (e-mails change).
- **Automatic linking only if both sides are verified:** provider returns `email_verified = true`
  (Google does) **and** our local account's e-mail is verified.
- **Pre-account-takeover attack:** attacker registers victim@gmail.com with a password (unverified),
  victim later logs in with Google → if we auto-link, attacker's password still works. Mitigation:
  e-mail registration requires verification; if an *unverified* local account meets a verified
  OAuth login → the OAuth identity wins, local password and sessions are invalidated.
- Provider without verified e-mail → **never auto-link**; user must log in with password and link the
  provider manually in settings.
- Use a proven library (django-allauth / Auth.js / Spring Security OAuth2 client …), do not hand-roll
  the OAuth flow.

<a id="q14"></a>
**Q14 – E-mail / push fan-out (5 000 external calls)**
- Model: `notification` (in-app, from Q9) + `notification_delivery(notification_id, channel, status,
  attempts, next_attempt_at, provider_message_id)`, `UNIQUE(notification_id, channel)` → one delivery
  per recipient per channel. Respect user preferences / unsubscribe (link in every e-mail; consent).
- **Rate limits:** dedicated `email` queue with limited concurrency + token bucket matching the
  provider limit; use the e-mail provider's **batch API** where it exists (many recipients per call).
  - **Correction (student pointed it out, verified):** FCM has **no real batch endpoint** any more –
    the legacy batch endpoint was shut down in June 2024. Admin SDK `sendEach` /
    `sendEachForMulticast` (max 500 tokens) sends **one HTTP v1 request per message** under the hood
    (over HTTP/2 multiplexing, concurrently). So push = N requests; rate limiting + per-recipient
    retry still apply exactly as for e-mail.
  - Alternative for push: **FCM topics** (topic `farmer_<id>`, subscribed when the customer follows
    the farmer) → one request, FCM fans out. Trade-off: no per-recipient delivery tracking and
    preferences must be reflected by (un)subscribing tokens to topics. Possible later optimisation.
- **Retry per recipient:** each delivery row retried independently, exponential backoff on 429/5xx;
  permanent errors (hard bounce, invalid token) → `FAILED`, no retry.
- **No double e-mails:** exactly-once over the network is impossible. Steps: `PENDING → SENDING → SENT`;
  provider **idempotency key = delivery id** where supported → provider deduplicates retries. Without
  it, a crash between the call and `SENT` may cause a rare duplicate – **at-least-once chosen
  deliberately** (a duplicate is better than a lost notification).
- Volume reduction: **digest** – several new insertions from followed farmers within a window →
  one e-mail per user.

<a id="q15"></a>
**Q15 – Deployed processes (Architecture 1)**
| Process | Instances | Role |
|---|---|---|
| `web` | 2–3, stateless | HTTP API + frontend, Stripe webhooks, OAuth callbacks |
| `worker` | 1–2 | job queue consumers (`default`, `email`, `payments` queues) |
| `scheduler` | 1 (or embedded in worker with lock) | periodic tasks T8, T9, safety-net sweeps |
| PostgreSQL (managed) + PgBouncer | 1 primary (+ replica later) | all data, job queue |
| Object storage + CDN | managed | photos |
| External | – | Stripe (Connect), e-mail provider, push (FCM), OAuth, geocoding |

→ **one codebase, three entrypoints**, one database.

**Open questions after Architecture 1**
- (resolved) Delivery per `FarmerOrder`; (resolved) max 1 active delivery per rider in MVP.

<a id="a1-final"></a>
### Architecture 1 – Final assessment (after the whole discussion)

**Strengths**
- ACID transactions across cart → stock → order; overselling and rider over-assignment solved with
  simple, provable atomic UPDATEs (Q1, Q10).
- Outbox for free via PostgreSQL job queue (Q9); delayed jobs + conditional transitions make all
  timers safe on multiple instances (Q11).
- Small operational footprint: 3 process types, 1 DB, managed services (Q15).
- Handles the expected load including 10× seasonal peaks; bottleneck (hot row) understood (Q3).
- Fast to develop for a small team; refactoring across modules is cheap (one repo, one deploy).

**Weaknesses**
- Scales only as a whole; a slow feature (e.g. e-mail fan-out) competes for the same DB.
- One deploy for everything – a bad release of a minor feature can break checkout.
- Module boundaries rely on discipline + CI rules; the shared transaction in `reserve_stock` is a
  deliberate coupling (Q8).

**Risks / what will hurt after one year (small team)**
1. **Money edge cases & support** – refunds, partial refunds, transfer reversals, disputes,
   SCA fallbacks, Stripe ↔ DB mismatches. Highest support load; needs reconciliation (T9) and an
   admin/back-office UI from day one.
2. **State-machine zoo** – orders, bookings, deliveries, payments each with timers (T1–T7). "Stuck"
   entities are hard to debug → need state history tables, observability, fake clock in tests.
3. **Database as the single heart** – job/outbox/notification tables bloat (vacuum, retention policy),
   schema migrations on big tables during the season must be lock-safe.
4. **Boundary erosion** – shortcuts under deadline pressure ("just one join into catalog").
5. **Third-party dependencies** – Stripe/e-mail/OAuth outages must degrade gracefully
   (e.g. checkout disabled with a clear message, notifications retried later).

---

## Architecture 2 – Microservices with event-driven communication

*(proposed by assistant – big picture first, failure scenarios in the next round)*

<a id="a2-1"></a>
### A2.1 Services and data ownership
Derived from the monolith modules. Rule: a service boundary = **a consistency boundary + a reason to
change independently**. Everything that must change atomically stays inside one service.

| Service | Owns (own database) | Monolith modules | Why this boundary |
|---|---|---|---|
| **Identity** (off-the-shelf IdP, e.g. Keycloak) | accounts, credentials, OAuth identities, role grants | identity | Security-critical, standard problem – buy, don't build. Q13 linking rules configured there. |
| **Catalog** | insertions, boxes, **stock + reservations**, seasonal calendar, farmer storefront (public farmer page), search | catalog | Owner of stock invariant (Q1). Read-heavy, scales differently from checkout. |
| **Ordering** | cart, orders, `FarmerOrder`, order items (price snapshots), **bookings**, **checkout saga state** | ordering + booking | Booking acceptance creates an order (Q2) – too coupled to split. Orchestrates checkout. |
| **Payment** | Checkout sessions, payments, refunds, Connect `payout_account`, transfers, Stripe event log | payment | Only service talking to Stripe; money logic, secrets, audit; changes for regulatory reasons. |
| **Delivery** | rider profiles, availability, `active_deliveries`, deliveries + state machine, geo | delivery | Own state machine and timers (T4–T7), geo queries, real-time-ish behaviour. |
| **Notification** | notifications, `notification_delivery`, preferences, device tokens | notification | Pure consumer of events; fan-out load isolated from checkout (A1 weakness). |
| **Community** | subscriptions, comments, badges | engagement | Each part too small for its own service → merged. |

- **Kept together deliberately:** cart + orders + bookings (Ordering); subscriptions + comments +
  badges (Community); search stays in Catalog (Postgres FTS is enough – no separate search service).
- Considered and rejected: subscriptions inside Notification (it is a user-facing feature, US 20, 35,
  not a delivery concern) – Notification gets subscriber lists via events / Community API.
- Plus infrastructure: **API gateway / BFF** (single entry for the frontend, JWT validation,
  composition of pages), broker, one Postgres cluster with **separate database per service**
  (logically isolated, cheap to run).
- Honest note: **6 services + IdP for a small team** – the main cost of this architecture.

<a id="a2-2"></a>
### A2.2 Broker
- Volume: hundreds to low thousands of events per hour (10× at peaks) – tiny.
- **Kafka rejected:** its strengths (huge throughput, retained log, replay, partition ordering) are
  not needed; operational cost (cluster, partitions, consumer groups, schema registry) high for a
  small team.
- **Chosen: RabbitMQ** (or managed equivalent – AWS SNS+SQS / Google Pub/Sub – if we are on a cloud;
  zero ops is even better): topic exchanges for events, per-message ack, dead-letter queues,
  simple model.
- Consequences regardless of broker:
  - **At-least-once delivery** → every consumer idempotent: **inbox table** `processed_event(event_id PK)`
    inserted in the same txn as the handler's changes.
  - **Transactional outbox becomes mandatory** in every producing service (Q9 – no longer optional);
    relay publishes from outbox to the broker.
  - **No global ordering** with competing consumers → handlers must tolerate out-of-order events
    (state machines accept only valid transitions; events carry entity `version`).

<a id="a2-3"></a>
### A2.3 Communication rule – sync vs. events
- **Synchronous (REST/gRPC)**: a user is waiting AND needs an authoritative answer now, read-only or a
  command with an immediate result. Max **one hop** – no sync chains (A→B→C).
- **Events**: facts other services react to ("BoxUpdated", "OrderPaid", "DeliveryPickedUp").
  Producer does not know or wait for consumers.
- **Commands via broker**: steps of the checkout saga (A2.4) – async, with replies as events.
- **Cart needs price & availability of boxes:**
  - Option A – cart calls Catalog synchronously (batch `GET /boxes?ids=…`) on every render. Simple,
    always fresh, but cart page is down when Catalog is down; temporal coupling.
  - Option B – **Ordering keeps a local read model** `box_view(box_id, name, price, farmer_id,
    expires_at, available, version)`, updated from Catalog events (`BoxPublished`, `BoxUpdated`,
    `StockLevelChanged`, `BoxDeleted`). Cart works even if Catalog is down; data may be seconds stale.
  - **Chosen: B.** Staleness is harmless because the cart is only a wish list (Q11) – the
    **authoritative** price and stock come from Catalog in the reservation step of the saga. If the
    price changed, the customer sees the new total before paying.

<a id="a2-4"></a>
### A2.4 Checkout saga – orchestrated by Ordering
- **Orchestration chosen over choreography:** 5 steps, branching, compensations, a timer. With
  choreography the flow would be spread over 4 services' event handlers and nobody would know the
  current state of a checkout. Orchestrator = `CheckoutSaga` table in Ordering with explicit state.

| Step | Who | Action | Failure → compensation | What the monolith gave us for free |
|---|---|---|---|---|
| S1 | Ordering | create `Order(PENDING)` + `FarmerOrder`s, outbox command `ReserveStock` | – (nothing done yet) | order and stock in **one transaction**; here an order exists *before* stock is known → must be hidden from the customer's history until confirmed |
| S2 | Catalog | `ReserveStock(order_id, items)` – local all-or-nothing txn, sorted UPDATEs (Q1), reservation keyed by `order_id` (idempotent) → `StockReserved{prices}` / `StockReservationFailed{unavailable}` | failed → Ordering marks order `REJECTED`, shows unavailable boxes | **read-your-writes**: in A1 the request knew the result instantly; now the browser waits for an async reply |
| S3 | Payment | `CreateCheckoutSession(order_id, per-FarmerOrder amounts, expires_at = 30 min)`, Stripe idempotency key = `order_id` → `CheckoutSessionCreated{url}` | Stripe error → command `ReleaseStock` to Catalog + order `FAILED` | **network call outside txn was trivial** in A1; now a third service must succeed. Customer waits for the redirect URL → frontend polls/WebSocket on saga state (UX cost) |
| S4 | Customer + Stripe → Payment | webhook `checkout.session.completed` → `PaymentSucceeded`; `checkout.session.expired` → `PaymentExpired` | expired → `ReleaseStock` + order `CANCELLED` | **one timer, one place** (Q6): now session expiry lives in Payment, stock in Catalog → Catalog reservations must **not** have their own short TTL (only a long safety TTL, e.g. 24 h + alert), released only by command |
| S5 | Ordering | order `PAID` → event `OrderPaid` → Catalog converts reservation to sold, Delivery creates deliveries, Notification informs farmers | **after payment = pivot point: no backward compensation**, only forward retry. If Catalog finds no reservation (bug) → `ReservationMissing` → Ordering → Payment **refund** | final state reached in **one commit**; now several services reach it eventually, each must be retried until success |

- Payment is the **single place that resolves the Stripe race** (completed vs. expired): conditional
  update on its session row emits exactly one terminal event per session.

<a id="a2-5"></a>
### A2.5 Where the monolith's solutions moved
| Item | Owner service | Notes |
|---|---|---|
| T1 reservation / session expiry | **Payment** | Stripe concept; emits `PaymentExpired` → saga compensates. Catalog only safety TTL. |
| T2 farmer booking response, T3 booking payment deadline | **Ordering** | bookings live there; T3 off-session charge requested via command to Payment |
| T4–T7 dispatch, radius, pickup timeout, auto-confirm | **Delivery** | |
| T8 badges | **Community** | reacts to events (`OrderCompleted`, `CommentAdded`) |
| T9 reconciliation | **Payment** (Stripe ↔ DB), **Delivery** (rider counters) + new cross-service check: `OrderPaid` without deliveries / transfers |
| Stripe webhooks (payments **and** Connect `account.updated`) | **Payment only** – single endpoint, translated into domain events (`PaymentSucceeded`, `PayoutAccountEnabled`). No other service knows Stripe. |
| Transfers to farmer / rider | **Payment**, driven by events: `DeliveryPickedUp(farmer_order_id)` or `FarmerOrderHandedOver` (self-pickup, from Ordering) → farmer transfer; `DeliveryCompleted(rider_id)` (after confirm/auto-confirm T7) → rider transfer. Amounts per `FarmerOrder` stored in Payment at S3; recipient account looked up in its own `payout_account`. Stripe idempotency key = `farmer_order_id + transfer type`. Out-of-order tolerant: `DeliveryCompleted` before `PickedUp` ⇒ pay both. |
| Onboarding gate (Q5, Q12) | `PayoutAccountEnabled` event → Catalog stores flag (farmer may publish), Delivery stores flag (rider may go available) |

<a id="a2-6"></a>
### A2.6 Identity and roles across services
- IdP issues **short-lived JWT access tokens** (5–15 min) with `sub` + roles; refresh token for renewal.
- Gateway validates the JWT; **each service validates the signature locally** (JWKS, cached) → no call
  to Identity per request. Services still do **ownership checks themselves** (Q12) using their own data.
- **Customer → farmer (US 12), token still says "customer":**
  - Upgrade is an *escalation* – stale token only means the new privilege is missing for a while.
    Fix: after the upgrade succeeds, the frontend **immediately refreshes the token** → new roles
    within one request. Other sessions of the user get it at the next refresh (≤15 min) – acceptable.
  - Upgrade is a **process**, not a flag: Identity grants role → `RoleGranted(farmer)` event →
    Catalog creates farmer record `PENDING_ONBOARDING` → Payment starts Connect onboarding →
    `PayoutAccountEnabled` → Catalog sets farmer `ACTIVE`. The token role alone never allows publishing.
- **Dangerous direction = revocation** (farmer suspended, rider banned): token still has the role up to
  15 min → services that matter check **authoritative local state** (Catalog: `farmer.status = ACTIVE`,
  Delivery: `rider.status = ACTIVE`, kept current via `RoleRevoked` / `FarmerSuspended` events).
  Token roles = coarse filter, local state = decision.

### Discussion log – failure scenarios

<a id="f1"></a>
**F1 – Compensation overtakes the action (`ReleaseStock` processed before a late `ReserveStock`)**
- Real problem: broker gives no ordering guarantee between two different commands, and a slow
  consumer can process `ReserveStock` after the orchestrator already gave up.
- **Fix: Catalog remembers releases – tombstones.** Reservation row keyed by `order_id` is a small
  state machine: `(none) → RESERVED → SOLD | RELEASED` and also `(none) → RELEASED` (tombstone).
  - **Correction (student found two bugs in the first version):** (a) `ON CONFLICT DO NOTHING`
    returning 0 rows does **not** mean "released" – the existing row can be `RESERVED`/`SOLD`
    (duplicate command) or `REJECTED`; each must be answered differently. (b) `RESERVED → RELEASED`
    must **return the quantities to `box.qty` in the same transaction** – the first version did not.
  - Statuses: `RESERVED | REJECTED | RELEASED | SOLD`; quantities kept in `reservation_item(order_id, box_id, qty)`.
  ```sql
  -- ReserveStock(order_id, items) – ONE transaction
  INSERT INTO reservation (order_id, status) VALUES (:id, 'RESERVED')
  ON CONFLICT (order_id) DO NOTHING RETURNING order_id;
  -- 0 rows → row already exists, answer by its status, NO stock change:
  --   RESERVED / SOLD → duplicate command → re-send the original StockReserved reply
  --   REJECTED        → re-send StockReservationFailed
  --   RELEASED        → tombstone (order cancelled first) → StockReservationFailed{reason: 'cancelled'}
  -- 1 row → claim succeeded:
  SAVEPOINT claimed;
  --   for each item ORDER BY box_id (lock order, Q1):
  UPDATE box SET qty = qty - :n WHERE id = :box_id AND qty >= :n AND expires_at > now() + :ttl;
  INSERT INTO reservation_item (order_id, box_id, qty) VALUES (:id, :box_id, :n);
  --   any UPDATE hit 0 rows → ROLLBACK TO SAVEPOINT claimed;
  --                           UPDATE reservation SET status = 'REJECTED' WHERE order_id = :id;
  --                           (outcome stored → duplicates get the same answer)
  -- + inbox row + outbox reply, COMMIT

  -- ReleaseStock(order_id) – ONE transaction
  INSERT INTO reservation (order_id, status) VALUES (:id, 'RELEASED') ON CONFLICT (order_id) DO NOTHING;
  -- 1 row → tombstone created (Reserve not processed yet) → nothing to return, done
  -- 0 rows → reservation exists:
  UPDATE reservation SET status = 'RELEASED' WHERE order_id = :id AND status = 'RESERVED';
  -- 1 row → return stock, per box ORDER BY box_id (same lock order as reserve → no deadlock):
  UPDATE box SET qty = qty + ri.qty FROM reservation_item ri
   WHERE ri.order_id = :id AND ri.box_id = :box_id AND box.id = ri.box_id;
  -- 0 rows → already RELEASED / REJECTED (no-op) or SOLD (release after payment = bug → no-op + alert)
  ```
  - Concurrent Reserve and Release for the same `order_id`: the unique index makes the second INSERT
    wait for the first txn to commit, then `ON CONFLICT` sees the row → serialized per order.
  - Tombstone retention must exceed the maximum possible message delay (incl. DLQ, see F3) →
    keep 14 days, then prune.
- Second line of defence in the orchestrator: a `StockReserved` reply for a saga that is already
  `CANCELLED` → send `ReleaseStock` again (idempotent).
- Same issue in S3: orchestrator gives up, Payment creates the session later. Fix: `CancelCheckout(order_id)`
  tombstone in Payment; a session created after it is expired immediately. Customer can't pay anyway –
  the URL was never delivered.
- **Step timeouts – guarded by Ordering** with delayed jobs in its own DB (same mechanism as Q11),
  saga row has `step` + `step_deadline`, every timeout = conditional transition:

| Step | Timeout | On timeout |
|---|---|---|
| S2 reserve stock | 10–15 s (customer is waiting) | saga `CANCELLED`, `ReleaseStock` (tombstone), customer: "try again" |
| S3 create Stripe session | 15 s | `CancelCheckout` + `ReleaseStock`, customer: "try again" |
| S4 payment | **no own cancel timer** – only Payment decides (Stripe expiry 30 min + webhook). Safety: at 45 min Ordering sends `ResolveSession` → Payment asks Stripe and emits the terminal event | never cancel on our own clock – that is the money race from Q6 |
| S5 post-payment | no cancel (pivot passed) | retries; alert if not all confirmations within 10 min |

<a id="f2"></a>
**F2 – Safety TTL, alerts, orchestrator crash**
- **24 h is wrong for perishable goods.** New rule: `hold_until = session expires_at + 30 min`
  (≈ 1 h after checkout start), and never beyond `box.expires_at`.
  - Why it is safe enough: Stripe cannot complete a session after `expires_at`; the only risk is a
    payment completed in time whose event is delayed > 30 min by an outage. Then `OrderPaid` arrives,
    Catalog tries to re-reserve, otherwise `ReservationMissing` → **refund** (path from S5 exists).
  - Trade-off chosen consciously: **rare refund during an outage** vs. **boxes blocked for a day**.
  - Every safety-net release emits `ReservationExpiredBySafetyNet` → metric + alert.
- **Alerts → on-call developer** (small team: one Slack/PagerDuty channel, weekly rotation). Triggers:
  DLQ depth > 0; outbox lag (oldest unpublished row > 1 min); saga in non-terminal state past its
  deadline; any safety-net release; reconciliation mismatch.
- **Runbook:** check broker / failing service health → after recovery the outbox relays publish the
  backlog automatically, delayed jobs fire overdue → nothing manual in the normal case. Manual work
  only for DLQ (F3) and reconciliation mismatches (refund / re-transfer via admin tool).
- **Ordering crashes mid-saga:** nothing is in memory.
  - Every saga transition = one local txn: update saga row + insert outbox command (+ schedule timeout job).
  - Restart → outbox relay publishes what was not sent yet; replies are waiting in **durable queues**
    (persistent messages) and are consumed now; overdue timeout jobs fire immediately.
  - Inbox dedup makes re-consumed replies harmless. Orchestrator = stateless code over a persistent
    state machine.

<a id="f3"></a>
**F3 – Inbox, ACK ordering, poison messages / DLQ**
- **Yes, `processed_event` is inserted in the same DB transaction as the business change and the
  outbox reply:**
  ```
  BEGIN
    INSERT INTO processed_event(event_id) ON CONFLICT DO NOTHING  -- 0 rows → duplicate → skip to COMMIT
    <business change>                                           -- e.g. sorted stock UPDATEs
    INSERT INTO outbox(...reply...)
  COMMIT
  ACK to RabbitMQ                                               -- strictly AFTER commit
  ```
  - Crash after COMMIT, before ACK → broker redelivers → inbox says duplicate → ACK, no double effect;
    the reply is already in the outbox → published.
  - ACK before commit would **lose** the message on a crash → never.
- **Error classification:**
  - transient (DB down, timeout) → requeue with backoff, *do not* DLQ quickly;
  - non-transient / bug (exception in handler, invalid payload) → 5 attempts with backoff
    (retry queues with TTL) → **DLQ**.
- **The saga does not hang forever:** step deadline (F1) fires → saga compensates and the customer
  gets "failed, try again". DLQ affects internal consistency, not the customer's wait.
- **Who watches DLQ:** alert on DLQ depth > 0 → on-call (at our volume every DLQ message is an
  incident). Dashboard shows message, headers, exception, original queue.
- **Redrive after the fix:** admin tool (or RabbitMQ shovel) moves messages back to the original
  queue. Safe because: inbox dedup, tombstones (late `ReserveStock` for a cancelled order → no-op),
  conditional transitions, entity `version` for stale events. Guard: the tool **refuses messages
  older than the tombstone retention** (14 days, F1) – those need manual review.

<a id="f4"></a>
**F4 – Separate databases on one shared Postgres cluster**
- **What we really get:** data ownership (no cross-database joins possible in Postgres), separate
  credentials per service, independent schema migrations, per-DB `pg_dump`, and above all
  **cheap future split** – moving one DB to its own cluster = logical replication/dump + new
  connection string, no code change.
- **What we don't get:** failure isolation (cluster down ⇒ all services down), resource isolation
  (noisy neighbour: CPU, I/O, connections), independent upgrades (one major version, one maintenance
  window), per-service point-in-time recovery (PITR is cluster-level).
- **Conscious compromise: yes.** Honest consequence – for DB failures A2 is **no more available than
  A1**; the availability gain is only at process level (one crashing service doesn't kill the others)
  and independent deploys.
- Mitigations now: DB role per service with `CONNECTION LIMIT` and `statement_timeout`; separate
  PgBouncer pool per service; `pg_stat_statements` per database monitoring.
- **Split the cluster when** (any of):
  1. a service's load measurably affects checkout latency (likely first: Notification bulk writes,
     Catalog search at peaks → Catalog read replica);
  2. different availability requirements (Payment + Ordering need HA standby with fast failover);
  3. compliance / audit for Payment data;
  4. separate teams own services and need independent maintenance windows.

<a id="f5"></a>
**F5 – Reading data across services (farmer page US 13, order history US 22)**
- Rule: **API composition** when sections are shown side by side and are independent;
  **read model** when we must filter / sort / paginate over combined data or the view is critical.
- **Farmer page → API composition in the BFF**: parallel calls, each with a timeout (~300 ms):
  profile + insertions from Catalog (**critical** – page fails without it), comments + badges from
  Community (**optional section**). Response cached in BFF/CDN for ~60 s (public, read-heavy).
  - **Community down:** page renders profile and insertions; comments/badges section shows
    "temporarily unavailable" – or the last cached version if still in cache. Graceful degradation,
    not a 500.
- **Order history → read model in Ordering** (`order_history_view`): Ordering owns the order and
  already receives most of the events for the saga; it additionally consumes
  `DeliveryStatusChanged` and `PaymentStatusChanged` (incl. refunds) and stores denormalised status
  columns. Paginating/filtering across 3 services by composition would be N+1 calls and slow.
  - Delivery/Payment down: history still works, status may be slightly stale.

<a id="f6"></a>
**F6 – Source of truth for "farmer can publish" (events from 3 services, any order)**
- Entity `version` can't help – the three facts have **three different owners**.
- **Fix: don't derive the state from the event sequence – store each fact separately, each with its
  own source version, and compute the permission:**
  ```
  farmer_permission(farmer_id,
    role_granted     bool, role_version     bigint,   -- from Identity
    payout_enabled   bool, payout_version   bigint,   -- from Payment
    suspended        bool, suspend_version  bigint)   -- from the owner of suspensions (admin/Identity)
  can_publish = role_granted AND payout_enabled AND NOT suspended
  ```
  - Each field updated only if `incoming.version > stored.version` for **that source**.
  - The predicate is an AND of independent facts → **order of arrival across sources doesn't matter**.
    Suspension processed before activation → `suspended = true`; activation later sets
    `payout_enabled = true`, but `can_publish` stays false. Correct.
  - Events are **state-transfer events** (`PayoutAccountStatusChanged{enabled: true, version: 7}`),
    not deltas → idempotent and safe to replay. Lifting a suspension = explicit event with a higher
    version (`suspended = false`), never implied.
  - One owner per fact (suspension owned by one service, not two). Missing event guard: nightly
    resync from each source's API.

<a id="f7"></a>
**F7 – Event schema evolution**
- **Envelope** for every event: `event_id, type, schema_version, occurred_at, correlation_id,
  causation_id, producer, payload`.
- **Rules:**
  - Allowed without coordination: **add an optional field**. Consumers are *tolerant readers*
    (ignore unknown fields, default missing ones).
  - Forbidden in place: remove, rename, change type/meaning.
  - **Rename = expand / contract:** add new field → producer writes both → consumers switch →
    remove old field once nobody reads it.
  - Truly breaking change → new type `InsertionPublished.v2`, producer publishes **v1 and v2 in
    parallel** during migration.
  - Deploy order: additive change → producer first is fine; removal → consumers first.
- **Tooling:** JSON Schema / AsyncAPI in a shared `contracts` repo; CI check of schema compatibility
  on every change; **consumer-driven contract tests** (Pact message pacts) – producer's CI fails if it
  breaks a consumer's expectation and tells us who still uses the old field. Confluent-style schema
  registry rejected – Kafka-centric, overkill for RabbitMQ at our size.
- **How long is the old version supported:** until (a) contract tests show no consumer uses it **and**
  (b) the max message age has passed – messages can sit in DLQ up to 14 days (F1/F3). In practice
  ≥ one release cycle + 14 days.

<a id="f8"></a>
**F8 – Debugging "I paid and I don't see my order" + local development**
- **Step by step:**
  1. Admin UI: find the customer → orders incl. hidden `PENDING` ones → `order_id`.
  2. **Saga table + `saga_step_log`** in Ordering: state, current step, deadline, history → e.g. stuck
     in S4 "waiting for payment result".
  3. **Correlation id = `order_id`** in every command/event envelope and log line + W3C
     `traceparent` propagated through message headers → **OpenTelemetry tracing** (Jaeger/Tempo)
     shows the whole chain Ordering → Catalog → Payment → Stripe webhook; centralised structured
     logs (Loki/ELK) – one query by `order_id` across all services.
  4. Payment: is the webhook in the Stripe event log table? No → Stripe dashboard → webhook
     deliveries (endpoint down, wrong signing secret). Yes → is `PaymentSucceeded` still in Payment's
     **outbox** (relay lag)? Published → is it in Ordering's queue or **DLQ**?
  5. Fix: redrive from DLQ (F3) or admin action **"resolve session"** (`ResolveSession`, F1) → Payment
     asks Stripe and emits the terminal event; saga continues or refunds.
  - Answer to the customer: the payment exists in Stripe → the order will be confirmed or
    automatically refunded.
  - Admin UI shows a **per-order timeline** assembled from the correlation id across services.
- **Local development:**
  - `docker compose` with infra: Postgres (init script creates a DB per service), RabbitMQ, Keycloak
    (realm imported from JSON), Mailpit (catches e-mails), Jaeger, **Stripe CLI**
    `stripe listen --forward-to` for webhooks in test mode.
  - The service you work on runs from the IDE; the other 5 as prebuilt images from `main`.
    Needs ~6–8 GB RAM. Shortened timeouts via config (no waiting 30 min for T1).
  - Test pyramid: most coverage in **component tests per service** (Testcontainers) + **contract
    tests** (F7); only a handful of **end-to-end checkout tests** (Playwright, Stripe test cards) on
    the full compose stack, nightly in CI.

<a id="f9"></a>
**F9 – Honest cost**
| | Architecture 1 (monolith) | Architecture 2 (microservices) |
|---|---|---|
| Deployables | 1 image, 3 process types | 6 services + BFF/gateway + Keycloak + RabbitMQ ≈ 9 deployables, ~15–20 running processes (2 replicas each) |
| CI pipelines | 1 | ~8 (per service + BFF + contracts repo) |
| Mandatory extras | – | outbox relay per service, inbox, tracing, central logs, DLQ tooling, contract tests |
| Team | 2–4 devs | realistically 5–8 devs incl. part-time platform/DevOps; on-call across 6 services |
| Infra / month (rough order of magnitude, managed cloud, small sizes) | ~€150–300 | ~€500–1 200 (more containers, managed broker, Keycloak + its DB, observability) |
- *Infra numbers are rough estimates, not quotes.* Infra is 3–5× more, but the **dominant cost is
  people** – a large share of dev time goes to plumbing (sagas, idempotency, contracts) instead of
  features.
- **Microservices would pay off when:** several independent teams (≈15+ devs) block each other in one
  codebase; parts with very different scaling/availability needs appear (national scale search,
  live GPS tracking of riders); payments need regulatory isolation; independent release cadence is a
  business need (e.g. expansion to several countries).
- **If we start with the monolith, extract first: Notification.**
  - Pure consumer of events – nobody waits for it, no sync calls into it, no saga.
  - Biggest isolation gain: fan-out, external rate limits and retries (A1 weakness) leave the main DB
    and process.
  - Lowest-risk way to introduce the broker + outbox relay: a late/lost notification is not money.
  - Strangler approach. Next candidates later: Payment (compliance), Delivery (real-time).
    **Not** Catalog/Ordering first – splitting the shared `reserve_stock` transaction means the
    checkout saga immediately = highest risk.

<a id="a2-final"></a>
### Architecture 2 – Final assessment (after the whole discussion)

**Strengths**
- Independent deploys and scaling per service; a crash of one process doesn't kill the others;
  Notification fan-out can no longer slow down checkout (F4 caveat: shared DB cluster).
- Boundaries enforced physically (own DB per service) instead of by CI rules (A1 Q8).
- Stripe and money logic isolated in Payment – security, secrets, audit (A2.1).
- Ready for team growth and different technology/scaling needs per area.
- Failure handling is explicit and well understood: outbox/inbox, tombstones, step deadlines,
  DLQ redrive (F1–F3).

**Weaknesses**
- Checkout loses its single transaction → saga with compensations, tombstones, timeouts (A2.4, F1).
- Eventual consistency becomes visible to users: waiting for the Stripe URL, stale read models (F5).
- Every producer/consumer needs outbox + inbox + idempotency; multi-source state needs per-source
  versioning (F6); schemas need evolution discipline + contract tests (F7).
- Debugging requires tracing, central logs, saga timeline UI (F8); local dev is heavy.
- 3–5× infra cost, ~8 pipelines, larger team (F9); shared Postgres limits real isolation (F4).

**Risks**
1. **Distributed monolith** – services that must be deployed together because of hidden coupling;
   all costs of microservices, none of the benefits.
2. **Money inconsistencies across services** – paid order without transfer, transfer without delivery;
   reconciliation now spans Payment, Ordering and Delivery.
3. **Wrong boundaries are expensive** – moving data and responsibilities between services is a
   migration project, not a refactoring.
4. **Ops overload of a small team** – on-call for 6 services + broker + Keycloak; DLQ incidents.
5. **Contract breakage** between independently deployed services.

**Verdict:** technically sound, but **not justified for E-Farmers at its current scale and team size.**
Valid as a *target* reached incrementally from the monolith (strangler, Notification first).

## Architecture 3 – Serverless / BaaS (Supabase + Edge Functions + Stripe)

*(proposed by assistant; lock-in, cost and testing in the next round)*

**Idea:** no own backend server. Supabase provides Postgres, Auth, Storage, Realtime and an
auto-generated REST API (PostgREST) – the frontend talks **directly to the database**, protected by
Row-Level Security. Logic that must be atomic lives in **Postgres functions (RPC)**; logic that
talks to the outside world lives in **Edge Functions** (Deno, stateless, short-lived). Background work
= `pg_cron` + `pgmq` (Supabase Queues) + Edge Functions as workers.

```
[Browser SPA] ──JWT──▶ PostgREST (/rest/v1)  ──▶ Postgres (RLS)  ◀── pg_cron (timers, sweeps)
     │                  /rpc/* (SQL functions) ─┘   ├─ public  schema (exposed, RLS everywhere)
     │                                              ├─ private schema (NOT exposed: payments, internal fns)
     ├──JWT──▶ Edge Functions (checkout, Stripe, mail/push workers) ──▶ Stripe, e-mail, FCM, geocoding
     ├──────▶ Supabase Auth (email + OAuth)         └─ pgmq queues (outbox / jobs)
     ├──────▶ Storage (photos, RLS on storage.objects, image transformations)
     └──ws──▶ Realtime (notification center, rider offers)
Stripe ──webhook──▶ Edge Function `stripe-webhook`
```

<a id="a3-1"></a>
### A3.1 What goes where
| Concern | Where | Notes |
|---|---|---|
| Registration e-mail + OAuth (US 1, 29), login/logout (US 2, 3) | **Supabase Auth** | Google etc. configured as providers. Q13 linking rules: Supabase auto-links identities by e-mail – **must verify its behaviour for unverified e-mails** against the pre-account-takeover scenario (test case, not assumption). |
| Roles in JWT | **Custom Access Token Hook** (SQL function adds roles to claims) | Claims only for UI. **RLS decides from tables, not from claims** → no stale-role problem from A2.6. |
| Profiles, insertions, boxes, calendar, search, subscriptions, comments, notification center | **Direct PostgREST + RLS** (simple owner-limited CRUD, reads) | Search = Postgres FTS via view/RPC. |
| Photos | **Storage** bucket, path `farmer_id/insertion_id/…`, RLS on `storage.objects` | Thumbnails via built-in image transformations (no CPU in Edge Functions). |
| Notification center, rider offers live | **Realtime** (postgres_changes respects RLS; Broadcast if it grows) | |
| `reserve_stock`, `start_checkout`, `accept_booking`, `accept_delivery`, `add_stock`, `upgrade_to_farmer/rider` | **Postgres functions (RPC)** | Everything that needs a transaction over our data. |
| Stripe Checkout / SetupIntent / Connect onboarding / transfers / refunds, e-mail, push, geocoding | **Edge Functions** | Need secrets and external I/O. |
| Stripe webhooks | **Edge Function `stripe-webhook`** | A3.5 |
| Timers, sweeps, queue draining | **pg_cron** (+ pg_net to call Edge Functions) | A3.4 |

- **Placement rule:**
  1. **Needs atomicity over our data → Postgres function** (one transaction, no network I/O).
  2. **Needs an external call or a secret → Edge Function**, which calls RPCs for state changes
     and never holds a DB transaction across the external call.
  3. **Plain CRUD of the user's own data → client directly**, guarded by RLS + column grants.
- **Own server: none.** Admin back-office = separate frontend calling admin-only RPCs / Edge
  Functions (role check inside), never the service-role key in a browser.

<a id="a3-2"></a>
### A3.2 Security – RLS is the only barrier
Conventions: `(select auth.uid())` instead of `auth.uid()` (evaluated once per query, not per row);
helper functions in the **non-exposed** `private` schema.

```sql
-- ===== Insertions & boxes: owner only (US 9, 10, 31); public read (US 8) =====
ALTER TABLE public.insertion ENABLE ROW LEVEL SECURITY;
CREATE POLICY insertion_read   ON public.insertion FOR SELECT TO anon, authenticated USING (deleted_at IS NULL);
CREATE POLICY insertion_insert ON public.insertion FOR INSERT TO authenticated
  WITH CHECK (farmer_id = (select auth.uid()) AND private.can_publish((select auth.uid())));   -- F6 predicate
CREATE POLICY insertion_update ON public.insertion FOR UPDATE TO authenticated
  USING (farmer_id = (select auth.uid())) WITH CHECK (farmer_id = (select auth.uid()));
-- no DELETE policy: deletion (US 9) = soft delete via UPDATE deleted_at, or RPC that refuses
-- when boxes have active reservations

ALTER TABLE public.box ENABLE ROW LEVEL SECURITY;
CREATE POLICY box_read   ON public.box FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY box_insert ON public.box FOR INSERT TO authenticated
  WITH CHECK (EXISTS (SELECT 1 FROM public.insertion i
                      WHERE i.id = insertion_id AND i.farmer_id = (select auth.uid())));
CREATE POLICY box_update ON public.box FOR UPDATE TO authenticated
  USING      (EXISTS (SELECT 1 FROM public.insertion i WHERE i.id = insertion_id AND i.farmer_id = (select auth.uid())))
  WITH CHECK (EXISTS (SELECT 1 FROM public.insertion i WHERE i.id = insertion_id AND i.farmer_id = (select auth.uid())));
-- column-level: client may never touch stock after creation
REVOKE INSERT, UPDATE ON public.box FROM anon, authenticated;
GRANT  INSERT (insertion_id, title, price, qty, expires_at) ON public.box TO authenticated;
GRANT  UPDATE (title, price, expires_at)                    ON public.box TO authenticated;
-- adding stock later = RPC add_stock(box_id, n) with the same owner check

-- ===== Comment only by the buyer after pickup (US 23) =====
ALTER TABLE public.comment ENABLE ROW LEVEL SECURITY;
CREATE POLICY comment_read   ON public.comment FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY comment_insert ON public.comment FOR INSERT TO authenticated
  WITH CHECK (author_id = (select auth.uid())
              AND private.has_completed_purchase(farmer_order_id, (select auth.uid())));
--   helper checks farmer_order.customer_id = uid AND status IN ('PICKED_UP','DELIVERED','COMPLETED')
--   + UNIQUE (farmer_order_id) → one comment per purchase

-- ===== Customer sees only own orders =====
ALTER TABLE public.orders       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.farmer_order ENABLE ROW LEVEL SECURITY;
CREATE POLICY orders_own ON public.orders FOR SELECT TO authenticated
  USING (customer_id = (select auth.uid()) AND status <> 'PENDING');           -- hide unfinished checkouts
CREATE POLICY farmer_order_parties ON public.farmer_order FOR SELECT TO authenticated
  USING (customer_id = (select auth.uid())                                     -- buyer
      OR farmer_id   = (select auth.uid())                                     -- seller
      OR private.is_assigned_rider(id, (select auth.uid())));                  -- rider of its delivery
-- NO insert/update/delete policies + REVOKE → orders change only through RPC / Edge Functions

-- ===== Rider sees offers within radius (PostGIS) =====
ALTER TABLE public.delivery ENABLE ROW LEVEL SECURITY;
CREATE POLICY delivery_rider ON public.delivery FOR SELECT TO authenticated
  USING (rider_id = (select auth.uid())
      OR (status = 'OFFERED' AND EXISTS (
            SELECT 1 FROM public.rider_profile r
            WHERE r.user_id = (select auth.uid()) AND r.status = 'ACTIVE' AND r.available
              AND ST_DWithin(r.geo, delivery.pickup_geo, delivery.offer_radius_m))));
-- RLS filters rows, not columns: before acceptance the rider must not see the exact customer address
-- → riders read offers through a view exposing only pickup area, distance, fee; accept via RPC
--   accept_delivery(id) (atomic UPDATE ... WHERE rider_id IS NULL + active_deliveries check, Q10)
```

- **Never writable by the client:** `box.qty` after creation, everything in `orders`/`farmer_order`/
  `order_item` (status, amounts, price snapshots), `reservation*`, `delivery.status/rider_id`,
  `rider_profile.active_deliveries`, `farmer_permission`, badges. **Payments, Stripe ids, transfers,
  `payout_account`, Stripe event log → `private` schema** – not exposed by PostgREST at all.
- **Forgotten RLS on a new table:** Supabase grants table privileges in `public` to `anon` and
  `authenticated` by default → a table without RLS is **readable and writable by anyone with the
  public anon key**. Defences:
  1. **Event trigger** on `ddl_command_end` that runs `ALTER TABLE … ENABLE ROW LEVEL SECURITY` for
     every new table in `public` → RLS on with no policy = **deny all** (safe default; a forgotten
     policy breaks the feature, not security).
  2. **CI fails** on Supabase database linter/advisors (`rls_disabled_in_public`,
     `function_search_path_mutable`, …) – run on every migration.
  3. Internal tables live in `private` from the start.
  4. Optionally `ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon` – grant explicitly.
- **Internal `SECURITY DEFINER` functions (e.g. `mark_order_paid`) must not be callable by clients:**
  - Postgres grants `EXECUTE` on new functions to `PUBLIC` by default; Supabase adds grants for
    `anon`/`authenticated` in `public`. So:
    1. Put them in **`private`** (not in the exposed schemas → PostgREST cannot route `/rpc/` to them).
    2. **And** revoke anyway (defence in depth):
       `REVOKE EXECUTE ON FUNCTION private.mark_order_paid(uuid, text) FROM PUBLIC, anon, authenticated;`
       `GRANT EXECUTE … TO service_role;`
       `ALTER DEFAULT PRIVILEGES IN SCHEMA private REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;`
    3. Client-callable RPCs (`start_checkout`, `accept_delivery`) are thin `SECURITY DEFINER`
       wrappers that **derive the actor from `auth.uid()`**, never take `user_id` as a parameter.
  - **`search_path`:** every `SECURITY DEFINER` function gets `SET search_path = ''` and uses fully
    qualified names (`public.box`, `pg_catalog.now()`). Otherwise a caller who can create objects in
    a schema on the search path could shadow a table/function and run code with the owner's rights.

<a id="a3-3"></a>
### A3.3 Checkout without a long-running process
- **Big win vs. A2: one database again** → order + stock reservation in **one transaction** (A1 Q1/Q8
  return unchanged). Only the Stripe call is outside, exactly as in A1.
- The DB row is the state machine; the Edge Function is a stateless driver; **every step idempotent,
  keyed by `order_id`**:
  1. RPC `start_checkout(cart)` – one txn: order `PENDING` + sorted stock UPDATEs + reservation
     `RESERVED, session_id NULL, hold_until = now() + 35 min` → returns `order_id`.
     Not enough stock → whole txn rolls back, returns unavailable boxes.
  2. Edge Function → Stripe `checkout.sessions.create` (**idempotency key = `order_id`**,
     `expires_at = 30 min`, `metadata.order_id`).
  3. RPC `attach_session(order_id, session_id)` – `UPDATE … SET session_id = ? WHERE order_id = ?
     AND status = 'RESERVED' AND session_id IS NULL`. 0 rows because the order was already released →
     Edge Function expires the session in Stripe.
  4. Return the URL to the browser.
- **Crash / timeout between steps:**
  - After 1, before 2/3 → the customer never got a URL, **cannot pay**. Client retry of "pay" →
    function sees `RESERVED, session_id NULL` → repeats step 2 → Stripe returns the **same session**
    (same idempotency key, valid 24 h) → attach → continue. Retry resumes, doesn't duplicate.
  - Nobody retries → **pg_cron sweep** each minute: `RESERVED AND session_id IS NULL AND created_at <
    now() - 2 min` → release stock (safe: no URL, no payment possible).
  - With a session: released only after the session is dead (A1 Q6 rule) – `checkout.session.expired`
    webhook, or the sweeper at `hold_until` enqueues "expire session" → Stripe confirms → release.
  - Whole flow ≈ 1–2 s → far below Edge Function limits.

<a id="a3-4"></a>
### A3.4 Timers, outbox and fan-out without a long-running process
- **Tools and verdict:**
  | Tool | What it is | Use |
  |---|---|---|
  | `pg_cron` | cron inside Postgres (minute schedules; seconds-interval in newer versions) | **all timers + kick the workers** |
  | `pgmq` (Supabase Queues) | durable queue in Postgres; `send` in a txn, `read` with visibility timeout, `delete`/`archive`, `read_ct` | **outbox + job queue** |
  | `pg_net` | async HTTP from SQL, fire-and-forget | only to *invoke* Edge Function workers from pg_cron |
  | Database Webhooks | trigger → pg_net HTTP | **rejected for anything important**: no durable retry/redelivery |
- **Timers T1–T7 = pure SQL in pg_cron** (each minute), conditional transitions exactly as Q11:
  `UPDATE booking SET status = 'DECLINED' WHERE status = 'PENDING' AND respond_by <= now() RETURNING …`
  (T2), T3 expire unpaid booking orders, T4/T5 widen `offer_radius_m` / give up, T6 unassign rider,
  T7 auto-confirm. Side effects needing the outside world (notify, Stripe transfer on T7, expire
  session on T1) → **`pgmq.send` in the same txn** = transactional outbox.
  - Only one pg_cron scheduler per DB → no "two instances" problem; conditional transitions still
    make overlapping runs harmless.
- **Workers:** pg_cron every ~10 s → `net.http_post` (service key from Vault) → Edge Function worker
  → `pgmq.read(queue, vt => 60, qty => 50)` → process → `pgmq.delete` on success.
  - Failure/crash → message reappears after the visibility timeout (**retry for free**); backoff via
    `pgmq.set_vt` growing with `read_ct`; `read_ct > 5` → `pgmq.archive` into a dead-letter queue + alert.
- **Fan-out to 5 000 subscribers:** trigger on new insertion → one `fanout` message → worker does the
  set-based `INSERT … SELECT` of in-app notifications (Q9) and `pgmq.send_batch` of per-recipient
  e-mail/push deliveries (`notification_delivery` model and duplicate rules from Q14 unchanged).
  - **Rate limit by construction:** throughput = cron frequency × batch size × parallel invocations
    (e.g. every 10 s × 50 = 5/s) – tuned to the provider limit.
- **Edge Function limits** (per Supabase docs, re-check for current plan): ~**256 MB memory**,
  **~2 s CPU time** per request (I/O waiting not counted), wall clock **150 s (free) / 400 s (paid)**.
  - Work-arounds: never one long job – **small batches + queue as checkpoint**; stop taking new
    messages when the time budget is nearly used; `EdgeRuntime.waitUntil` only for short tails after
    the response; CPU-heavy work (images) via Storage transformations, not in functions.

<a id="a3-5"></a>
### A3.5 Stripe webhooks in an Edge Function
- Deploy with **JWT verification off** (`--no-verify-jwt`) – Stripe sends no Supabase JWT; the
  **Stripe signature is the authentication**.
- **Raw body:** `const body = await req.text()` – never parse JSON before verification; in Deno use
  `await stripe.webhooks.constructEventAsync(body, sig, secret, undefined, Stripe.createSubtleCryptoProvider())`
  (WebCrypto is async).
- **Fast ack:** verify → RPC `private.record_stripe_event(event)` (via service role): `INSERT INTO
  private.stripe_event(id …) ON CONFLICT DO NOTHING` + `pgmq.send('stripe_events', …)` in one txn →
  return 200. Processing by a worker.
- **Cold start:** typically sub-second; Stripe waits several seconds and **retries for up to 3 days**
  with backoff → not a correctness issue, fast ack keeps it far from timeouts.
- **Idempotency:** event id as PK (duplicates ignored) + conditional state transitions in processing.
- **Carried over from A1 unchanged:** atomic sorted stock UPDATEs (Q1), all-or-nothing reservation,
  "no Stripe in the stock transaction" (Q3), one-timer rule / release only after session is dead (Q6),
  SetupIntent + off-session for bookings, SEPA only for bookings (Q2, Q6), Connect Express + separate
  charges and transfers (Q5), transfer timing (Q7), conditional transitions for timers (Q11), rider
  counter (Q10), data model incl. profiles and `payout_account` (Q12), notification delivery model (Q14),
  outbox idea (Q9 → pgmq).
- **What changes:** authorization moves from application code to **RLS + grants** (A3.2); module
  boundaries become **schemas + grants**; the process model becomes **pg_cron + queues + short
  functions** instead of a worker; the **DB schema becomes the public API** of the frontend
  (consequences for versioning → next round).

### Discussion log – security & development (A3)

<a id="s1"></a>
**S1 – Rider offer view vs. RLS; event trigger on managed Supabase**
- Student is right: a plain view runs with its **owner's** rights and bypasses RLS of the base table
  (Supabase linter flags it as `security_definer_view`).
- `security_invoker = true` (PG 15+) → RLS of `delivery` applies, but the rider then needs `SELECT`
  on `delivery` and could query the base table directly through PostgREST.
- **Column grants don't solve it:** they are per *role*, and every logged-in user is the same role
  `authenticated` → impossible to say "the assigned rider sees the address, other riders don't".
  Visibility differs **per row and per user** → that is RLS's job → **split the data:**
  - `delivery` – only non-sensitive columns: status, pickup area, `pickup_geo`, distance, fee,
    coarse drop-off area (district / rounded geo for fee display). RLS policy `delivery_rider` (A3.2).
  - `delivery_dropoff(delivery_id PK, address, geo, phone)` – own RLS: visible only to the customer
    of the order and to `rider_id = auth.uid()` while status is `ASSIGNED`/`PICKED_UP`.
  - Offer view (`security_invoker = true`) only for convenience/shape; security is in the tables.
  - Alternative considered: `SECURITY DEFINER` RPC `get_delivery_offers()` filtering by `auth.uid()`
    – works, but security then lives in code of one function, not in the data model. Rejected.
- **Event trigger – verified:** since 2025 Supabase allows the `postgres` role to create event
  triggers via the `supautils` extension (proxy for superuser, without giving superuser).
  Caveats: user event triggers are **skipped for superuser and reserved roles** – migrations from
  CLI run as `postgres` → fires; changes made by internal Supabase roles would not. Older projects
  may need an upgrade.
  → Event trigger = first line, **CI linter (`rls_disabled_in_public`) stays as the second line**.

<a id="s2"></a>
**S2 – DB schema as public API (web + mobile apps living for months)**
- **Decision: expose only an `api` schema** (PostgREST "exposed schemas" = `api_v1` only, not
  `public`); tables move to `app` (internal) + `private`.
  - `api_v1` = `security_invoker` views over tables + RPC functions; writes preferably via RPC
    (complex views need `INSTEAD OF` triggers – avoid).
  - **Rename a column:** rename in `app`, `api_v1` view keeps the old name as an alias → old clients
    unaffected. **Split a table:** `api_v1` view joins the two new tables.
  - **Breaking change:** new schema `api_v2` side by side; clients choose the schema
    (`supabase.schema('api_v2')`, PostgREST `Accept-Profile` header). Old schema dropped when usage
    (logged per schema) falls to zero + **minimum app version check** in the mobile app (force upgrade).
  - Caveat: Realtime `postgres_changes` works on tables, not views → realtime via Broadcast from
    triggers instead.
- **Is it our own API layer again, just written in SQL? Yes – honestly.** Maintaining `api_v1/v2`
  views and RPCs costs about the same as maintaining REST endpoints, and SQL has weaker tooling for
  logic. What remains from BaaS: no server to run/scale, Auth/Storage/Realtime built-in, contract
  declarative and close to the data. **The promise "no API layer" does not survive a mobile app.**
  For a web-only MVP `api_v1` is still worth it from day one (cheap now, expensive later).

<a id="s3"></a>
**S3 – Testing, review, debugging, local vs. prod, migrations**
- **RLS tests – pgTAP** via `supabase test db`:
  ```sql
  SET LOCAL ROLE authenticated;
  SET LOCAL request.jwt.claims = '{"sub":"<farmer_b_uuid>","role":"authenticated"}';
  SELECT throws_ok($$ UPDATE api_v1.insertion SET title = 'x' WHERE id = '<farmer_a_insertion>' $$);
  -- or: is((UPDATE ... RETURNING 1), NULL) when RLS silently filters rows (UPDATE of 0 rows, no error!)
  ```
  - Test helpers (e.g. community `supabase-test-helpers`: create user, authenticate as, check RLS
    enabled on all tables).
  - **Matrix per table × operation × actor** (anon, owner, other user, farmer without payout,
    suspended farmer, rider outside radius, assigned rider) → expected allowed/denied.
  - Note: RLS denial is often **not an error but 0 rows** → tests must assert row counts, not only exceptions.
  - Plus a test "every table in exposed/app schemas has RLS enabled" (query `pg_class.relrowsecurity`).
- **Time:** `now()` is also constant within a transaction (txn start), so tests couldn't move it anyway.
  → **Timer functions take time as a parameter:** `private.expire_bookings(p_now timestamptz)`;
  pg_cron calls `SELECT private.expire_bookings(now())`, tests call it with any time.
  Functions never call `now()` internally for business decisions.
- **Code review:** migrations are append-only → a changed function shows up as a full
  `CREATE OR REPLACE` copy (diff unreadable). → Keep function/table sources in **declarative schema
  files** (`supabase/schemas/*.sql`), generate migrations with `supabase db diff`; review the diff of
  the schema files. Static analysis: `plpgsql_check` (used by `supabase db lint`) in CI.
- **Debugging/logging PL/pgSQL:** no debugger in prod. `RAISE LOG` with a request id
  (`current_setting('request.headers')` from PostgREST) → Postgres logs in the dashboard / Log Drains.
  **Do not log into a table inside the business transaction** – a failing txn rolls the log row back
  with everything else. Edge Function logs separately (`console.log`) → correlate by request/order id.
- **Local (Supabase CLI, Docker) vs. production:**
  | Thing | Local | Production |
  |---|---|---|
  | pg_cron | works | works |
  | pg_net → Edge Function | URL differs (Docker network, not `127.0.0.1`) | public function URL → **base URL in Vault/config per env**, never hard-coded |
  | Auth e-mails | caught by local mail catcher (Inbucket/Mailpit) | **default Supabase SMTP is rate-limited, meant for testing → must configure own SMTP provider** |
  | OAuth | provider config in `config.toml`, redirect to localhost, separate OAuth client | production client + redirect URLs |
  | Edge Function limits | not representative | real CPU/wall limits → load test on staging |
  | Stripe webhooks | `stripe listen --forward-to localhost:54321/functions/v1/stripe-webhook` | real endpoint + signing secret |
- **Migrations & environments:** `supabase db diff` → SQL migration in git → CI applies with
  `supabase db push` (staging, then prod after approval). Environments = **separate Supabase
  projects** (staging, prod), secrets per project. **Branching** (paid): preview DB per PR from
  migrations + `seed.sql` (no prod data). Lock-safe migration rules from A1 still apply.

<a id="s4"></a>
**S4 – Worker concurrency, secret for pg_net, 17 minutes for 5 000 e-mails**
- pg_cron itself never runs the same job twice in parallel, **but** our job only fires `net.http_post`
  (async, ms) → the Edge Function runs independently → **invocations overlap**. Student is right:
  "rate limit by construction" does not hold.
  - Duplicates are not the issue (pgmq `read` with visibility timeout hands each message to one worker);
    **rate and concurrency** are.
- **Fix:**
  1. **Lease rows** bound concurrency: `UPDATE private.worker_lease SET holder = :id,
     expires_at = now() + interval '60 s' WHERE name = 'email_1' AND expires_at < now()` → only the
     lease holder works; `k` lease rows = max `k` parallel workers. Lease expires on crash.
     (Session advisory locks rejected – connections are pooled, the lock outlives the request or leaks.)
  2. **Global token bucket in the DB** `private.rate_bucket(name, tokens, refilled_at)` – worker takes
     N tokens atomically (`UPDATE … RETURNING`) before each batch → provider rate holds regardless of
     how many workers run.
  3. Worker time budget < cron interval.
- **Secret for pg_net → Edge Function:** stored in **Supabase Vault** (`vault.create_secret`), read in
  the cron SQL from `vault.decrypted_secrets` (schema not exposed by the API).
  - **Not the service-role key**, but a dedicated `WORKER_SECRET`: worker function deployed with
    `--no-verify-jwt` and checks the header. Leak ⇒ attacker can only trigger a worker run (idempotent,
    harmless), not read the whole DB. The worker reads `SUPABASE_SERVICE_ROLE_KEY` from its own env.
- **17 minutes (5/s) – it depends on the channel:**
  - In-app (Realtime) for all subscribers: **instant** (one set-based INSERT).
  - Push (FCM): N requests but high quotas and HTTP/2 concurrency → seconds.
  - E-mail: 5/s was only an example. With the provider's **batch API** (≈100 recipients per call) and
    its real limit → seconds to a minute. 5 000 is the upper bound; realistic farmer has hundreds.
  - **Fairness issue spotted:** limited stock (Saturday strawberries) + 17 min spread ⇒ the first
    recipients get a head start. → recipients **shuffled**, the instant channels (in-app/push) are the
    primary ones, e-mail can be a digest.
  - **Conclusion:** 17 min would be fine only for a digest-type e-mail, not as the main channel.

### Discussion log – lock-in, cost, realtime, GDPR, critique (A3)

<a id="l1"></a>
**L1 – Lock-in and exit plan**
- **Portable:** Postgres itself (schema, data, PL/pgSQL, RLS policies), `pg_cron`, `pgmq`, PostGIS,
  PostgREST, Vault extension – all open source; Edge Function code is TypeScript (Deno) → reusable in
  Node/Deno with small changes; Storage files are plain objects (S3-compatible API). Supabase itself is
  open source and self-hostable.
- **Sticky:** `auth` schema (GoTrue) and `auth.uid()`/`auth.jwt()` in every policy (they only read the
  `request.jwt.claims` setting → reproducible elsewhere); Realtime protocol + client library;
  Custom Access Token Hook; supautils event trigger; dashboard, Branching, Log Drains.
  **Biggest lock-in is the architectural style** (RLS as authorization, `supabase.from()` calls in the
  frontend), not the vendor.
- **Exit A – self-hosted Supabase** (Docker Compose / community Helm): code unchanged; ~1–2 weeks to set
  up, but then **we operate ~10 components** (Postgres HA, backups, upgrades, GoTrue, Realtime, Kong,
  Storage, Edge Runtime…). Lock-in traded for ops burden; Branching and some dashboard features lost.
- **Exit B – move to an A1-style backend** (more sensible long-term):
  1. Postgres: dump/restore (incl. `auth` schema), or keep it on any managed Postgres.
  2. **Migration trick:** the new backend sets `request.jwt.claims` per transaction → existing RLS
     policies keep working while code moves over; drop them gradually.
  3. Rewrite: `api_v1` views/RPC → REST endpoints; frontend data layer (all `supabase.from()` calls);
     Auth → own/Keycloak/Auth.js; Storage → S3 bucket (URLs change); Realtime → WebSocket/SSE in backend;
     Edge Functions → backend handlers (TS reused); pg_cron/pgmq can stay or move to a job library.
  4. **Rough effort for our MVP size: ~2–4 developer-months**, dominated by the frontend data layer.
     Mitigation now: frontend accesses data only through a thin repository layer, never
     `supabase.from()` scattered in components.
- **Passwords: yes, transferable.** `auth.users.encrypted_password` holds standard **bcrypt** hashes →
  importable into any system supporting bcrypt (Keycloak with bcrypt hash provider, Auth0 bulk import,
  own table) → no forced reset. OAuth identities (`auth.identities`: provider + subject) mapped 1:1;
  keep the same OAuth client/project so provider subjects stay stable. Sessions and MFA enrolments
  are lost → users log in again.

<a id="l2"></a>
**L2 – Cost**
- Billing items (Pro plan, third-party summaries of the pricing page – **verify on supabase.com before
  relying on it**): base **$25/month** incl. compute credit for the smallest instance; included ~100k MAU
  (then ~$0.00325/MAU), 8 GB DB, 100 GB files, 250 GB egress (then ~$0.09/GB), 2M Edge Function
  invocations (then ~$2/M), Realtime 500 peak connections + 5M messages (then ~$2.50/M messages);
  bigger compute instances, PITR, extra projects (staging) and Branching hours billed extra.
- **Our scale:** few thousand MAU, low egress (photos via CDN cache), worker cron every 10 s ≈ 0.3–1M
  invocations/month, hundreds of Realtime connections → mostly within included quotas.
  Need a larger compute instance (pg_cron, pgmq, PostGIS, RLS at peaks) + staging project + own SMTP
  + PITR (money system).
  | | Our scale | 10× growth |
  |---|---|---|
  | **A3 Supabase** | ~€100–250/month (≈€60–120 without PITR) | ~€250–500 (bigger compute, Realtime connections/messages, egress) |
  | A1 monolith (managed PaaS + Postgres) | ~€150–300 | ~€300–600 |
  | A2 microservices | ~€500–1 200 | ~€1 000–2 000 |
  *Rough order-of-magnitude estimates.* People cost (ops time saved) matters more than these numbers.
- **When BaaS becomes expensive:** egress-heavy media (photos/video without a CDN, image
  transformations), **many concurrent Realtime connections + high message volume** (e.g. live GPS of
  riders), hundreds of thousands of MAU (MAU price grows linearly), large compute tiers priced above raw
  VMs. Rule of thumb: once the bill exceeds the cost of ~0.5 DevOps FTE, self-hosting / A1 pays off.
  Unlikely for a regional E-Farmers.

<a id="l3"></a>
**L3 – Broadcast from triggers, offline clients, private channels**
- **Rollback:** broadcasting from the DB (`realtime.send` / `realtime.broadcast_changes`) writes into
  `realtime.messages`, which Realtime delivers from the WAL → **only committed** messages are sent;
  rollback ⇒ nothing goes out (to confirm with a test). Never broadcast from an Edge Function *before*
  the DB commit.
- **Broadcast is a signal, not the source of truth** – pattern **"signal + fetch"**:
  - messages carry only ids + `version`; client dedupes by version;
  - on (re)connect (channel status back to `SUBSCRIBED`, app back to foreground) the client **fetches
    the current state** via `api_v1` (open offers, notifications with `id > last_seen`).
  - Rider offline 30 s: the offer is still `OFFERED` in the DB → appears after the reconnect fetch; if
    another rider took it meanwhile it is simply gone (correct). Riders additionally get **push (FCM)**
    for new offers when the app is in background.
- **Private channels = Realtime Authorization:** channels created with `private: true`, **RLS policies
  on `realtime.messages`** using `realtime.topic()`:
  ```sql
  CREATE POLICY user_channel_read ON realtime.messages FOR SELECT TO authenticated
    USING (realtime.topic() = 'user:' || (select auth.uid())::text);
  -- no INSERT policy for clients → only DB triggers / server can send
  ```
  Public channel access disabled in project settings; topic names being unguessable is **not** the
  security – RLS is. Rider offers: per-rider topic `rider:<uuid>` filled by the dispatch trigger.

<a id="l4"></a>
**L4 – GDPR** *(not legal advice – to be confirmed with a DPO/lawyer)*
- **Region:** project created in an **EU region** (chosen at creation, cannot be moved later without
  migration). Edge Functions execute close to the caller by default → check/pin execution region.
- **DPA:** sign Supabase's DPA (SCCs for transfers – Supabase is a US company); record of processing
  with all sub-processors: Supabase (AWS), e-mail provider, Stripe (partly an independent controller),
  FCM (Google), geocoding provider.
- **Right to erasure – `delete_account` process (Edge Function, service role), within 1 month:**
  | Where | Action |
  |---|---|
  | Auth | `auth.admin.deleteUser()`; our FKs to `auth.users` must **not cascade into orders** |
  | Profiles, addresses (`delivery_dropoff`), subscriptions, notifications, device tokens | delete |
  | Comments | delete or anonymise author ("deleted user") |
  | Storage (farmer photos) | delete **via Storage API** – deleting the `storage.objects` row alone does not delete the file |
  | Stripe | delete Customer; Connect account (farmer/rider) closed/rejected – Stripe keeps KYC/payment data under its own legal obligations |
  | Logs | short retention, **no PII in logs** (ids, not e-mails/addresses) |
  | E-mail provider | suppression list keeps the address (legitimate interest – never e-mail again) |
  | Backups | cannot be edited → expire by retention (daily backups / PITR window) – stated in the privacy policy; **deletion log** of erased user ids re-applied if a backup is ever restored |
- **Cannot be deleted:** accounting/tax records (invoices, payments, orders) – legal obligation
  (GDPR Art. 17(3)(b); e.g. in Slovakia accounting documents are kept for years – exact period to
  confirm with an accountant); records needed for disputes/chargebacks during their window.
  → **pseudonymise** (order linked to a tombstone user, invoice keeps only what the law requires),
  **retention policy** with a scheduled pg_cron job deleting when the period ends.

<a id="l5"></a>
**L5 – Why Supabase and not Firebase/Firestore**
| | Firestore | Supabase (Postgres) |
|---|---|---|
| Stock transactions | optimistic txns with retries; **sustained writes to one document ~1/s** → hot box at a Saturday peak = contention | row lock, hundreds of atomic UPDATEs/s (Q1, Q3) |
| Joins | none → denormalise farmer page, order history; fan-out writes | SQL joins, views |
| Search (US 8), radius (riders) | no full-text → Algolia/Typesense extension; geo via geohash libraries | Postgres FTS + PostGIS built-in |
| Security rules | own DSL, limited document reads per rule → "bought this box?" needs denormalised flags | RLS in SQL, can query anything, pgTAP-testable |
| Pricing | **per read/write/delete** → browsing + listeners make the bill unpredictable | per resources (compute, storage, egress) |
| Firebase strengths | excellent mobile offline sync (riders!), FCM integration, longer-running Cloud Functions | – |
→ **Supabase**: the core of E-Farmers is relational and transactional.

<a id="l6"></a>
**L6 – Critical question: what is left of the BaaS promise?**
- **Real savings that remain:**
  - Auth (e-mail + OAuth + verification + password reset + linking) – weeks of work.
  - Storage with RLS, CDN, image transformations.
  - Realtime with authorization – A1 would need its own WebSocket server.
  - Managed Postgres with backups, dashboard, logs – no servers.
  - Auto-generated API for plain reads/CRUD (catalog browsing, profiles, comments, subscriptions).
- **What evaporated:**
  - "No backend code" – the core (checkout, bookings, dispatch, payments, timers, fan-out) is the same
    amount of logic, now in **PL/pgSQL + Deno with weaker tooling** (debugging, refactoring, types,
    libraries, review – S3).
  - Background-processing reliability we built by hand (lease rows, token bucket, cron-driven workers –
    S4); an A1 job library gives concurrency limits, rate limits and retries out of the box.
  - `api_v1` is an API layer, just written in SQL (S2).
  - **Inverted security model:** A1 = deny by default (only the backend touches the DB); A3 = everything
    not locked down is exposed → larger attack surface, one forgotten policy = data leak (S1, S2).
- **Is A3 just A1 in SQL?** For the **core domain – largely yes**: same data model, same atomic
  patterns, same Stripe design (A3.5 list). That is itself a finding: **the hard parts of E-Farmers are
  domain problems, not infrastructure**, and no platform removes them.
- **A3 better than A1:** faster to MVP (auth, storage, realtime, CRUD, admin data view ready), less
  ops, similar or lower cost at our scale, realtime features for riders/notifications out of the box.
- **A3 worse than A1:** business logic in PL/pgSQL (skills, testing, review), security surface (RLS
  everywhere), hand-made workarounds for background work, platform limits, lock-in, harder debugging.
- **Observation for Task 2 (ADR):** a **hybrid** is possible – A1 monolith for all domain logic and
  writes, using Supabase only as *managed Postgres + Auth + Storage (+ Realtime for signals)*; the
  frontend talks to Supabase only for auth/files, never for domain writes. Keeps the real savings,
  drops the PL/pgSQL core and the exposed-DB security model.

<a id="a3-final"></a>
### Architecture 3 – Final assessment (after the whole discussion)

**Strengths**
- Fastest path to a working MVP: Auth with OAuth, Storage, Realtime, auto-API for CRUD built in (L6).
- One database again → order + stock in one transaction; all A1 consistency patterns carry over (A3.3, A3.5).
- No servers to operate; lowest infra cost at our scale (L2).
- Postgres-based → relational model, FTS, PostGIS, RLS testable with pgTAP; much better fit than Firestore (L5).
- Open source core → exit paths exist (self-host or A1, passwords portable) (L1).

**Weaknesses**
- Core business logic in PL/pgSQL + Deno: weaker tooling for testing, debugging, review (S3).
- Exposed database: RLS + grants + `private` schema + event trigger + linter must all be right (A3.2, S1).
- Schema becomes the public API → versioned `api_v*` schema = own API layer in SQL (S2).
- No long-running process → lease rows, token bucket, cron-driven workers built by hand (S4, A3.4).
- Realtime is non-durable → "signal + fetch" needed everywhere (L3).

**Risks**
1. **Security misconfiguration** – one table/function/view exposed without the right policy = data leak
   or privilege escalation (`SECURITY DEFINER`, `search_path`, security-definer views).
2. **Logic sprawl in SQL** – PL/pgSQL functions grow, few developers can safely change them.
3. **Platform limits and pricing changes** (Edge Function CPU/wall limits, quotas) outside our control.
4. **Lock-in to the architectural style** – exit B costs ~2–4 developer-months (L1).
5. **GDPR across many places** (Auth, Storage, Stripe, backups, logs) – erasure process must be built
   and tested (L4).

**Verdict:** a strong choice for a **fast prototype/MVP with a small team that knows Postgres well**.
For E-Farmers' money-heavy core, keeping the domain logic in a real application language (A1) is safer;
the **hybrid (A1 + Supabase as managed Postgres/Auth/Storage)** is a serious candidate for the ADR.

## Comparison & conclusion

<a id="h1"></a>
### H1 – Critique of the hybrid (A1 + Supabase as managed Postgres/Auth/Storage)
*Student: why not plain EU managed Postgres + a proven auth library + S3-compatible storage?*

- **What Supabase really adds in the hybrid:**
  - Hosted auth server: e-mail verification, password reset, magic links, OAuth providers, MFA,
    rate limiting, e-mail templates – configured, not coded.
  - Storage with image transformations, signed URLs, CDN.
  - Realtime (Broadcast from DB triggers, Realtime Authorization) – A1 would need its own SSE/WebSocket endpoint.
  - One dashboard; `pg_cron`/`pgmq` available (not on every managed Postgres); Branching.
- **What it costs:**
  - **Two identity worlds:** `auth.users` (Supabase) vs. our users and profiles → synchronisation.
  - Backend must verify a foreign JWT; login depends on an external service (Supabase Auth down ⇒
    nobody logs in).
  - The biggest Supabase feature (PostgREST auto-API) is **switched off** – we pay for a platform and use
    a third of it; US vendor (DPA + SCCs) vs. an EU provider.
- **Verifying the JWT in the monolith:** projects with **asymmetric JWT signing keys** publish a JWKS
  (`https://<project>.supabase.co/auth/v1/.well-known/jwks.json`) → backend verifies the signature
  locally with cached keys; legacy projects use a shared HS256 secret (secret in backend config).
  Always check `iss`, `aud = authenticated`, `exp`; `sub` = user id. Roles **not** taken from the JWT –
  read from our tables (no stale-role problem, A2.6).
- **Keeping `auth.users` and our tables in sync:** same database → real FK
  `app.user_account(id PK REFERENCES auth.users(id))`, created by an `AFTER INSERT ON auth.users`
  trigger (documented Supabase pattern) **in the sign-up transaction** → never out of sync.
  E-mail change → `AFTER UPDATE OF email` trigger. Farmer/rider profiles (Q12) reference `user_account`.
  Deletion only via our `delete_account` process (pseudonymise orders first, then
  `auth.admin.deleteUser`, L4). Caveat: triggers on the managed `auth` schema must stay minimal –
  a failing trigger blocks all sign-ups.
- **RLS when only the backend touches the DB:**
  - **Mandatory:** turn the Data API (PostgREST) off / expose no schema and revoke all grants from
    `anon` and `authenticated` → the database is not reachable from browsers at all. This, not RLS, is
    the real barrier in the hybrid.
  - RLS as a general mechanism: **dropped** – backend connects as its own role; ownership checks in the
    data layer + tests (Q12) as in A1.
  - Optional defence in depth only on the most sensitive tables (`delivery_dropoff`, orders,
    payout data): backend runs `SET LOCAL app.user_id = …` per transaction, policies use it. Cost: every
    query/transaction must set it; jobs need a bypass role. Decide during implementation.
- **Verdict of H1:** the hybrid saves mainly auth server + realtime + image pipeline. With a framework
  that has **mature built-in auth/OAuth** (Django + allauth, Rails + Devise, Spring Security, …) these
  savings shrink to days and the hybrid's costs (two identity worlds, foreign JWT, external login
  dependency) dominate. → **Plain EU managed services are preferred; the hybrid stays a valid
  alternative** if the chosen stack lacks good auth or realtime is needed early.

<a id="c1"></a>
### C1 – Comparison table
*Costs are rough order-of-magnitude estimates based on unofficial/third-party pricing summaries – not quotes.*

| Criterion | A1 Modular monolith (plain EU managed services) | A2 Microservices, event-driven | A3 Supabase BaaS (auto-API + RLS + Edge Functions) | Hybrid (A1 + Supabase Postgres/Auth/Storage) |
|---|---|---|---|---|
| **Money & stock consistency** | ★★★ one ACID txn; atomic sorted UPDATEs | ★ saga, compensations, tombstones, timeouts | ★★★ one DB again (txn in RPC) | ★★★ as A1 |
| **Security model** | ★★★ deny by default, only backend touches DB | ★★ per-service checks, JWT + local state | ★ exposed DB, RLS + grants + `private` + linter must all be right | ★★★ as A1 (Data API off) |
| **MVP speed** | ★★ build auth (library), realtime (SSE) | ★ plumbing first | ★★★ auth/storage/realtime/CRUD ready | ★★★ auth/storage ready, logic as A1 |
| **Infra cost / month** (our scale → 10×) | ~€150–300 → €300–600 | ~€500–1 200 → €1 000–2 000 | ~€100–250 → €250–500 | ~€100–250 → €250–500 |
| **People / team** | 2–4 devs | 5–8 devs incl. platform/DevOps | 2–3 devs with strong Postgres/SQL | 2–4 devs |
| **Ops burden** | ★★★ low: 3 process types, 1 DB | ★ high: ~9 deployables, broker, IdP, tracing, DLQ | ★★★ lowest (no servers) but hand-made workers | ★★★ low |
| **Scaling** | ★★ whole app; enough for 10× peaks; hot row understood | ★★★ per service (but shared DB cluster) | ★★ platform tiers; Edge limits | ★★ as A1 |
| **Testability / debugging** | ★★★ normal language tooling, fake clock | ★★ contract tests, tracing, heavy local env | ★ pgTAP, PL/pgSQL, weak debugging | ★★★ as A1 |
| **Lock-in** | ★★★ minimal (standard Postgres, S3 API) | ★★★ minimal (but RabbitMQ/IdP choice) | ★ architectural style; exit 2–4 dev-months | ★★ Auth + Storage tied to Supabase |
| **Growth path** | ★★★ strangler to A2 (Notification first), seams ready (modules, outbox) | already there | ★ → A1 rewrite of API/frontend data layer | ★★★ as A1; can drop Supabase pieces one by one |

(★ = weak, ★★ = acceptable, ★★★ = strong for E-Farmers' context)

<a id="c2"></a>
### C2 – Recommendation
**Architecture 1 – modular monolith**, on plain EU managed services:
managed PostgreSQL (EU region) + PostgreSQL-backed job queue, S3-compatible object storage + CDN,
framework's proven auth library with OAuth, SSE endpoint for notification center and rider offers,
Stripe Connect Express. Built with **A2-ready seams**: schema per module, public module APIs checked
in CI (Q8), outbox via job queue (Q9), Notification as the first candidate for extraction.

**Why:**
- The hard parts of E-Farmers are **domain problems** – stock under contention, payments with Connect,
  bookings, dispatch, timers (L6). A1 solves them most simply: one transaction, normal language,
  normal tooling, deny-by-default security.
- Expected scale incl. 10× peaks fits easily (Q3); the bottleneck (hot row) is about lock duration, not
  architecture.
- Smallest team and ops burden that still keeps full control; minimal lock-in; clear path to A2.

**I would change the recommendation if:**
| Condition | Then |
|---|---|
| 1–2 developers, MVP needed within weeks, team strong in Postgres/SQL, mostly CRUD validation of the idea | **A3** for the prototype (accepting a later rewrite of the core) |
| Chosen stack lacks mature auth/OAuth, or realtime is central from day one | **Hybrid** |
| ~15+ developers / 3+ teams blocking each other; diverging scaling (national scale, live GPS tracking); regulatory isolation of payments | **A2 incrementally** (strangler: Notification → Payment → Delivery) |
| Platform must hold funds itself / become a payment institution | revisit Q5 first – it changes the payment design in every architecture |

<a id="c3"></a>
### C3 – Decisions valid for any architecture
| Area | Decision | Ref. |
|---|---|---|
| Marketplace money | Stripe Connect **Express**, **separate charges and transfers**; platform never holds third-party funds long | Q5, Q7 |
| Transfer timing | farmer on hand-over (`PICKED_UP` / self-pickup), rider on `DELIVERED` (+24 h confirm / auto-confirm); `source_transaction`, `transfer_group` | Q7 |
| Bookings | SetupIntent at booking → off-session charge on accept → 24 h payment-link fallback (SCA); farmer must answer within 48 h | Q2 |
| Payment methods | instant methods only for cart checkout; SEPA Direct Debit only for bookings; **no manual capture** | Q6 |
| Checkout timers | one timer: session `expires_at` = reservation TTL (30 min); release stock **only after the session is dead**; never on our own clock | Q4, Q6, F1 |
| Stock | reserve at checkout (cart = wish list); atomic conditional UPDATE `qty >= n`; **sorted lock order**; all-or-nothing; **no network I/O inside the stock txn** | Q1, Q3 |
| Box expiry | derived from `expires_at` (last sellable moment), no job; cannot buy a box expiring during checkout | Q11 |
| Rider assignment | atomic `UPDATE … WHERE rider_id IS NULL`; max 1 active delivery in MVP (partial unique index), counter + CHECK later | Delivery model, Q10 |
| Delivery model | one delivery per `FarmerOrder`; dispatch with radius widening and terminal give-up; pickup timeout | Delivery model, Q11 |
| Data model | `Order → FarmerOrder → OrderItem` with price/name snapshots; roles as 1:1 profile tables; one `payout_account` per person | Q5, Q8, Q12 |
| Authorization | ownership enforced in the data-access query itself (`WHERE … AND owner = actor`), 404 not 403; roles from DB, not from token | Q12, A2.6 |
| Multi-source permissions | store each fact with its source version, compute the permission (`can_publish`) | F6 |
| Timers | delayed jobs / sweeps as **conditional state transitions** (safe to run twice); time passed as parameter for tests | Q11, S3 |
| Events | **transactional outbox** + idempotent consumers, at-least-once; state-transfer events with versions | Q9, F3, F6 |
| Idempotency | Stripe idempotency keys (`order_id`, `farmer_order_id + type`); webhook event id dedup | Q4, A2.5, A3.5 |
| Account linking | auto-link only if both e-mails verified; pre-account-takeover mitigation | Q13 |
| Notifications | `notification_delivery` per recipient/channel, per-recipient retry, rate limit, digest, shuffled recipients; FCM = N requests | Q14, S4 |
| Operations | admin back-office from day one; nightly reconciliation Stripe ↔ DB; state history tables; alerts on stuck states | A1 final, F2, T9 |
| GDPR | EU region; erasure process across all stores; pseudonymise accounting records; no PII in logs | L4 |

<a id="c4"></a>
### C4 – Open questions and assumptions to verify
**With the client / product owner**
1. Scale assumptions (users, farmers, 10× peaks) – confirm with real expectations.
2. Bookings: how far ahead; does acceptance commit farm capacity; charge on acceptance or closer to
   harvest date?
3. Box expiry semantics – is `expires_at` "last sellable moment", who sets it?
4. Delivery: pricing formula (per km?), radius, rider vetting, self-pickup option, later bundling,
   may a rider deliver their own order / may a farmer buy own boxes?
5. Commission model: platform fee, who pays Stripe fees, delivery fee split.
6. Refund / complaint policy and chargeback liability (platform is liable with Express accounts).
7. Badges (US 28) – criteria undefined.
8. Seasonal calendar (US 7) – who maintains it (farmers vs. platform)?
9. Comments – moderation, one per purchase OK?
10. Channels: in-app / push / e-mail; is a **mobile app** planned (affects API versioning, S2)?
11. Countries, currency, payment methods; who issues invoices, VAT treatment.

**Legal / compliance (not legal advice)**
12. Confirm that Connect separate charges and transfers keeps the platform outside PSD2 licensing.
13. Accounting retention periods and GDPR retention policy; DPAs with all sub-processors.

**During implementation**
14. Technology stack / language not chosen yet → determines auth library, job queue library,
    architecture-test tool.
15. Stripe details: Connect Express availability for SK/EU farmers and riders; limits on delaying
    transfers in separate charges and transfers; Checkout `expires_at` range; idempotency-key lifetime.
16. E-mail provider: batch API and idempotency-key support (decides duplicate handling, Q14).
17. Geocoding provider and cost; haversine × factor accuracy acceptable?
18. Load test of the hot-row scenario (one box, 10× peak) to confirm Q3.
19. If A3/hybrid were chosen: Supabase account-linking behaviour for unverified e-mails (A3.1),
    Broadcast-on-rollback behaviour (L3), current pricing and Edge Function limits.
