# Notes template (NOTES.md)

Copy the skeleton below into the notes file at setup. Keep it updated after **every** round.

```markdown
# <System> – Architecture discussion notes

Running notes from the discussion between <user> and the coding assistant. Not a 1:1 transcript –
proposals, questions, answers, decisions and corrections.

Source requirements: <link>

**How to read:** items have stable IDs – `R<n>` requirements analysis, `A<k>.<n>` architecture k,
`H<n>` runner-up/hybrid critique, `C<n>` comparison. **Decision:** = agreed; **Correction:** = an earlier
statement was wrong (says what and who found it); *(superseded → ID)* = replaced by a later item.

**Contents** (update at the end)

---

## Run log
| Field | Value |
|---|---|
| Skill | architecture-exploration |
| Start | <date time> |
| End | <date time> |
| Mode | normal / fast |
| User prompts (total) | <n> |

| # | Time | Phase / architecture / round | Topics covered | User prompts | Requested by the user beyond the skill's plan | Corrections |
|---|---|---|---|---|---|---|
| 1 | | Setup | | 1 | – | – |

---

## 0. Requirements analysis
<a id="r1"></a>
**R1 – Actors / roles** …
<a id="r2"></a>
**R2 – Domain concepts** …
<a id="r3"></a>
**R3 – Hard spots** (category → user stories)
<a id="r4"></a>
**R4 – Assumptions** (status: proposed / confirmed by user)
<a id="r5"></a>
**R5 – Candidate styles** (approved by user: yes/no)

---

## Architecture 1 – <name>
*(proposed by assistant)*
Idea, diagram, components and data ownership, deployed processes.

### Discussion log
<a id="a1-1"></a>
**A1.1 – <topic>**
- User: <question / proposal>
- Assistant: <answer, position>
- **Decision:** …
- **Correction:** <what was wrong, found by whom> (if any)

<a id="a1-final"></a>
### Architecture 1 – Final assessment
(see assessment-template.md)

---

## Architecture 2 – … (same structure)

---

## Comparison & conclusion
(see assessment-template.md – contract for the ADR skill)
```

## Rules
- One ID per discussion item; never renumber. Corrections get their own line inside the item they fix
  and a *(superseded → ID)* marker where the old statement stands.
- Anchors: `<a id="…"></a>` on its own line, preceded by a blank line, directly before the item.
- Code/SQL snippets in notes must satisfy correctness rule R3 (all states, all invariants).
- Facts from the web: add the source URL. Unverifiable facts: **[unverified]**.
- Run log: count every user message that drives the work; in "Requested by the user beyond the skill's
  plan" write what the user had to ask for that the skill should have covered itself.
