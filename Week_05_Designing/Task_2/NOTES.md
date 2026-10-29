# Task 2 – ADR discussion notes (E-Farmers)

Running notes from creating and refining the Architecture Decision Record.
Not a 1:1 transcript – requests, critique, changes and their reasons.

- Source of truth: [../Task_1/NOTES.md](../Task_1/NOTES.md) (no new decisions may be invented).
- Output: [ADR-001-architecture-style.md](ADR-001-architecture-style.md)

---

## Student's brief (round 0)
- One ADR for the main decision: **architecture style** (options A1, A2, A3, hybrid).
- Architecture-independent decisions (Task 1, C3) → **not in the ADR body**, only as a list of related
  decisions that deserve their own ADRs.
- Reader: new developer / tech lead who was not in the discussion → must understand *why* and *when to
  revisit*.
- Short: ~2–4 pages, English. Missing information → open question, not invention.
- Assistant to state up front: chosen format and why, what was deliberately left out, whether a table
  or diagram was added.

## Version 1 (assistant)

**Format: MADR (Markdown Architectural Decision Records)** rather than Michael Nygard's template.
- Nygard (Title, Status, Context, Decision, Consequences) is ideal for a short single-path decision,
  but has no place for *considered options* and their comparison – which is the core of this decision
  (4 options discussed in depth).
- MADR adds **Decision drivers**, **Considered options**, **Pros and cons of the options** and
  **Confirmation** – exactly what a reader who missed the discussion needs to see *why the others lost*.
- Added beyond plain MADR: a **"When to revisit"** table (student explicitly asked for re-evaluation
  conditions) and **Related decisions** list.

**Deliberately left out (and why)**
- All implementation detail: SQL, Stripe flows, saga steps, RLS policies, timer table T1–T9 → belongs to
  the related ADRs / design docs; would blow the 2–4 page limit.
- A2 failure-scenario analysis (F1–F9) and A3 security/dev rounds (S1–S4, L1–L6) → condensed to one or
  two cons per option + link to Task 1 notes.
- Cost line items and pricing sources → only the summary row with a "rough, unofficial" disclaimer.
- GDPR details → one related-ADR pointer (ADR-009).
- Firebase comparison → one clause in A3 pros (it was a side question, not an option).
- No new decisions: technology stack stays open (it was never decided in Task 1).

**Overview table / diagram**
- **Comparison table** (drivers × options, ★ ratings + cost row): yes – 4 options × 7 drivers is
  unreadable as prose; the table is the fastest way for a newcomer to see the trade-off.
- **Diagram**: yes, one small Mermaid diagram of the *chosen* architecture only (processes, DB, external
  services) – renders on GitHub, shows what "monolith with 3 process types" means physically.
  No diagrams of rejected options (they would only add length).

**Structure of v1:** metadata table → Context and problem statement → Decision drivers (D1–D7, ranked)
→ Considered options → Decision outcome (what it includes, diagram, consequences, confirmation, when to
revisit) → Pros and cons (comparison table + per-option bullets) → Related decisions (ADR-002…009) →
Open questions → More information.

**Points the assistant considers uncertain (for the student's review)**
- Status set to **Accepted** with the student as decider – change to *Proposed* if it should await
  review.
- Ranking of decision drivers (D1 > D2 > D3 …) is an interpretation of the Task 1 discussion, not an
  explicit decision there.
- Numbering of related ADRs (002–009) is a proposal only.

## Review round 1 (student) → Version 2

**Student's answers to the uncertain points**
- Status → **Proposed** during review; *Accepted* + date only in the final version.
  Deciders: Filip; **Consulted:** coding assistant.
- Driver order must match what actually decided in Task 1 C2. Student's order:
  (1) money & stock correctness, (2) simplicity for a small team + delivery speed, (3) security model –
  DB only via backend, (4) ops & cost, (5) testability, (6) path to services, (7) scaling + lock-in –
  explicitly lowest at regional scale.
- Related ADR numbering OK.

**Assistant's original order (v1) and why it differed**
- v1: D1 consistency → D2 secure by default → D3 ops & cost → D4 time to MVP → D5 testability →
  D6 growth path → D7 lock-in.
- Differences: (a) security was 2nd and "simplicity/speed" 4th – I weighted the A3 rejection (exposed DB)
  most heavily; but C2's actual reasoning is "A1 solves the domain problems *most simply*" – simplicity
  is the core argument, security a supporting one. (b) **Scaling was not an explicit driver** at all in
  v1, although discussed (Q3). → **Student's order adopted** (D7 = scaling + lock-in).

**Requested changes and what was done**
1. **TL;DR** (3–4 sentences) at the top: decision, main reason, main revisit trigger. → Added as a
   quote block under the metadata.
2. **Star table vs. decision – contradiction check.** Assistant recomputed v1 stars:
   - Unweighted sum: **A1 = 20, Hybrid = 20**, A3 = 13, A2 ≈ 10 → tie.
   - Weighted by v1 driver order (weights 7…1): **A1 = 80, Hybrid = 83** → **the hybrid "won"** –
     v1 table contradicted the decision. Student was right.
   - Root cause: v1 rated the hybrid ★★★ on MVP speed and never captured its costs from H1 (two
     identity stores, foreign JWT, login depending on an external service). With mature framework auth
     the hybrid's saving is "days" (H1), so it is not faster than A1, and it is more complex.
   - **Fix:** ratings re-derived from Task 1 (no new facts): hybrid D2 = *Acceptable* (second identity
     store + foreign JWT), A1 D2 = *Strong*; added explicit scaling to D7.
   - **Format chosen: verbal ratings (Strong / Acceptable / Weak) + one-sentence reason in each cell.**
     Why: stars invite summing (exactly the trap found here) and need a legend; words + reason are
     readable without a legend and explain themselves to a newcomer. Added a rule below the table:
     *ratings are not additive, driver order decides* + "A1 is the only option Strong in all top five
     drivers".
3. **Prices:** euro amounts removed. D4 row now relative: A2 infra ≈ 3–5× A1 and team ≈ 2× A1;
   A3 ≈ A1 or lower; hybrid ≈ A1; footnote with estimate date (October 2026), unofficial sources and
   links to Task 1 F9/L2/C1.
4. **Duplicates:** v1 had A1's pros/cons twice (Decision outcome → Consequences *and* section
   "Pros and cons of the options → A1"), and the reasons for the decision both in the outcome text and
   in the table. → A1 subsection removed from the options section (pointer to Consequences); section
   renamed **"Why the other options were rejected"** and keeps only details *not* in the table;
   the outcome text now refers to the comparison instead of repeating it. "Pro" lists of rejected
   options dropped (they were in the table).
5. **Assumptions** as an explicit numbered list in Context (regional scale, 10× peaks, team 2–4,
   + Stripe Connect / no own holding of funds – taken from Task 1 C2 revisit conditions) with the note
   "if any stops holding, revisit". "When to revisit" table now references which assumption breaks.

**Other small changes in v2**
- Comparison table moved up next to Considered options (it is the core argument; reader sees it before
  the outcome).
- Negative consequence added: auth and realtime must be built from libraries (it was an A1 con in v1's
  options section – moved, not lost).
- Open question about cost verification dropped (covered by the footnote).

## Review round 2 (student) → Version 3

**0) Inconsistency found by the student – hybrid ratings vs. H1**
- v2 claimed "the hybrid differs from A1 only in D2", but H1 lists further hybrid costs: **login depends
  on an external service**, **US vendor**, **we use ~⅓ of the platform**. v2 ignored them.
- Re-checked against H1 → corrected:
  - **D4 hybrid: Strong → Acceptable** (infra ≈ A1, but external auth = availability dependency; paying
    for an unused platform).
  - **D7 hybrid: Acceptable → "Acceptable, weaker than A1"** (Auth + Storage tied to one US vendor; exit
    feasible thanks to portable bcrypt hashes – L1).
- Added the **tie-break rule** under the table: compare driver by driver in priority order, the first
  driver with a difference decides (lexicographic). Hybrid vs. A1: tie at D1 → A1 wins at D2.
  Also stated where A3 (D2, D3) and A2 (D1) lose.

**1) Second diagram – module view**
- Added "Module view – why it is *modular*": 8 modules with owned schema and main tables; solid arrows =
  calls through `api/`, dashed = domain events via job queue (outbox), **bold arrow = the only deliberate
  exception: `catalog.api.reserve_stock` runs in the caller's transaction** (Task 1 Q8). Rule "any
  dependency not drawn is forbidden" + no cross-schema FKs (price snapshots).
- Both diagrams got headings stating the level: **Deployment view** (processes/infrastructure → why
  monolith) vs. **Module view** (boundaries → why modular).
- Kept **8 modules incl. `booking`** as in Task 1 A1 (student's list had 7 without booking and named
  engagement "community"; booking was a separate module in A1, merged with ordering only in A2) → label
  "engagement – community".
- Arrows derived from Task 1 flows: ordering→catalog (Q8), ordering→payment (checkout session, Q4),
  booking→ordering/payment (Q2), engagement→ordering (comments, Q12), catalog⇢notification
  (InsertionPublished, Q9), payment⇢ordering, ordering⇢delivery (OrderPaid), delivery⇢payment
  (transfers, Q7).
- **GitHub rendering:** assistant tried to verify by rendering with `mermaid-cli` (npx) – the command
  was **blocked by the permission classifier** (downloads a package), so rendering is **not verified by
  running it**. Mitigation: syntax unified to the most standard GitHub-supported form (`flowchart`,
  quoted node labels, `-->|"label"|`, `-.->|"label"|`, `==>|"label"|`, `<br/>`). Student should check
  the rendered view on GitHub (or VS Code Markdown preview with Mermaid) after push.

**2) Link to requirements** – new table "Requirements that shaped the decision" in Context (6 rows):
US 14–17/33 → D1; US 18/21/32 → D1, D5; US 24–27/34 → D1, D5; US 19/20/35/36 → D4 worker + outbox;
US 4/9/10/23/31 → D3 (main reason A3 is Weak); US 1/29 → D2 (A1 vs. hybrid).
The previous "forces" bullet list was removed – the table replaces it (no duplication).

**3) Related decisions** – each ADR-002…009 now states what was **already agreed in Task 1** (one
sentence), a common **status** ("agreed in Task 1, ADR not written yet – the agreed decision is binding
until then") and the reference (Q/S/L point) into Task_1/NOTES.md. Q/S/L items are bold paragraphs, not
headings → no stable anchors; references are by item id.

**4) Confirmation made concrete** – table of 8 checks with what each proves: architecture import test,
no cross-schema FK (pg_constraint query), SQL lint for foreign schemas, parallel overselling test
(50 checkouts / qty 10, opposite-order carts), parallel rider-accept test, "no network I/O inside a
transaction" guard, outbox/timer/webhook idempotency tests, hot-row load test.
- **Correction found while doing this:** v1/v2 said "*all* external side effects go through jobs". That
  is **not** what Task 1 decided – the Stripe Checkout session is created synchronously in the request
  (customer waits for the URL), only **after** the stock transaction commits (Q3/Q4). The real rule is
  "**no network I/O inside a DB transaction**" → check #6 tests exactly that.
- The latency target for the load test was never defined → added as open question #5 (not invented).

**Length check**
- After the additions v3 had ~3 300 words (≈ 6 pages) → **over the 2–4 page limit**.
- Compressed without dropping content: Context bullets shortened (requirements table carries the forces),
  options as a short list, comparison cells shortened, positive consequences merged to 3 bullets, risks
  in one line, "why rejected" condensed, "More information" folded into one footer line.
- Result: **~2 500 words of text + 2 diagrams ≈ 4–5 printed pages** (tables are dense). Still slightly
  above 4 pages when the diagrams are counted – candidates to cut if needed: "Why the other options were
  rejected" (≈150 words) and "Risks to watch" (both partly covered by the table / Task 1).

## Review round 3 (student) → Version 4 (final)

**Requested:** cut only duplicates (no content), merge "Risks to watch" into the Consequences table,
one sentence per rejected option, ~2 000 words; full consistency check (esp. the "no network I/O inside
a DB transaction" rule and the deployment view); clickable anchors into Task 1; status Accepted.

**Consistency check – findings and fixes**
1. **Deployment view did not show the corrected rule.** `WEB <--> STRIPE` was unlabeled, so it was
   unclear that `web` creates the Checkout session **synchronously after commit** and that Stripe sends
   **webhooks to `web`**. Worker → Stripe was unlabeled too. → Labeled edges: web → Stripe "sync, after
   commit: create Checkout session"; Stripe → web "webhooks: payment result, session expired, account
   updated"; worker → Stripe "jobs: transfers, refunds".
2. **OAuth providers missing in the deployment view** although US 1/29 drive D2 → added `web ↔ OAuth
   providers`.
3. **"What the decision includes" stated only the outbox path.** → Explicit rule with both paths:
   synchronous external calls in `web` after commit; asynchronous side effects as jobs enqueued in the
   transaction and executed by `worker`.
4. **Module-view legend:** solid arrows (e.g. ordering → payment: checkout session) involve network I/O
   → legend now says such calls run after the caller's transaction commits.
5. **Duplicates:** positive consequences repeated "standard tooling, minimal lock-in" from the
   comparison (D5, D7) → removed; "boundary erosion" (risk) duplicated "boundaries rely on discipline"
   (negative) → merged into one row.
6. **TL;DR** said "Revisit when…" as if it were the only trigger, while "When to revisit" has four →
   "**the main** trigger to revisit".
7. Scheduler label → "periodic tasks, timers" (matches the timer-related consequences and checks).
- Verified as consistent (no change): 8 modules = 8 nodes in the module view; Notification-first in TL;DR,
  negative table and revisit table; assumption numbers in the revisit table; hybrid ratings vs. the
  "reading the table" text; ADR-003 and Confirmation #6 use the same rule.

**Other changes**
- "Risks to watch" merged into **"Negative, risks and mitigations"** table (3 new rows: money edge
  cases, stuck state machines, external outages; boundary erosion merged).
- "Why the other options were rejected" → one sentence per option with a link to the Task 1 source.
- **Anchors:** 54 HTML anchors `<a id="…"></a>` inserted into Task_1/NOTES.md (q1–q15, delivery-model,
  a1-final, a2-1…a2-6, f1–f9, a2-final, a3-1…a3-5, s1–s4, l1–l6, a3-final, h1, c1–c4), each on its own
  line after a blank line; a diff confirmed **no other line changed**. ADR now has 32 links into Task 1;
  a script confirmed every linked anchor exists.
- Status **Accepted**, date 2026-10-29.
- **Length:** ~2 300 readable words (without diagram code and link URLs) + 2 diagrams. Slightly above
  the ~2 000 target because the merged risk rows were kept (rule: cut duplicates, not content).

## Review round 4 (student) → Version 5 (final)

**1) Real inconsistency found by the student: module view vs. Confirmation check #3**
- Notifying subscribers of a new insertion needs the farmer's subscribers, which live in the
  `engagement` schema. Task 1 Q9 did it with a cross-schema `INSERT … SELECT FROM engagement.subscription`
  directly from `notification` – **forbidden by check #3** (no cross-schema SQL) and, because "anything
  not drawn is forbidden", the fan-out as designed was **forbidden by the ADR itself**. v1–v4 missed it.
- **Decision (made in this round, student asked the assistant to decide):** `notification` calls
  **`engagement.api` → subscribers of farmer** (read in batches), then inserts notifications into its own
  schema.
  - Rejected alternative: route the event through `engagement` (engagement handles `InsertionPublished`
    and emits per-subscriber events) – more events and an extra hop, with no gain inside a monolith. The
    api call keeps engagement as the owner of subscriptions.
  - Cost: Q9's single set-based statement becomes batched reads + inserts. Acceptable at ≤ 5 000
    subscribers.
- Drawn in the module view: `NOTI --> ENG` "engagement.api: subscribers of farmer".
- **ADR-008 row:** "Changed by this ADR: subscribers read in batches via `engagement.api`; replaces the
  cross-schema INSERT … SELECT from Q9" + link to Q9. (Task 1 notes themselves were not edited – they
  record the discussion as it happened.)

**2) Undrawn event flows** (notification centre: booking accepted/declined US 21/32, order and delivery
status; badges US 28 from sales)
- Chosen: an **explicit legend rule** instead of drawing ~10 more arrows: "`notification` and `engagement`
  may subscribe to domain events of any module (events only, never calls; event types are part of the
  producer's `api/`)". Legend now lists **two kinds of allowed undrawn dependencies** (identity.api
  reads, event subscriptions) and says "**any other** dependency not drawn is forbidden" → consistent.
- Check #1 updated: "only along the module-view arrows **or the two legend rules**".

**3) SSE – was it agreed in Task 1?**
- Partly: SSE appears in Task 1 **C2** (recommendation) and H1 mentions an "own SSE/WebSocket endpoint" –
  but it was **never analysed** (connections, load balancer, reconnect).
- Also found: the mitigation "SSE is enough at our connection counts" in Consequences was an
  **unsupported claim**. → Replaced with "SSE only as a signal + fetch on reconnect (pattern from L3);
  capacity to be verified", source link to C2, and new **open question #6** (concurrent connections at
  peak, behaviour behind the load balancer with 2–3 `web` replicas, reconnect / missed events).

**4) Small fixes**
- Deployment view: added **geocoding provider** (Task 1 delivery model: geocode on address save),
  drawn from the monolith as a whole with "outside a transaction" – which process calls it was not
  decided in Task 1, so the diagram does not pretend it was.
- Related decisions: added **ADR-010 Technology stack – not decided yet** (source C4 #14); status line
  now distinguishes ADR-002–009 (agreed) vs. ADR-010 (not decided); open question #1 points to ADR-010.
- Check #4 reworded: opposite-order multi-box carts must produce **zero deadlock errors (SQLSTATE
  40P01)**; sorted locking must prevent them, the retry is only a safety net and must not fire in the test.
- Context: GDPR applies because **the platform operates in the EU and serves EU users**, not because
  data is processed in the EU.

## Summary of versions

| Version | What changed | Why |
|---|---|---|
| **v1** | First ADR in MADR format: context, drivers D1–D7, 4 options, ★ comparison table, deployment diagram, consequences, revisit table, related ADRs 002–009, open questions | Student's brief: one ADR for the architecture style, reader = newcomer, 2–4 pages |
| **v2** | Status Proposed; driver order adopted from the student (simplicity 2nd, scaling explicit); TL;DR; **stars → verbal ratings with reasons**; prices → relative; duplicates of A1 pros/cons removed; explicit assumptions list | Review 1 – the star table contradicted the decision; prices age; duplicates |
| **v3** | Hybrid ratings fixed (D4, D7) + tie-break rule; module-view diagram with schemas and the shared-transaction exception; requirements → drivers table; related ADRs with "already agreed" + status + refs; concrete Confirmation (8 checks); compressed from ~3 300 words | Review 2 – hybrid ratings ignored H1; missing "why modular"; traceability; verifiable confirmation |
| **v4** | Consistency pass (deployment view shows sync Stripe call + webhooks + OAuth; explicit I/O rule); risks merged into consequences; one-line rejections; clickable anchors into Task 1; Accepted | Review 3 – final polish and consistency |
| **v5** | Module view: notification → engagement.api (subscribers); legend rule for event subscriptions of notification/engagement; ADR-008 notes the replaced cross-schema SQL; SSE sourced to C2 + open question; geocoding in deployment view; ADR-010 stack; check #4 = zero deadlocks; GDPR wording | Review 4 – **diagram contradicted check #3** (fan-out as designed was forbidden by the ADR) |

**Errors found during review (lessons for Task 3 skill)**
1. **The comparison table contradicted the decision** (v1): weighted stars made the hybrid win (83 vs.
   80). Cause: ratings not derived systematically from the discussion; numeric stars invite summing.
   → Use verbal ratings with a reason in every cell, and state the decision rule (lexicographic by driver
   priority) explicitly.
2. **Hybrid ratings ignored known costs** (v2): H1 listed external login dependency, US vendor and
   unused platform, but D4/D7 rated the hybrid like A1. → Re-check every rating against the source
   notes, especially for the runner-up option.
3. **The rule on external calls was stated wrongly** (v1–v2): "all side effects go through jobs" – Task 1
   actually decided "no network I/O inside a DB transaction" (the Stripe session is created
   synchronously after commit). Also the deployment diagram did not show it (v3). → Quote decisions
   from the source precisely; check diagrams against the rules in the text.
4. **The module diagram contradicted a Confirmation check** (v1–v4): Q9's cross-schema fan-out query
   violated check #3 and the "not drawn = forbidden" rule; event flows to notification/engagement were
   missing. → Walk every user-story flow (US 19, 21/32, 28, 36…) through the module diagram and the CI
   checks before finalising; state rules for intentionally undrawn edges.
5. **Unsupported claims slipped in** ("SSE is enough at our connection counts", v3–v4) → every claim in
   the ADR must trace to a Task 1 point; otherwise it is an open question.
6. Smaller: driver order not matching the real reasoning (v1), duplicates between sections (v1–v3),
   length over the limit (v3), unverifiable diagram rendering (tool blocked – student must check on
   GitHub).
