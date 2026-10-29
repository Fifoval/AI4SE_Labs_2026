# Failure question bank

Use in Round 2 (and to front-load Round 1). Pick what applies to the system; present the 5–7 most
dangerous ones with fixes, list the rest in one line. Format: **Question** → *reveals*.
These are generic technical traps – adapt them to the system's own concepts.

## A. Cross-cutting (any style)

### Concurrency and invariants
- Two requests take the last unit at the same time – is the check-then-act atomic (conditional
  `UPDATE … WHERE qty >= n`, unique constraint)? → *overselling / double allocation.*
- Two multi-item requests lock the same rows in opposite order? → *deadlocks; need a global lock order.*
- 2 of 3 items available – partial success or all-or-nothing? → *surprising partial orders, payment mismatch.*
- One extremely popular row at a peak – how long is its lock held; is there any network call inside the
  transaction? → *hot-row throughput collapse.*
- A counter must stay ≤ N under concurrency (e.g. max N active tasks per worker) – unique index can't
  count; lock row, counter + CHECK, or SERIALIZABLE (retry cost)? → *limit violations (write skew).*
- **Any network call (payment provider, e-mail, push, HTTP) while a DB transaction / row lock is open?**
  A slow provider then holds connections and locks for its whole timeout; webhooks and user requests
  block on the same rows; the pool runs dry and the whole site degrades. Claim (short tx) → call (no tx)
  → apply a terminal fact (short tx). → *one external outage becomes a database outage.*
- A user edits a quantity/price form while sales happen – absolute value or delta? Price changing during
  checkout – snapshot? Delete of a referenced item – withdraw instead? → *lost updates, orphaned orders.*

### External payment / checkout providers
- Our reservation TTL and the provider's checkout-session expiry are two clocks – can the customer pay
  after we released the reservation? Release only after the provider session is dead. → *paid without goods.*
- Is the browser redirect or the webhook the source of truth for "paid"? → *fake/lost payments.*
- Webhook: signature verified on the **raw body**? Duplicate events idempotent (event id)? → *spoofing, double effects.*
- Asynchronous payment methods (bank debits) stay "processing" for days – hold scarce or
  time-bound inventory (tickets for tonight, a room for tomorrow) that long or restrict methods? → *blocked or oversold inventory.*
- Pre-authorisation/hold validity (often ~days) vs. long lead times of deferred purchases – save the
  payment method and charge later instead? Off-session charge needs strong customer authentication → fallback? [verify limits]
- Marketplace: does the platform collect money and pay sellers itself? → *may require a payment-services
  licence (e.g. PSD2 in the EU), AML/KYC; prefer the provider's connected-accounts model.* [not legal advice]
- Multi-seller cart: does the provider's charge type support several recipients per payment? → *wrong charge model.*
- When are sellers / service workers paid – before fulfilment (reversals, platform liable for negative
  balances) or after (how long may funds sit on the platform)? → *liability, regulatory exposure.*
  Tie each party's payout to **its own** obligation (handover vs. delivery), check the provider's maximum
  holding period [verify] and cap advance-reservation horizons below it. → *unfair cash flow, held funds.*
- Provider session/checkout minimum and maximum lifetime [verify] – is the reservation TTL derived from
  it? Release only after the provider confirms the session is dead (expire it, then read a terminal state).
  → *payment for already released stock.*
- Session/payment creation outcome unknown (timeout) – retry with the same idempotency key; never release
  on "unknown". → *orphaned sessions that can still be paid.*
- Idempotency keys expire at the provider [verify] – what does a retry after the window do (list before
  create)? → *double refunds/transfers.*
- Delayed payment methods (bank debits) – besides "processing" for days: no-reason dispute windows after the
  goods were delivered [verify] – who carries that loss? → *losses after fulfilment.*
- Provider outage recovery – a burst of retries, expiries and new checkouts shares one rate limit:
  shared token bucket with priorities, circuit breaker. → *self-inflicted 429s on customer checkouts.*

### Time-driven behaviour
- List every deadline/timer: trigger, owner, action. → *missing or doubly-owned timers.*
- The job runs twice or late (two instances, retry) – is it a conditional state transition
  (`UPDATE … WHERE status = 'PENDING' AND deadline <= now`)? → *double side effects.*
- Must "expired" be stored, or can it be derived from a timestamp in queries? → *needless jobs.*
- How is time tested (time as a parameter / fake clock; `now()` constant inside a DB transaction)? → *untestable timers.*
- Is every timeout derived from a domain constraint (event start, check-in date, sale end, legal deadline)? → *absurd TTLs.*
- Is there a deadline for **every human or external obligation after payment** (seller hands over, worker
  finishes, courier delivers)? A paid state without a deadline keeps money held forever. → *stuck paid orders.*
- A timer that cancels another component's step: does it decide from a read model / missing event, or ask
  the owner? → *refund for goods already picked up.*

### Operations without an ops person
- Who reacts to a stuck flow at night? Which **automatic** actions are safe – only re-sending the same
  intent or applying a terminal fact from its owner; never deciding money/stock from a timeout. → *stock
  blocked all weekend, or wrong automatic refunds.*
- Alert routing by risk: page only for "customer charged but order not confirmed", the rest next morning
  with an automatic message to the affected party. → *alert fatigue or ignored money incidents.*
- Background work with no process that visibly crashes (cron → function, fire-and-forget HTTP): heartbeat
  per worker type + an **external** monitor. → *money flows stop silently while the site looks healthy.*

### Asynchronous processing and messaging
- Commit succeeds, process crashes before enqueueing the job/event? → *lost side effects → transactional outbox.*
- At-least-once delivery – is every consumer idempotent (inbox table / unique keys)? → *duplicate effects.*
- ACK before or after commit? Crash in between? → *lost messages (ACK first) vs. safe redelivery (ACK after).*
- A handler keeps failing (bug) → dead-letter queue: who is alerted, how are messages re-driven, is
  re-driving safe (old messages vs. already-compensated state)? → *silent stuck flows.*
- Workers triggered asynchronously (cron firing HTTP) – can runs overlap? How are concurrency and the
  provider's rate limit bounded (leases, token bucket)? → *rate-limit violations.*
- Fan-out to N recipients via an external provider – per-recipient retry, duplicates, batch support
  (verify: batch endpoints get deprecated), order/fairness when the notification announces scarce items? → *spam, unfair access.*
- Worker killed mid-batch (CPU/wall-clock limit, crash) before acknowledging – per-item idempotency and
  "mark then send" for notifications vs. "call with key then record" for money. → *duplicate pushes or lost payouts.*
- Push on mobile web is only a signal (platform restrictions [verify], reliability) – is the offer/state
  durable and re-fetched on reconnect, with a timeout and re-offer? → *missed time-critical offers.*

### Identity and authorization
- One account, several roles – how are roles stored and checked? → *privilege confusion.*
- Ownership enforced in the query (`WHERE id = ? AND owner = :actor`) or only in a controller? → *IDOR.*
- 403 vs. 404 for others' resources? → *existence leaks.*
- Role changed but the access token still carries the old role – escalation (missing privilege for a
  while) vs. revocation (privilege kept too long)? → *stale-token abuse.*
- OAuth login with an e-mail that matches an existing unverified password account – auto-link? → *pre-account takeover.*
- Provider without verified e-mail? → *account hijack via linking.*

### Data, privacy, compliance
- Right to erasure across all stores: auth, DB, file storage (deleting a metadata row may not delete the
  file), backups, logs, payment provider, e-mail suppression lists? → *incomplete erasure.*
- Records that must be kept (accounting) – pseudonymise instead of delete? → *legal conflict.*
- Region of data and of compute, processors and DPAs; PII in logs? → *compliance gaps.* [not legal advice]

### Operations, cost, team
- What exactly is deployed (process types, stores, brokers, external services)? → *hidden ops burden.*
- What will hurt after one year (support cases, stuck states, table bloat, migrations at peak)? → *unplanned cost.*
- Reconciliation with external systems (payments) and an admin back-office from day one? → *money drift.*
- External service outage – how does the system degrade? → *cascading failure.*
- Relative infra cost, number of pipelines, team size needed; when does this style pay off? → *over-engineering.*

## B. Monolith / modular monolith
- How are module boundaries enforced (schema per module, public `api` package, CI import rules, no
  cross-schema foreign keys, no cross-schema queries)? → *boundary erosion.*
- Which flows need data from another module's schema (e.g. a fan-out query joining another module's
  table)? Do they go through that module's API? → *hidden coupling contradicting the rules.*
- Deliberate exceptions (shared transaction across modules) – documented and minimal? → *uncontrolled coupling.*
- One deploy for everything – blast radius of a small change? → *outage from unrelated features.*
- Background jobs compete with requests for the same DB – separate queues/concurrency? → *noisy neighbour.*
- Which module would be extracted first and why (pure event consumer, isolated load)? → *no growth path.*

## C. Microservices / event-driven
- Compensation overtakes the action (cancel processed before a delayed reserve) – tombstones keyed by
  the business id? → *resources reserved for cancelled flows.*
- Saga step timeouts – who guards them, which steps must never be cancelled by our own clock (payment)? → *money races.*
  Cancel by **asking the owner** (cancel command + tombstone at the owner, exclusive final outcome). → *paid after cancel.*
- Payout and reversal commands arriving out of order – ledger per business id with tombstones. → *paid despite an upheld claim.*
- Broker outage – outbox age as a health signal that stops accepting new work that would hold resources. → *resources held for doomed flows.*
- Orchestration or choreography – where is the current state of a flow visible? → *untraceable flows.*
- Pivot step (after payment) – only forward recovery? → *impossible compensations.*
- Safety TTL on reservations when a compensation is stuck – value derived from the domain? → *blocked or oversold items.*
- Orchestrator crashes mid-flow – is all saga state persisted (no in-memory state)? → *lost flows.*
- Separate databases on one shared cluster – what independence do we really get? → *false isolation.*
- Pages combining data of several services – API composition (degradation when one is down) or read
  model (staleness)? → *broken pages.*
- State derived from events of several services in any order – per-source versions, state-transfer
  events? → *wrong permissions.*
- Event schema evolution – additive changes, expand/contract renames, versioned types, contract tests,
  support period ≥ max message age? → *consumer breakage.*
- "I paid and don't see my order" – correlation id, tracing, saga timeline, DLQ check? → *undebuggable incidents.*
- Local development of N services + broker + IdP? → *developer productivity collapse.*
- Broker choice proportional to volume (log-based vs. queue vs. managed)? → *ops overkill.*
- Distributed monolith (services that must deploy together)? → *all costs, no benefits.*

## D. Serverless / BaaS (client talks to the database)
- Row-level security is the only barrier – what happens to a new table without RLS (default grants to
  anonymous/authenticated roles)? Can a guard (event trigger, linter in CI) be used on the managed
  platform? [verify] → *public read/write data.*
- Views run with the owner's rights and bypass RLS unless invoker rights are set? → *data leak via views.*
- Column privileges are per role, not per user – data visible only to some users of the same role must
  be split into another table. → *sensitive columns exposed.*
- Functions in exposed schemas are executable by PUBLIC by default; privileged (security-definer)
  functions callable via RPC? `search_path` pinned? → *privilege escalation.*
- The schema becomes the public API – old mobile clients for months: versioned API schema of views/RPCs?
  Is that just an API layer in SQL? → *breaking clients / lost promise.*
- Business logic in SQL – tests under different roles/claims (denial = 0 rows, not an error), time as a
  parameter, code review of append-only migrations, debugging without a debugger? → *untested core.*
- Local vs. production differences (auth e-mails/SMTP limits, OAuth redirects, function URLs,
  scheduler → function calls). → *works locally only.*
- Function limits (CPU/wall clock/memory) vs. long jobs – batching with the queue as checkpoint? [verify] → *timeouts.*
- Secrets for internal calls – least privilege, not the full service key? → *key leak = full access.*
- Functions running with the service key take the user id from the request body instead of the verified
  token? → *any user acts as any other (IDOR with RLS bypassed).*
- RLS limits **which rows**, not **which values** – does the client still have UPDATE grants on tables with
  invariants? Invariants belong in functions; the client gets no write grant there. → *oversell through a "secure" table.*
- The auto-generated API lets any client compose expensive queries (filters, sorts, embeds) on the only
  database; per-row policy cost (`auth.uid()` per row [verify]). → *query-cost DoS against checkout.*
- Realtime is non-durable – signal + fetch after reconnect? Messages sent on rollback? Private channel
  authorization? → *missed or leaked updates.*
- Lock-in and exit plan (self-host vs. rewrite), portability of password hashes, effort estimate. → *trapped.*
- Pricing drivers (MAU, egress, connections, invocations) and where it becomes expensive. [verify] → *bill shock.*
- Alternative BaaS with a document database – transactions on hot documents, joins, search, per-read
  pricing? → *wrong platform.*
- Devil's advocate: after all the workarounds, what is left of "faster and less code"? → *false premise.*

## E. Hybrids (e.g. own backend + BaaS pieces)
- Two identity stores to keep in sync; how is the foreign token verified (JWKS / shared secret)? → *drift, auth bugs.*
- Login depends on an external service – availability? → *nobody can log in.*
- Paying for a platform whose main feature is switched off; vendor region/DPA. → *cost without benefit.*
- Is the exposed database surface really switched off (API off, grants revoked)? → *accidental exposure.*
