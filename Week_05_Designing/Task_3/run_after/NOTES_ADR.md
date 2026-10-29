# ADR-001 – Working notes and version log

Notes for writing [ADR-001-architecture-style.md](ADR-001-architecture-style.md) from the discussion notes [NOTES.md](NOTES.md).

## Run log
| Field | Value |
|---|---|
| Skill | architecture-decision-record |
| Start | 2026-10-29 15:43 |
| End | 2026-10-29 16:08 |
| User prompts (total) | 4 |
| Versions | v1, v2, v3 (Accepted) |

| # | Time | Step | What happened | User prompts | Requested by the user beyond the skill's plan |
|---|---|---|---|---|---|
| 1 | 15:43 | Steps 0–4 | Inputs checked, defaults chosen, drivers taken from C0 (already confirmed), v1 drafted, self-review run, full text printed | 1 | Print the full ADR text at the end (the skill shows only a link by default) |
| 2 | 15:52 | Step 5 – review iteration | User review with 7 findings → v2; full user-story walk-through; checklist re-run | 1 | All 7 findings (see v2) – none was caught by the self-review |
| 3 | 16:01 | Step 6 – finalise | Erasure legend rule, corrections A1.1-C1 and C3-C1 in NOTES.md, status Accepted, final checklist, summary | 1 | Write the corrections back into the source notes with history (the skill does not cover updating the source notes) |
| 4 | 16:08 | Step 6 – render confirmation | User confirmed both diagrams render; labels removed, K14 ✅ | 1 | – |

## Step 0 – Inputs and gaps
- Source: own notes following the `architecture-exploration` contract – H1, C0–C4 and the three final assessments exist; no gaps
  requiring questions.
- The user asked to prepare the ADR immediately, so Step 0 questions were **not asked**; defaults chosen and listed for confirmation:
  | Item | Default chosen | Status |
  |---|---|---|
  | Language | English (notes language) | to confirm |
  | Audience | developers joining the project + project owner | to confirm |
  | Length budget | ~2 000 words (2–4 pages) | to confirm |
  | Scope | one ADR: the overall architecture style; architecture-independent decisions (C3) only as *Related decisions* | to confirm |
  | Deciders / consulted | Filip (to confirm) / AI coding assistant | to confirm |
  | File | `ADR-001-architecture-style.md` in `run_after/` | given by the user (folder) |
  | ADR notes | this file | given by the user |

## Step 1 – Drivers and decision rule
- Drivers D1–D6 and their order taken from [C0](NOTES.md#c0); confirmed by the user in the exploration (prompt 15), including the broad
  D2 definition ([C0.2](NOTES.md#c0-2)) and the sensitivity tests ([C1](NOTES.md#c1)). No re-confirmation needed.
- Decision rule: driver by driver in priority order, first difference decides.

## Version log

### v1 – 2026-10-29 15:46
**Content:** MADR-based ADR with TL;DR, context, requirements table (6 rows), 9 assumptions (condensed from the 11 in C0 – #10 booking
deadlines and #11 back-office/alerting moved to related decisions / context because they do not affect the style choice), drivers,
options, comparison table, decision outcome with quoted rules, deployment view, module view, consequences, confirmation (8 checks),
revisit table, rejected options (incl. hybrids H-b, H-d), related decisions (8 proposed ADRs), open questions (5).

**Deliberately left out:** diagrams of rejected options; the full C3 list (22 items – summarised into 8 proposed ADRs with a link);
the detailed failure scenarios (linked by ID); hybrid H-a (identical to A1) and H-c (hosting choice – mentioned in the decision outcome).

**Self-review (checklist K1–K18)**
| # | Result | Note |
|---|---|---|
| K1 | ✅ | A1 beats A2 at D1, A3 at D2 – matches the decision |
| K2 | 🔧 | D4 row had no source → C1/A3.4 added; A2 schema evolution (A2.14) and A3 query-cost DoS (A3.5) from the documented costs were missing in ratings → added to D2 cells |
| K3 | ✅ | Order confirmed by the user in the exploration (C0, prompt 15) |
| K4 | 🔧 | Release and owner rules quoted the C3 wording but linked only A1.8 / A2 round 2 → C3 added as source; other quotes checked against A1.1, A1.5, A1.11, A1.17 |
| K5 | ✅ | All Context integrations (PSP, OAuth, e-mail, push, object storage) in the deployment view; after-commit session call, webhooks and jobs outside transactions labelled |
| K6 | 🔧 | Walk-through: insertion → notifications, checkout, booking accept, comment eligibility (US 23), rider claim/delivery/payout, role upgrade, search, back-office refund, handover deadline. The handover-deadline flow needs Ordering to cancel the delivery (A1.14) → arrow Ordering → Delivery "sync in-tx: cancel delivery if not picked up" added and listed as derived; Confirmation #1 now refers to "module view and its legend rules" so the allowed undrawn dependencies are not forbidden by the CI check |
| K7 | ✅ | Capacity claim linked to A1.19; costs [unverified]; legal statement with "not legal advice" |
| K8 | ✅ | Every revisit trigger cites an assumption number; TL;DR names the two main triggers |
| K9 | 🔧 | Risk rows "Module boundaries erode" (duplicate of Confirmation #1) and "Distributed concerns remain" (duplicate of the comparison) removed |
| K10 | ⚠️ | 2 350 words without diagrams/links vs. ~2 000 budget (+17 %); duplicates removed; remaining overrun is traceable content (comparison table, quoted rules, related decisions) – user to decide whether to cut |
| K11 | ✅ | Only relative costs with date 2026-10-29 and source C1 |
| K12 | ✅ | Tests assert exact properties (exactly k, exactly 3, zero deadlocks, exactly one refund); load-test target undefined → Open question 4 |
| K13 | ✅ | GDPR trigger = establishment (Art. 3(1)), "not legal advice, verify"; licensing question marked as such |
| K14 | ⚠️ | No Mermaid renderer available locally (no `mmdc`; installing the CLI would download a headless browser) → both diagrams labelled "[unverified render]"; standard syntax with quoted labels used |
| K15 | ✅ | All `NOTES.md#…` anchors used in the ADR exist (checked by script) |
| K16 | ✅ | 8 related decisions, each with an agreed summary, status line and source |
| K17 | ✅ | Derived elements (module arrows from flows, concurrency tests from A1.2/A1.15/A3.9) marked or traceable; no new decisions |
| K18 | ✅ | Status Proposed |
| extra | 🔧 | Two tables directly after a paragraph line (risks, related decisions) – blank line added so they render as tables |

**Errors found in v1 before showing:** 5 (K2, K4, K6, K9 fixes above) – all found by the assistant's self-review.

**Points for the user's decision:** Step 0 defaults (language, audience, budget, scope, deciders); whether the 17 % overrun is acceptable;
whether the derived module arrows (Booking → Ordering, Delivery ↔ Ordering, Reputation → Ordering, Back-office → *) reflect the intended
design.

<a id="v2"></a>
### v2 – 2026-10-29 15:52

**User decisions:** Step 0 defaults confirmed (English, audience, one ADR for the style, Deciders: Filip); ~2 400 words acceptable if
edits do not enlarge it significantly.

**Findings by the user → changes**
| # | Finding (user) | Change in v2 | Type |
|---|---|---|---|
| U1 | Stock-release rule too broad: P2 quantity returns at the payment deadline with no session (A1.3); holds released on a definite session-creation error (A1.2-C3) | Rule split: stock tied to a session that exists or may exist → terminal PSP fact only (C3, A1.8) + never release on unknown creation outcome (A1.2-C3); stock without a session → domain rule (definite error, booking payment deadline) – all quoted from the notes | precision, no new decision |
| U2 | Module view misses flows: badges need sales events; back-office handles overdue deliveries; rider availability requires an active push subscription; search needs box availability/expiry | Arrows added: Ordering ⇢ Reputation (job: sales events), Back-office → Delivery, Delivery → Engagement (push subscription check; `push_subscriptions` owned by Engagement per A1.1); read-model exception extended to search incl. expiring boxes – **Changed by this ADR** (A1.1 named only home/farmer page). The full walk-through (below) found two more: Catalog → Inventory (create/adjust/withdraw boxes, A1.13) and the read part of Ordering/Booking → Inventory | diagram + one changed rule |
| U3 | Deployment view: worker deletes files on erasure (A1.18) – no arrow to object storage; external uptime monitor from Confirmation #8 missing | Arrow worker → object storage "delete files on erasure"; node "External uptime monitor" polling the web health endpoint; monitor also listed in Context integrations | diagram |
| U4 | D3 has no confirmation check; no check for "no network call inside a transaction" | Confirmation #9 negative authorization (404), #10 revocation on the next request, #11 OAuth linking, #12 PSP/e-mail/push clients fail when a transaction is open | confirmation |
| U5 | Requirements table misses notifications (US 19, 35, 36) although the `bulk` queue and the Engagement extraction come from them | Row added (A1.5, A1.17) | content |
| U6 | Assumption 4 "growth to a few regions in 2–3 years" allegedly not discussed | **Not removed:** the text is in NOTES [R4](NOTES.md#r4) A4 and was confirmed by the user in prompt 3 ("Predpoklady A1–A8 potvrdzujem"); a source link to R4 was added. The user can still ask to drop it | source link |
| U7 | Open question: coordinates for distance search – geocoding provider vs. map pin; cost and GDPR | Open question 6 added, marked "not in the notes, added at the user's request" | open question |

**Proposed follow-up in NOTES.md (not done – content change needs the user's consent):** C3 row "Releasing stock" has the same over-broad
wording as v1 of the ADR; A1.1 read-model exception should list the search read model.

**User-story walk-through of the module view (v2)** – arrows used per story (ID = Identity calls, allowed by legend; RM = read-model
exception)
| US | Flow | Arrows / rule |
|---|---|---|
| 1, 2, 3, 29, 30, 6 | register, logout, login, OAuth, edit/show own info | inside Identity |
| 5 | home page | RM |
| 7 | seasonal calendar | inside Catalog |
| 8 | search insertions incl. availability | RM (extended in v2) |
| 9, 10 | delete / modify insertion → withdraw its boxes | Catalog → Inventory (sync in-tx) – **added in v2** |
| 11 | expiring boxes list | RM (extended in v2) |
| 12, 24 | upgrade to farmer / rider | inside Identity; Delivery reads the rider role via ID |
| 13 | farmer page incl. comments, badges | RM |
| 14, 15, 33 | cart add/remove/show | inside Ordering; Ordering → Inventory (sync read of box) |
| 16, 17 | order + checkout + payment | Ordering → Inventory (in-tx hold); PSP via web after commit; webhook → Ordering; Ordering ⇢ Delivery, Ordering ⇢ Engagement |
| 18 | book from calendar | Booking → Inventory (read planned box) |
| 19, 35 | subscribe / unsubscribe | inside Engagement |
| 20 | list of subscribed farmers | Engagement + ID (farmer profiles) |
| 21 | accept / decline booking | Booking → Inventory (in-tx allocate), Booking → Ordering (in-tx create order), Booking ⇢ Engagement |
| 22 | order history incl. delivery status | inside Ordering (status updated by Delivery ⇢ Ordering jobs) |
| 23 | comment after purchase | Reputation → Ordering (sync read) |
| 25 | rider delivery page incl. addresses | inside Delivery + ID (addresses under Identity's access rules) |
| 26 | rider available → receives offers | Delivery → Engagement (push subscription check) – **added in v2**; Delivery ⇢ Engagement (offers) |
| 27 | delivery option at checkout | Ordering ⇢ Delivery (request per farmer_order) |
| 28 | badges | Ordering ⇢ Reputation (sales events) – **added in v2** |
| 31 | add boxes to own insertion | Catalog → Inventory (sync in-tx) – **added in v2** |
| 32 | status of booking requests | inside Booking |
| 34 | rider updates delivery status | inside Delivery; Delivery ⇢ Ordering (picked up / delivered → payouts) |
| 36 | notification centre | inside Engagement |
| implicit | back-office: refunds/disputes, overdue deliveries, moderation, roles | BO → Ordering, BO → Delivery (**added in v2**), BO → Reputation, BO → ID |
| implicit | handover deadline cancels delivery | Ordering → Delivery (sync in-tx, added in v1 review) |
| implicit | GDPR erasure | each module erases its own data via its interface – job from Identity (not drawn; **open point** – see below) *(resolved in v3: legend rule `erase_user`)* |

**Open point found by the walk-through (not fixed, for the user):** erasure (A1.18) touches every module (orders pseudonymised, comments
anonymised, push subscriptions deleted, files deleted). The module view has no arrows for it and the legend forbids undrawn dependencies.
Proposal for v3: legend rule "Identity may enqueue an `erase_user` job that every module handles for its own data" (derived from A1.18)
instead of eight more arrows.

**Why self-review K6 did not catch U2 (lesson for the skill)**
1. K6 asks for **4–6 key flows**; v1 sampled the risky money/stock flows (checkout, booking, rider claim, refund) – exactly the ones that
   were already designed in detail. The missed flows were the "boring" ones (badges, search, back-office delivery cases), where nobody had
   designed the dependency explicitly.
2. K6 traces **user stories** only; two misses came from **non-story sources**: an assumption with an enforcement point (A6′ – available only
   with a push subscription) and an implicit requirement (back-office handling A1.14 cases). K6 does not tell the reviewer to walk
   assumptions, timers and back-office actions.
3. The **read-model exception was copied verbatim** from the notes (K4 "quote exactly") without checking which stories rely on it – K4 and
   K6 pulled in opposite directions and K4 won.
4. The module view lists **owned data** but K6 does not ask "for every piece of data a flow reads, who owns it?" – the `push_subscriptions`
   table is owned by Engagement, which made the Delivery dependency invisible.
- **Proposed skill change:** K6 → walk **every** user story plus every assumption with an enforcement point, every timer owner and every
  back-office action; for each data item read, name the owning module and the arrow or legend rule that allows it; output the walk-through
  table into the ADR notes (as done in v2).

**Self-review v2 (K1–K18 re-run)**
| # | Result | Note |
|---|---|---|
| K1 | ✅ | Ratings unchanged; A1 still wins at D1 vs. A2 and at D2 vs. A3 |
| K2 | ✅ | No rating changed; new requirement row and checks have sources |
| K3 | ✅ | Unchanged |
| K4 | ✅ | Release rule now quotes C3, A1.8, A1.2-C3 and A1.3 verbatim; the read-model rule quotes A1.1 and marks the extension as changed by this ADR |
| K5 | ✅ | Uptime monitor now in Context and in the deployment view; erasure file deletion drawn |
| K6 | 🔧 | Full walk-through of 36 stories + implicit flows; 6 arrows added; 1 open point (erasure) left for the user |
| K7 | ✅ | Open question 6 marked as not from the notes |
| K8 | ✅ | Unchanged; assumption 4 now linked to R4 |
| K9 | 🔧 | Derived-arrow list moved from the ADR legend to this file (it duplicated the walk-through) |
| K10 | ⚠️ | 2 701 words (v1: 2 350, +15 %; user's limit "about 2 400"): additions are the user's 7 findings; duplicates trimmed (legend list, open question 6) |
| K11 | ✅ | Unchanged |
| K12 | ✅ | New checks assert exact outcomes (404, denied on the next request, failing client) |
| K13 | ✅ | Open question 6 mentions DPA/region without legal claims |
| K14 | ⚠️ | Still not rendered locally; module view uses a subroutine node and `-.-|"…"|` links – standard syntax, unverified render |
| K15 | ✅ | All NOTES.md anchors exist; `NOTES_ADR.md#v2` anchor added |
| K16 | ✅ | Unchanged |
| K17 | ✅ | One "Changed by this ADR" item (read-model exception) at the user's request; open question 6 marked as added |
| K18 | ✅ | Proposed |

**Errors in v2 found by:** user 7 (U1–U7, one of them – U6 – turned out to have a source); assistant 3 more during the walk-through
(Catalog → Inventory, read part of Ordering/Booking → Inventory, erasure open point).

<a id="v3"></a>
### v3 – 2026-10-29 16:01 (final, Accepted)

**User decisions:** assumption 4 stays (source R4 confirmed); erasure legend rule accepted; corrections to be written into NOTES.md with
history; ~2 700 words accepted; status Accepted with today's date.

**Changes**
- ADR legend: "**Erasure:** Identity may enqueue an `erase_user` job that every module handles for its own data" – marked *added by this
  ADR (v3, user's request), derived from A1.18*.
- NOTES.md: new items **A1.1-C1** (read-model exception incl. search and expiring boxes; erasure job) and **C3-C1** (precise stock-release
  rule); the old statements marked *(superseded → …)*; ADR links now point to these corrections.
- Status **Accepted**, Date 2026-10-29, Deciders Filip.
- **Not changed:** the "[unverified render]" labels – the user's message contained the unfilled placeholder "[doplň: vykreslili sa bez
  chyby / chyba: ...]", so the render result is unknown; labels stay until the user reports the result. *(16:08: the user reported that
  both diagrams render without errors in mermaid.live → labels removed, K14 ✅; content of the ADR unchanged.)*

**Final self-review (K1–K18)**
| # | Result | Note |
|---|---|---|
| K1 | ✅ | A1 wins at D1 vs. A2 and at D2 vs. A3; sensitivity unchanged |
| K2 | ✅ | Every rating cell has a notes ID |
| K3 | ✅ | Order confirmed (C0, exploration prompt 15) |
| K4 | ✅ | Rules quoted from A1.1, A1.5, A1.11, A1.17, C3, A1.8, A1.2-C3, A1.3; changes marked and now recorded in the notes (A1.1-C1, C3-C1) |
| K5 | ✅ | All Context integrations incl. uptime monitor drawn; after-commit call, webhooks, jobs, file deletion labelled |
| K6 | ✅ | Full walk-through (36 stories + back-office, timers, erasure) – no flow without an arrow or legend rule |
| K7 | ✅ | Claims sourced or marked [unverified] / "not in the notes" |
| K8 | ✅ | Revisit triggers cite assumptions; TL;DR consistent |
| K9 | ✅ | No duplicates found |
| K10 | ✅ | 2 735 words – within the user-approved ~2 700 |
| K11 | ✅ | Relative costs with date |
| K12 | ✅ | All checks assert exact properties; load-test target in Open question 4 |
| K13 | ✅ | Legal statements with "not legal advice / verify" |
| K14 | ✅ | Verified by the user in mermaid.live (16:08): both diagrams render without errors; "[unverified render]" labels removed |
| K15 | ✅ | All `NOTES.md#…` and `NOTES_ADR.md#v2` anchors resolve (checked by script) |
| K16 | ✅ | 8 related decisions with summary, status, source |
| K17 | ✅ | Two "changed/added by this ADR" items, both at the user's request and now in the notes |
| K18 | ✅ | Accepted + date on the user's instruction |

## Final summary

| Version | Time | Trigger | Main changes |
|---|---|---|---|
| v1 | 15:46 | first draft | full ADR, self-review with 5 fixes |
| v2 | 15:52 | user review (7 findings) | precise stock-release rule, 6 module arrows + read-model exception, deployment additions, 4 confirmation checks, notifications row, open question on geocoding |
| v3 | 16:01 | finalisation | erasure legend rule, corrections back-ported into NOTES.md, Accepted |

**Findings caught by the self-review (before the user saw them): 8**
- v1 (5): missing source for D4; documented costs A2.14 and A3.5 absent from ratings (K2); incomplete source for two quoted rules (K4);
  missing Ordering → Delivery cancel arrow + CI check forbidding legend-allowed dependencies (K6); two duplicate risk rows (K9); plus
  tables without a preceding blank line (formatting).
- v2 (3, during the full walk-through): Catalog → Inventory arrow; read part of Ordering/Booking → Inventory; erasure without any arrow or
  rule.

**Findings from the user's review: 7** (6 real, 1 – U6 – had a source in the notes)
| # | Finding | Checklist item that should have caught it | Why it did not |
|---|---|---|---|
| U1 | Stock-release rule too broad | K4 (quote exactly) | K4 checks wording against the source, not whether the source rule itself covers all cases; the notes' C3 row was already too broad |
| U2 | 4 missing module flows | K6 | samples only 4–6 flows; stories only; no "who owns the data I read" question (details in v2) |
| U3 | Missing deployment edges (file deletion, uptime monitor) | K5 | K5 checks Context integrations against the diagram; the monitor was not in Context and file deletion is a flow, not an integration |
| U4 | No confirmation check for D3 and for the no-network-in-transaction rule | K12 | K12 checks the quality of each test, not **coverage**: every top driver and every key rule needs at least one check |
| U5 | Notifications missing in the requirements table | none | no check that every component/queue in the decision is motivated by a requirements row |
| U6 | Assumption allegedly unsourced | K7 | (had a source – the ADR now links it explicitly) |
| U7 | Coordinates / geocoding open question | none | gaps in the notes themselves are not searched for; only claims in the ADR are traced |

**What follows for the skill (proposed changes)**
1. **K4+:** besides quoting exactly, check each quoted rule against **all states it governs** (R3 from the exploration skill: enumerate
   the states – here "stock with / without a PSP session") – exact quoting of a too-broad rule propagates the error.
2. **K6 rewrite:** walk **every** user story plus assumptions with enforcement points, timer owners, back-office actions and erasure; for each
   data item read, name the owning module and the arrow/legend rule; store the walk-through table in the ADR notes.
3. **K5+:** every Confirmation check and every risk mitigation that needs an external system (monitor, storage) must appear in the
   deployment view; every "worker does X with Y" in the notes is an edge.
4. **New K19 – Confirmation coverage:** each of the top 3 drivers and each key rule in *What the decision includes* has at least one check.
5. **New K20 – Requirements coverage:** every component, queue or extraction path named in the decision is motivated by a row in the
   requirements table.
6. **New K21 – Gaps in the source:** for every assumption, ask "what does implementing it require that the notes never discussed?" →
   Open questions (e.g. geocoding for distance search).
7. **Step 6+:** when the review changes a rule, write a Correction back into the source notes with a link to the ADR version (done
   manually here at the user's request).
8. Step 0: when the user asks to skip questions, record the defaults as "to confirm" (worked well – keep).
