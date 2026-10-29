# Task 3 – Before/after report: architecture skills

Compares the original run (no skills: [before.md](transcripts/before.md), [Task_1/](../Task_1/NOTES.md),
[Task_2/](../Task_2/ADR-001-architecture-style.md), analysis in [NOTES.md](NOTES.md)) with the run that used the skills
([after.md](transcripts/after.md), [run_after/](run_after/NOTES.md)). Date: 2026-10-29.

## 1. Setup
- **Same system:** E-Farmers ([requirements](../Tasks/data/EFarmers.txt), 36 user stories); same student, same task: debate 3
  architectures (Task 1), write an ADR (Task 2).
- **Skills** (in `.claude/skills/`, derived from the original run, 644 lines at test time):
  - `architecture-exploration` – rounds per architecture (big picture → failures → assessment), correctness rules R1–R9,
    hard-spot checklist, failure question bank, notes template with IDs and a Run log, comparison contract.
  - `architecture-decision-record` – MADR template, self-review checklist K1–K18, version log.
- **Leak prevention:** Task_1/, Task_2/, Task_3/NOTES.md and the transcripts were moved to `../week05_backup/` (outside the repo,
  never committed); a new session was started; the skills were grepped for domain words (0 matches); the memory folder was empty and
  there is no CLAUDE.md (checked after the test).
- **Triggering:** the first prompt ("Prečítaj požiadavky … poďme spolu prebrať rôzne architektúry") did not name a skill;
  `architecture-exploration` started on its own. The ADR request ("priprav ADR") triggered `architecture-decision-record`.

## 2. Metrics

**Active time** = sum of gaps between consecutive JSONL events (user, assistant, tool) inside a task's window; gaps longer than
30 min are treated as pauses and left out. Windows: from the task's first prompt to the next task's first prompt. It includes the
student's reading/thinking and the assistant's generation and web searches. **Words** = words in the student's messages without IDE
context, attachments and system text (the prompts themselves, also when pasted).

| Metric | Task 1 before | Task 1 after | Task 2 before | Task 2 after |
|---|---|---|---|---|
| Student prompts | 12 (2 setup + 10) | 15 | 5 | 4¹ |
| Active time | 42 min | 118 min | 18 min | 19 min |
| Pauses > 30 min left out | 1 (34 h) | 4 (11.8 h) | 0 | 0 |
| Words written by the student | 2 748 | 2 102 (−24 %) | 1 356 | 686 (−49 %) |
| The 20 items requested manually before (NOTES §1 b) – covered by the agent unasked | – (11 requested) | **11 / 11** | – (9 requested) | **9 / 9** (3 incomplete²) |
| New requests beyond the skill's plan | – | 15 (≈ 6 real skill gaps³) | – | 2 (print full ADR, back-port corrections) |
| Corrections found by the student / agent | 6 / 0 | 4 / 3 | – | 2 / 0 (back-ported to the notes) |
| ADR versions | – | – | 5 | 3 |
| ADR review rounds by the student | – | – | 4 | 2 (+1 render confirmation) |
| ADR errors found in review – by the student / by the agent | – | – | 10 / 2 | 7 (6 real) / 0 |
| ADR errors caught by the skill's self-review before the student saw them | – | – | – | 8 |

¹ The 4th prompt only confirmed the diagram render and started the post-test steps. ² Requirements table (notifications missing),
module view (4 flows missing), Confirmation (no check for D3). ³ Assumption impact, no network call inside a transaction, payout
timing vs. holding limits, who handles alerts without ops, precise driver definition, sensitivity test.

## 3. Quality of the result – the two final ADRs
- **Same decision:** modular monolith on a managed EU PostgreSQL with the job queue in the database; same runner-up logic; A2 loses
  at money correctness. Both are MADR with TL;DR, assumptions, verbal ratings + decision rule, two diagrams, Confirmation, revisit
  table, related decisions.
- **Only in the after ADR:** precise driver definitions and a sensitivity test (winner robust to swapping D2/D3, depends on the broad
  "operability" definition); a stock-release rule split by "with / without a payment session"; heartbeats + external monitor; tests
  for revocation, OAuth linking and negative authorization; erasure as a module-level job; a walk-through of all 36 user stories;
  web-verified facts (iOS Web Push, Stripe session lifetime and 90-day holding limit, SEPA disputes) in the notes behind it.
- **Only in the before ADR:** the hybrid as a full column; migration and SQL-lint checks forbidding cross-schema FKs (the after run
  allows FKs on IDs); a separate `scheduler` process and a separate payment module; SSE and geocoding as named integrations;
  ADR-010 (technology stack) and the mobile-app question. Some domain decisions differ (before: card saved at booking, SEPA allowed
  for bookings, one active delivery per rider; after: pay within 24 h after acceptance, cards only, capacity as a parameter).
- **Assessment:** the after ADR is more internally consistent and better tested against its own rules; the before ADR went through
  more review rounds and therefore covers a few practical items (FK checks, stack ADR) the after run did not reach.

## 4. Did the student reach the goal faster?
**Mixed – less effort, not less time.**
- **Time:** no. Task 1 took 2.8× longer (118 vs. 42 min active); Task 2 took the same (19 vs. 18 min). The skill's deep mode adds an
  understanding question to every round, verifies facts on the web (16 searches/page reads) and writes longer answers; the student also chose
  the deep mode explicitly and asked many follow-ups. The original run was unusually fast because pre-written prompts were pasted
  every 3–5 minutes.
- **Effort and rework:** yes. 24 % (Task 1) and 49 % (Task 2) fewer words; all 20 items that had to be requested manually before
  were addressed unasked, 3 of them incompletely; the ADR needed 3 versions and 2 review rounds instead of 5 and 4; the student found 6 real ADR errors instead of 10,
  and the self-review caught 8 more before he saw the draft; the agent found 3 of its own errors during Task 1 (0 before).

## 5. Limitations
- Same system and same student: he knew the topic and the traps from the first run, which makes the second run easier regardless
  of the skills.
- The skills were derived from the first run, so they may be fitted to exactly these problems; a different system is the real test.
- This report is written by the assistant about its own run; the numbers come from scripts over the JSONL logs, the qualitative
  parts are not independent.
- One run only; no statistical meaning.
- In both runs the student prepared prompts with another AI assistant, so "words" measure what he pasted, not how long he thought.
- That helper assistant knew the results of the first run. It tried not to carry them into the new run, but some of the student's
  review points (e.g. notifications in the requirements table, geocoding) may have been influenced by that knowledge.
- Active time includes model latency and web searches, which depend on the day; the before window started with a setup day.
- Active time captures only what happens in the session: time spent with the helper assistant is counted only when the gap between
  two messages was shorter than 30 minutes.

## 6. Gaps found in the test and their fixes
The test ran on the **original skill version (644 lines)**; after the test the skills were updated (715 lines):

| Gap seen in the test | Fix | File |
|---|---|---|
| A PSP call was shown inside a DB transaction holding a row lock (A1.8-C1) | R10 "no network inside a transaction" + bank item with its failure | exploration SKILL.md, failure-question-bank.md |
| Decisions from read models / timeouts across components (A2.9, A2.10) | R11 "decide at the owner" + bank items (ask the owner, ledger with tombstones) | SKILL.md, bank §A, §C |
| Order of "record" vs. "act" for push vs. money | R12 | SKILL.md |
| Assumptions without their impact on the style; no operations model | Phase 1: impact per assumption, who reacts at night | SKILL.md |
| Missing deadlines after payment, safe automatic actions, alert routing, silent background failures | New bank section "Operations without an ops person" + time-driven items | failure-question-bank.md |
| Payout timing vs. provider holding limit, session lifetime, unknown creation outcome, key expiry, outage burst | Bank items in "External payment / checkout providers" | failure-question-bank.md |
| Driver definitions and sensitivity test requested by the student | Phase 3: precise definitions + mandatory sensitivity table | SKILL.md, assessment-template.md |
| Over-broad rule copied exactly (U1) | K4 extended: check all states the rule governs, correct the source | adr-review-checklist.md |
| Missing module flows (U2) – K6 sampled only 4–6 flows | K6 rewritten: every user story + assumptions, timers, back-office, erasure; owner of each data item | adr-review-checklist.md |
| Missing deployment edges (U3) | K5 extended to systems used by checks and mitigations | adr-review-checklist.md |
| No check for the 3rd driver (U4), unmotivated requirement gaps (U5), source gaps like geocoding (U7) | New K19 Confirmation coverage, K20 Requirements coverage, K21 Gaps in the source | adr-review-checklist.md |
| Corrections from the ADR review were not written back to the notes | Step 5: back-port corrections with the student's consent; skipped Step 0 → defaults "to confirm" | decision-record SKILL.md |

The generality grep after the update still finds no domain words in `.claude/skills`.

## 7. Next steps
- **Real generality test:** run the skills on another system from [Tasks/data](../Tasks/data/) – not EventTicket, because the
  neutralised skills use ticket and hotel examples; Teamify or RecipeCove are suitable.
- **Measure fast mode**, which was not used in this test.
- **Test the improved skills (715 lines)** – this test ran on the original version.
