# ADR template (MADR-based)

Why MADR and not Nygard: the decision usually compares several options in depth; MADR has *Decision
drivers*, *Considered options*, *Pros and cons* and *Confirmation*. Additions below (TL;DR, assumptions,
traceability, revisit table, related decisions) came from real reviews.

```markdown
# ADR-<nnn>: <decision as a short noun phrase> – <chosen option>

| | |
|---|---|
| **Status** | Proposed (under review) → Accepted |
| **Date** | <YYYY-MM-DD> |
| **Deciders** | <names> |
| **Consulted** | <e.g. AI coding assistant> |
| **Source** | <link to notes> |

> **TL;DR.** 3–4 sentences: what was decided, the main reason, the main trigger to revisit.
> Must match the body (decision, drivers, revisit table).

## Context and problem statement
Short system description (bullets), integrations, why regulation applies (actual legal trigger).
**Question:** one sentence.

### Requirements that shaped the decision
| Requirements / user stories | What makes them hard | Driver / consequence |
(max ~6 rows; every row maps to a driver)

### Assumptions
**Valid only while these hold – if one breaks, revisit.** Numbered (scale, peaks, team, payments/
regulatory model, …). Each must come from the notes (confirmed by the user).

## Decision drivers (in priority order)
D1 … Dn, one line each. The order reflects the real reasoning; the lowest priority is stated explicitly.

## Considered options
One bullet per option (one or two sentences).

### Comparison
| Driver | Option A | Option B | … |
| **D1** … | **Strong** – reason | **Weak** – reason | … |
Ratings: Strong / Acceptable / Weak, one-sentence reason each (traceable to notes IDs).
Cost row: relative estimates + date + source; no absolute prices.
**Reading the table:** ratings are not added; compare driver by driver in priority order, the first
difference decides. Then: where the chosen option beats each other option.

## Decision outcome
**Chosen option: …** Reasons → comparison (no repetition).
What the decision includes: components/modules, process types, key rules (quoted exactly from the
notes), infrastructure.

#### Deployment view – <what it shows>
Mermaid diagram: processes, stores, **every external integration from Context**, sync vs. async edges
labelled consistently with the rules.

#### Module / component view – <what it shows> (if boundaries matter)
Mermaid diagram: modules with owned data, allowed dependencies (calls vs. events), deliberate
exceptions highlighted. Legend: arrow types, **explicit rules for allowed but undrawn dependencies**,
"any other undrawn dependency is forbidden".

### Consequences
**Positive** – only what is not already in the comparison.
**Negative, risks and mitigations** – one table (negative/risk → mitigation); risks from the notes'
final assessment merged here.

### Confirmation
| # | Check | Proves |
Concrete CI checks and tests that show the implementation follows the decision (architecture tests,
schema/FK checks, concurrency tests that prove the property, load test with a target). Each must be
consistent with the diagrams.

### When to revisit
| Trigger (usually a broken assumption – cite its number) | Re-evaluate towards |

## Why the other options were rejected
One sentence per option, linked to its source in the notes (details are in the table).

## Related decisions (should get their own ADRs)
Status line (agreed in notes, ADR not written / not decided yet).
| Proposed ADR | Already agreed | Source |

## Open questions
Numbered; only items that do not change this decision; link to the notes' full list.

*Format: MADR. Links to the notes sections.*
```
