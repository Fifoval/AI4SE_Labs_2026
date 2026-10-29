# Task 3 – Skill creation notes

Running notes for turning Task 1 (architecture debate) and Task 2 (ADR) into reusable skill(s), testing
them in a new session and comparing before/after.

Sources inspected: [../Task_1/NOTES.md](../Task_1/NOTES.md), [../Task_2/NOTES.md](../Task_2/NOTES.md),
[../Task_2/ADR-001-architecture-style.md](../Task_2/ADR-001-architecture-style.md).
`Task_3/transcripts/before.md` **does not exist yet** – the analysis below uses the two NOTES files plus
the assistant's own session history (same session). The transcript must be exported before the
comparison report (see "Transcripts" at the end).

---

## Step 1 – Analysis of the original run (before the skill)

### a) Course of the work and prompt cost (student prompts)

| # | Step | Student prompts | Output |
|---|---|---|---|
| 0 | Setup: analyse Week 05, ask for project; project = EFarmers | 2 | task overview |
| T1.1 | Requirements analysis + A1 (modular monolith) proposal | (incl. in setup prompt 2) | notes §0, A1 |
| T1.2 | A1 debate: stock atomicity, booking, peaks, timers, marketplace money (Q1–Q5) | 1 | Q1–Q5 |
| T1.3 | A1: delivery model, manual capture, transfer timing, module boundaries, outbox (Q6–Q9) | 1 | Q6–Q9 |
| T1.4 | A1: rider limit, **timer inventory**, roles/authz, account linking, fan-out, **deployed processes + final assessment** (Q10–Q15) | 1 | Q10–Q15, A1 final |
| T1.5 | A2 big picture (services, broker, sync/async, saga, moved timers, identity) + FCM fact fix | 1 | A2.1–A2.6 |
| T1.6 | A2 **failure scenarios** (F1–F4) | 1 | F1–F4 |
| T1.7 | A2 cross-service reads, multi-source state, schema evolution, debugging, **honest cost** + final (F5–F9) | 1 | F5–F9, A2 final |
| T1.8 | F1 SQL bugs + A3 big picture (A3.1–A3.5) | 1 | A3.1–A3.5 |
| T1.9 | A3 security & development (S1–S4) | 1 | S1–S4 |
| T1.10 | A3 lock-in, cost, realtime, GDPR, Firebase, **critical "what is left of the promise"** + final (L1–L6) | 1 | L1–L6, A3 final |
| T1.11 | **Hybrid critique** + comparison & conclusion (C1–C4) + notes cleanup | 1 | H1, C1–C4 |
| T2.1 | ADR brief → v1 | 1 | v1 |
| T2.2 | Review 1 → v2 (driver order, TL;DR, star table contradiction, prices, duplicates, assumptions) | 1 | v2 |
| T2.3 | Review 2 → v3 (hybrid ratings, module view, requirements table, related ADR status, confirmation) | 1 | v3 |
| T2.4 | Review 3 → v4 (consistency pass, risks merge, anchors, Accepted) | 1 | v4 |
| T2.5 | Review 4 → v5 (diagram vs. CI check, event rule, SSE source, geocoding, ADR-010, deadlock test, GDPR wording) | 1 | v5 |

**Totals:** Task 1 = **10 work prompts** (+2 setup), Task 2 = **5 prompts** (1 brief + 4 review rounds).
Each student prompt was long and expert-level (5–10 numbered questions).

### b) What the student had to request manually (could have been done up front)

Task 1
1. **Failure scenarios per architecture** (A2 F1–F4, A3 S1–S4) – the assistant only presented happy paths.
2. **Complete inventory of time-driven behaviour** (Q11 timers T1–T9) – appeared piecemeal.
3. **Deployment / process view and "what hurts after a year"** (Q15).
4. **Final assessment per architecture** (strengths, weaknesses, risks, verdict) – first requested for A1,
   then reused.
5. Cross-cutting topics for distributed/BaaS styles: cross-service reads, multi-source state, schema
   evolution, debugging + local dev, identity propagation (F5–F8, A2.6).
6. **Honest cost** (deployables, pipelines, team size, infra) and **lock-in / exit plan** (F9, L1, L2).
7. **Compliance** (GDPR: region, DPA, erasure across stores) (L4).
8. **Comparison with the obvious alternative product** (Supabase vs. Firebase, L5).
9. **Devil's-advocate question** "what is left of the style's promise?" (L6).
10. **Critique of the hybrid / runner-up** before accepting it (H1).
11. **Comparison table with fixed criteria, recommendation + change conditions, architecture-independent
    decisions, open questions** (C1–C4) and a notes cleanup (TOC, superseded markers).

Task 2
12. Explicit **assumptions** list with "revisit if broken" (v2).
13. **TL;DR** (v2).
14. **Driver order matching the actual reasoning** + explicit **decision rule** (tie-break) (v2, v3).
15. **Relative instead of absolute costs** with estimate date (v2).
16. **Requirements → drivers traceability** table (v3).
17. **Module view** in addition to the deployment view (v3).
18. **Concrete, verifiable Confirmation** (CI checks, tests) (v3).
19. **Status + summary of each related decision** (not just a pointer) (v3).
20. **Clickable anchors** into the notes (v4).

### c) Errors found in review and the rule that would have prevented each

| # | Error (where) | Found by | Preventive rule |
|---|---|---|---|
| E1 | Manual capture as 3rd protection layer – redundant given layers 1–2 (Task 1 Q4→Q6) | student | For every protective mechanism, name the failure it prevents and check whether an earlier layer already prevents it. |
| E2 | FCM "batch API up to 500 per call" – outdated (batch endpoint shut down) (Q14) | student | Claims about external APIs, limits, prices, platform capabilities must be verified against current docs (web search) or marked *unverified*. |
| E3 | Idempotent compensation SQL: "0 rows = released" ignored other states; stock not returned (F1) | student | For every idempotent/compensating operation, enumerate all pre-existing states and the effect on every invariant (e.g. stock quantity). |
| E4 | 24 h safety TTL for perishable goods (F2) | student | Derive timeouts from domain constraints (perishability, legal deadlines), never from generic defaults. |
| E5 | "Rate limit by construction" – async trigger means overlapping workers (S4) | student | When work is triggered asynchronously, check overlap/concurrency explicitly. |
| E6 | Rider view: security-definer view bypasses RLS; column grants can't distinguish users of one role (S1) | student | Verify the real semantics of a security mechanism (row vs. column, owner vs. invoker rights, per role vs. per user). |
| E7 | Comparison table contradicted the decision (weighted stars → hybrid won) (ADR v1) | student | Use verbal ratings with reasons; state the decision rule; mechanically check that the chosen option wins under that rule. |
| E8 | Hybrid ratings ignored costs listed in H1 (ADR v2) | student | Trace every rating to a notes item; re-check the runner-up option against all its documented cons. |
| E9 | Rule misquoted: "all side effects through jobs" vs. decided "no network I/O inside a DB transaction" (ADR v1–v3) | assistant (v3) | Quote decisions from the source precisely, with the source ID; never paraphrase a rule into a stronger/different one. |
| E10 | Deployment diagram did not show the sync Stripe call, webhooks, OAuth; geocoding missing (v3–v4) | student | Every integration named in Context and every rule in the text must be visible in the diagrams; check diagram ↔ text. |
| E11 | Module diagram contradicted CI check #3 (fan-out via cross-schema SQL); undrawn event flows (v1–v4) | student | Walk each key user-story flow through the module view and the Confirmation checks; state explicit rules for intentionally undrawn edges. |
| E12 | Unsupported claim "SSE is enough at our connection counts" (v3–v4) | student | Every claim in the ADR must trace to a notes ID; otherwise it becomes an open question. |
| E13 | Driver order didn't match the actual reasoning (v1) | student | Derive driver priority from the recommendation's "why" in the notes; show it to the user for confirmation. |
| E14 | Duplicates between sections; length over the limit (v1–v3) | student | Run a duplication pass (each fact once) and a word-count budget before presenting. |
| E15 | Absolute prices in a long-lived document (v1) | student | Long-lived docs use relative estimates + estimate date + source. |
| E16 | Deadlock test tolerated deadlocks ("after retries") (v4) | student | A test must verify the property (zero deadlocks), not tolerate its violation via the safety net. |
| E17 | GDPR applicability worded as "data processed in EU" (v4) | student | Legal applicability statements: state the actual trigger (establishment / target users); mark "not legal advice". |
| E18 | Mermaid rendering not verified (tool blocked) | assistant | Try to validate diagrams; if impossible, say so explicitly and ask the user to check. |

### d) What worked and must be kept

- **One architecture at a time, in rounds**; the student asked 4–10 deep questions per round, the
  assistant answered each point, **took positions** ("you are right" / counter-proposal, e.g. SetupIntent
  instead of only payment link) and recorded decisions.
- **Running NOTES with stable IDs** (Q/F/S/L/H/C), explicit **Decision** lines, **Correction** and
  *superseded* markers, later **HTML anchors** → reusable as ADR sources.
- **Final assessment per architecture** (strengths / weaknesses / risks / verdict) and the **comparison
  section** (table, recommendation + change conditions, architecture-independent decisions, open
  questions).
- **Fact verification with sources** (FCM, Supabase event triggers, pricing) and honesty about
  uncertainty ("not legal advice", "rough estimate", "verify").
- **Concrete artefacts to test understanding:** SQL snippets, state machines, timer tables, flow steps.
- **Honest critique** ("is A3 just A1 in SQL?", "what hurts after a year", "distributed monolith").
- ADR: **MADR**, verbal ratings + decision rule, two diagram levels, assumptions, confirmation checks,
  revisit triggers, related decisions with status; **version log with what/why** in Task 2 notes.
- "Only source = notes; missing → open question" rule for the ADR.

---

## Step 2 – Skill structure (approved with changes)

Proposed: two skills (`architecture-exploration` for Task 1, `architecture-decision-record` for Task 2)
in `.claude/skills/`, short SKILL.md + `references/`. Reason for two (not one, not three): different
triggers – an ADR is often written from existing/foreign notes without a debate; shared conventions
(notes IDs, Comparison & conclusion) are defined by the first skill and consumed by the second.

**Student's changes at approval**
1. Generic ≠ vague: domain solutions of E-Farmers are forbidden, but **concrete generic technical traps**
   belong in the question bank (compensation overtakes action, ACK before/after commit, outbox/inbox,
   views bypassing RLS, functions callable via PUBLIC, stale JWT role, OAuth pre-hijacking, reservation
   timer vs. payment-gateway expiry, marketplace holding third-party funds) – each with the failure it
   reveals.
2. Stronger descriptions with EN + SK trigger phrases (student will first test without naming the skill).
3. Round budget: max 3 rounds per architecture (big picture / failures / final assessment), max 5–7
   points + 2–3 questions per round; "fast mode / rýchly režim" merges rounds.
4. Run log section in the notes template (start/end time, rounds, number of user prompts, what the user
   had to request beyond the skill).
5. Skill instructions in English; talk in the user's language; ADR language chosen by the user, default EN.
6. Unverifiable items labelled (diagram render → ask to check in mermaid.live; facts without web → [unverified]).
7. Skills linked: exploration produces *Comparison & conclusion* in the shape the ADR skill expects;
   the ADR skill also works with foreign notes and **asks** when options/reasoning/assumptions are missing.

## Step 3 – Skills written

### Files (line counts)
```
.claude/skills/
├── architecture-exploration/
│   ├── SKILL.md                                  140
│   └── references/
│       ├── hard-spots-checklist.md                25
│       ├── failure-question-bank.md              134
│       ├── assessment-template.md                 63
│       └── notes-template.md                      83
└── architecture-decision-record/
    ├── SKILL.md                                   88
    └── references/
        ├── adr-template.md                        86
        └── adr-review-checklist.md                25
                                         total    644
```
README with links: [README.md](README.md).

### Error → preventing rule
| Error | Prevented by | File |
|---|---|---|
| E1 redundant protection layer | R1 "Justify every protection layer" | exploration/SKILL.md |
| E2 outdated external fact (batch API) | Ground rule 8 + R2; bank note "verify: batch endpoints get deprecated" | exploration/SKILL.md, failure-question-bank.md §A |
| E3 compensation SQL ignored states / invariant | R3 "Enumerate states"; notes rule for snippets; bank "compensation overtakes the action (tombstones)" | exploration/SKILL.md, notes-template.md, failure-question-bank.md §C |
| E4 generic 24 h TTL | R4 "Timeouts from the domain"; bank "timeout derived from a domain constraint", "safety TTL … derived from the domain" | exploration/SKILL.md, failure-question-bank.md §A, §C |
| E5 overlapping async workers | R5 "Async triggers overlap"; bank "workers triggered asynchronously … can runs overlap?" | exploration/SKILL.md, failure-question-bank.md §A, §D |
| E6 RLS bypass via view / per-role column grants | R6 "Real security semantics"; bank §D views + column privileges | exploration/SKILL.md, failure-question-bank.md §D |
| E7 table contradicted decision | Phase 3 step 3 rule check; C1 "Rule check"; K1 | exploration/SKILL.md, assessment-template.md, adr-review-checklist.md |
| E8 runner-up ratings ignored critique | Phase 3 step 1 "critique runner-up with *all* costs"; K2 | exploration/SKILL.md, adr-review-checklist.md |
| E9 misquoted rule | ADR ground rule 3 "Quote decisions precisely"; K4 | decision-record/SKILL.md, adr-review-checklist.md |
| E10 deployment view missing rule/integrations | K5; template guidance "every external integration from Context, sync vs. async edges" | adr-review-checklist.md, adr-template.md |
| E11 module view vs. CI check | K6 flow walk-through; template legend rule for undrawn dependencies; bank §B "flows needing another module's schema" | adr-review-checklist.md, adr-template.md, failure-question-bank.md |
| E12 unsupported claim | ADR ground rule 2 "Single source"; K7 | decision-record/SKILL.md, adr-review-checklist.md |
| E13 driver order ≠ reasoning | ADR Step 1 (derive from reasoning, user confirms); K3; exploration Phase 3 step 2 | decision-record/SKILL.md, adr-review-checklist.md, exploration/SKILL.md |
| E14 duplicates / length | K9, K10 | adr-review-checklist.md |
| E15 absolute prices | R9; K11; template cost row guidance | exploration/SKILL.md, adr-review-checklist.md, adr-template.md |
| E16 test tolerated deadlocks | R7 "Tests prove the property"; K12 | exploration/SKILL.md, adr-review-checklist.md |
| E17 legal wording | R8; K13 | exploration/SKILL.md, adr-review-checklist.md |
| E18 unverified Mermaid render | ADR ground rule 5; K14 (try, else label + mermaid.live) | decision-record/SKILL.md, adr-review-checklist.md |

### Manual requests from the original run → where the skill covers them itself
| # | Manually requested in the original run | Covered by |
|---|---|---|
| 1 | Failure scenarios per architecture | Phase 2 Round 2 + failure-question-bank.md |
| 2 | Inventory of time-driven behaviour | Phase 2 Round 1 ("proactively include") + hard-spots H4 + bank §A |
| 3 | Deployed processes, what hurts after a year | Round 1 "what we actually deploy" + Round 3 assessment "Risks after one year" |
| 4 | Final assessment per architecture | Round 3 + assessment-template.md §1 |
| 5 | Cross-service reads, multi-source state, schema evolution, debugging/local dev, identity propagation | failure-question-bank.md §C (+ §A identity) |
| 6 | Honest cost, lock-in / exit plan | assessment-template.md (Cost & team, Lock-in & exit) + R9 + bank §A, §D |
| 7 | GDPR / compliance | hard-spots H12 + bank §A data/privacy + assessment "Compliance impact" |
| 8 | Comparison with the obvious alternative product | bank §D "alternative BaaS with a document database" (pattern: compare with the closest alternative of the same style) |
| 9 | Devil's advocate "what is left of the promise" | Round 3 assessment-template "Devil's advocate" + bank §D |
| 10 | Hybrid / runner-up critique | Phase 3 step 1 + assessment-template H1 + bank §E |
| 11 | Comparison table, recommendation + change conditions, independent decisions, open questions, notes cleanup | Phase 3 + Phase 4 + assessment-template §2 (C0–C4) |
| 12 | Explicit assumptions (revisit if broken) | Phase 1 (confirm assumptions) + C0 + adr-template "Assumptions" |
| 13 | TL;DR | adr-template.md |
| 14 | Driver order + decision rule (tie-break) | exploration Phase 3 steps 2–3 + ADR Step 1 + K1, K3 |
| 15 | Relative costs | R9 + K11 + adr-template cost row |
| 16 | Requirements → drivers traceability | adr-template "Requirements that shaped the decision" |
| 17 | Module view | ADR Step 2 visuals + adr-template module view + K6 |
| 18 | Concrete Confirmation | adr-template Confirmation + K12 |
| 19 | Related decisions with status + summary | adr-template + K16 |
| 20 | Clickable anchors | exploration Phase 4 + notes-template + ADR Step 2 + K15 |

### Generality check (grep)
- `grep -rniE "stripe|booking|rider|farmer|insertion|e-?farmers" .claude/skills` → **no matches**.
- Borderline generic words found by a wider grep (kept on purpose, they are generic categories, not
  E-Farmers solutions): `book` (cue word for reservations in the hard-spots checklist), `seasonal`
  (cue for peaks), `dispatch`, `radius` (assignment/geo category cues), `perishable/perishability`
  (example of a domain constraint for timeouts), `marketplace` + `PSD2` (generic regulatory trap of
  holding third-party funds), `delivery` (message delivery semantics / notification delivery).

## Transcripts
- `before.md` was not on disk after the student's export attempt → generated from the session log
  `~/.claude/projects/c--Users-Fifov-Documents-MATFYZ-2mAIN-AI-AI4SE-Labs-2026/ad3caea8-….jsonl`
  (only session of the project, no compaction, source read-only – SHA1 checked) with
  `tools/jsonl_to_md.py`: 21 user messages at first conversion; re-generated after Task 3 skill writing.
- `after.md` – will be generated the same way from the new session's JSONL.

## Step 4 – Neutrality pass and test preparation
**Neutrality (no food/farm associations, no fixed trio of styles):**
- R4 example "perishability" → "event start time for tickets, check-in date for hotel rooms, flash-sale end".
- Hard spots: H1 examples → concert tickets, hotel rooms, flash-sale items, appointment slots (cue "book"
  → "hold", added "sold out"); H4 cues "seasonal, calendar" → "valid until, auto-cancel, reminders";
  H6 "dispatch, radius" → "claim a task, available agents/technicians, nearest free"; H10 "radius" →
  "distance"; H13 "seasonal" → "ticket on-sale moment, flash sales".
- Failure bank: "scarce/perishable inventory" → "scarce or time-bound inventory (tickets for tonight, a
  room for tomorrow)"; "perishability" → "event start, check-in date, sale end".
- Phase 1 candidate styles: the example trio (modular monolith / event-driven / serverless) could steer
  the test towards the same three options → replaced by a broader menu (layered/modular monolith,
  microservices, event sourcing + CQRS, serverless/BaaS, space-based, pipeline/batch, micro-frontends)
  + "do not default to a fixed trio".
- Kept on purpose (generic, requested by the student as concrete traps): marketplace / multi-seller
  payments and licensing, notification fairness for scarce items. Residual bias to note in the report:
  the failure bank has detailed sections for monolith, microservices, serverless/BaaS and hybrids
  (the styles discussed originally); other styles rely on the cross-cutting section.
- Grep after the pass: no `perish|seasonal|farm|food|fresh|harvest|grocer|produce` in `.claude/skills`.

**Converter in the repo:** `Task_3/tools/jsonl_to_md.py` (+ optional title argument), usage in README.

**Test preparation:** Task_1/, Task_2/, Task_3/NOTES.md (this file) and Task_3/transcripts/ moved to
`../week05_backup/` (outside the repo, nothing deleted); empty `Task_3/run_after/` created. This file is
therefore in the backup during the test and is restored afterwards.
