---
name: architecture-decision-record
description: >-
  Write, review or revise an Architecture Decision Record (ADR) from an architecture discussion,
  meeting notes or exploration notes. Use whenever the user wants to document or record an architecture
  decision, turn a discussion into an ADR, improve or check an existing ADR – e.g. "write an ADR",
  "create an architecture decision record", "document the architecture decision", "record why we chose
  X", "review my ADR", "napíš ADR", "vytvor architecture decision record", "zdokumentuj rozhodnutie o
  architektúre", "rozhodnutie o architektúre", "zaznamenaj, prečo sme zvolili". Uses the notes as the
  only source (missing information becomes a question or an open question, never an invention), runs
  a built-in consistency self-review before showing any version, and logs every version in the notes.
---

# Architecture Decision Record

Goal: a concise ADR (default 2–4 pages ≈ 2 000 words) from which a newcomer understands **what** was
decided, **why** the other options lost, and **when to revisit** – and which is internally consistent.

## Ground rules
1. **Language.** These instructions are English. Talk to the user in their language. The ADR language is
   chosen by the user; default **English**.
2. **Single source.** Use only the given notes (and the requirements they cite). Every rating, claim and
   rule in the ADR must trace to a notes ID. Anything without a source becomes an **open question**.
   A new decision made during the ADR review is allowed only when the user asks for it, and is marked
   **"Changed by this ADR"** with the reason.
3. **Quote decisions precisely.** Do not paraphrase a rule into a stronger or different one
   (e.g. "no network I/O inside a transaction" ≠ "all side effects go through jobs").
4. **Self-review before showing.** Run `references/adr-review-checklist.md` on every version and fix
   findings first. Report the checklist result with the version.
5. **Unverifiable items are labelled**: diagrams that could not be rendered → "[unverified render –
   please check in mermaid.live or the GitHub preview]"; facts that could not be checked → [unverified].
6. **Log every version** in the ADR notes (what changed and why, errors found, who found them).

## Workflow

### Step 0 – Inputs and gaps (one exchange)
1. Locate the notes. If they follow the `architecture-exploration` contract, use the
   *Comparison & conclusion* section (H1, C0–C4) and the per-architecture final assessments.
2. **Foreign notes:** check that these exist: considered options, the reasons for the choice,
   decision drivers or enough material to derive them, assumptions, consequences/risks, open questions.
   If something is missing, **ask** (list exactly what is missing and why it is needed); do not guess.
3. Ask in one message (skip what the user already said): ADR language, audience, length budget, scope
   (one ADR per decision – which decision?), deciders / consulted, ADR file name and location, notes
   file for the ADR work (default `NOTES.md` next to the ADR, with a Run log as in the exploration
   skill's notes template).

### Step 1 – Drivers and decision rule
- Derive the driver priority from the **reasoning of the recommendation** in the notes (not from a
  generic list). Show the order and **ask the user to confirm** before drafting if it was not
  confirmed in the notes.
- Decision rule: options are compared driver by driver in priority order; the first difference decides.

### Step 2 – Draft (version v1)
- Follow `references/adr-template.md` (MADR-based). Status **Proposed** while under review.
- Architecture-independent decisions do not go into the body: list them under *Related decisions*
  with a one-sentence summary of what is already agreed, their status and a link to the source ID.
- Visuals: a comparison table with verbal ratings (always); a deployment/process view of the chosen
  option; a module/component view if the decision is about boundaries (e.g. modular monolith,
  services). No diagrams of rejected options.
- Links: if the notes have anchors (`<a id>`), link to them; if not, propose adding anchors (only
  anchors, no content change) and ask before editing the notes.

### Step 3 – Self-review (mandatory, before showing)
Run every check in `references/adr-review-checklist.md`. Fix what you can. Anything you cannot verify
(e.g. diagram rendering without a renderer) is labelled and listed for the user.

### Step 4 – Present
Start the reply with:
1. the format chosen and why,
2. what was deliberately left out and why,
3. which tables/diagrams were added and why,
4. the self-review result (checks passed / fixed / unverifiable),
5. points you are unsure about and need the user's decision on.
Then the link to the file (show the full text only if the user asks).

### Step 5 – Review iterations
- Apply the user's feedback, re-run the full checklist (changes often break other sections), log the
  version (v<n>: what changed, why, errors found, by whom).
- When the user finds an error the checklist missed, add it to the version log as a lesson.
- When a review changes or narrows a rule that comes from the source notes, **write a Correction back into
  the notes** (new ID, link to the ADR version, *superseded → ID* on the old statement) – only with the
  user's consent; the ADR then links the correction instead of saying "changed by this ADR".
- If the user asks to skip the Step 0 questions, record the chosen defaults as "to confirm" in the ADR
  notes and list them in the Step 4 reply.

### Step 6 – Finalise
- Status **Accepted** + date (only on the user's instruction), deciders/consulted filled.
- Final checklist run; anchors resolve; Run log closed (end time, prompts, versions).
- Summary table of versions in the notes.

## References
- `references/adr-template.md` – section skeleton with guidance.
- `references/adr-review-checklist.md` – self-review checks (each derived from a real review error).
