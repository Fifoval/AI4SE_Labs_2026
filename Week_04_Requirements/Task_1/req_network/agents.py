"""Graph nodes after preprocessing: LLM agents plus the deterministic glue between them."""
import hashlib
import json
import math
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from langgraph.types import Send

from . import prompts
from .config import (ASSIGN_BATCH, CACHE_DIR_NAME, MAX_AREA_SHARE, MAX_CONCURRENCY,
                     MAX_REVISIONS, MODELS, PAIR_BATCH, PAIR_NEIGHBORS, PRIORITIES,
                     PRIORITY_KEYWORDS, PRIORITY_MARKER, PRIORITY_SCALE)
from .llm import structured_call
from .schemas import (ArbiterDecision, AssignmentBatch, ConsolidationResult, CriticReport,
                      DuplicateCheck, ExtractionResult, FusedRequirement, IssueList,
                      StructurePlan)
from .state import GraphState

FALLBACK_AREA = {"code": "OTH", "name": "Other Requirements",
                 "description": "Requirements not assigned to any other area."}


def _priority_text() -> str:
    return "\n".join(f"- {k}: {v}" for k, v in PRIORITY_SCALE.items())


def _doc_index(state: GraphState) -> dict:
    return {d["doc_id"]: d for d in state["documents"]}


# --- extraction (LLM, fan-out per chunk) ---------------------------------------
def fan_out_extraction(state: GraphState) -> list[Send]:
    cache_dir = str(Path(state["output_dir"]) / CACHE_DIR_NAME)
    return [Send("extract", {**chunk, "cache_dir": cache_dir}) for chunk in state["chunks"]]


def extract(chunk: dict) -> dict:
    user = (f"Document: {chunk['path']} (type: {chunk['doc_type']}, "
            f"date: {chunk['date'] or 'unknown'})\n"
            f"Fragment {chunk['chunk_id']}:\n\"\"\"\n{chunk['text']}\n\"\"\"")
    # cache keyed by model + prompt + input, so reruns skip finished chunks
    key = hashlib.sha256(f"{MODELS['extractor']}\n{prompts.EXTRACTOR}\n{user}".encode()).hexdigest()
    cache = Path(chunk["cache_dir"]) / f"extract_{key[:24]}.json"
    if cache.exists():
        items = json.loads(cache.read_text(encoding="utf-8"))
        print(f"[extract] {chunk['chunk_id']}: {len(items)} items (cached)")
        return {"raw_items": items}
    try:
        result: ExtractionResult = structured_call("extractor", ExtractionResult,
                                                   prompts.EXTRACTOR, user)
    except Exception as exc:  # keep the run alive, report in the document
        print(f"[extract] {chunk['chunk_id']} FAILED: {exc}")
        return {"errors": [f"Extraction of {chunk['chunk_id']} ({chunk['path']}) failed: {exc}"]}
    items = [{**it.model_dump(), "doc_id": chunk["doc_id"], "chunk_id": chunk["chunk_id"]}
             for it in result.items]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    print(f"[extract] {chunk['chunk_id']}: {len(items)} items")
    return {"raw_items": items}


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _quote_found(quote: str, doc_ngrams: set, doc_text: str, n: int = 4) -> bool:
    """True if the quote occurs in the document (tolerating whitespace, punctuation,
    and small edits: at least 60 % of its word 4-grams must appear in the document)."""
    words = _words(quote)
    if len(words) < n:
        return " ".join(words) in doc_text
    grams = [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]
    return sum(g in doc_ngrams for g in grams) / len(grams) >= 0.6


def _source_priority(quote: str, paragraphs: list[tuple[str, str]], hint: str) -> tuple[str, str]:
    """Priority evidenced by the source text: an explicit priority marker in the paragraph
    holding the quote wins; otherwise modal keywords in the quote; else the LLM hint."""
    head = " ".join(_words(quote)[:6])
    raw, norm = next(((r, n) for r, n in paragraphs if head and head in n), ("", ""))
    if m := re.search(PRIORITY_MARKER, raw, re.IGNORECASE):
        level = {"high": "Must", "medium": "Should", "low": "Could"}[m.group(1).lower()]
        return level, f"explicit marker \"{m.group(0)}\""
    for level, pattern in PRIORITY_KEYWORDS:
        if m := re.search(pattern, quote, re.IGNORECASE):
            return level, f"keyword \"{m.group(0)}\" in the quote"
    # nearest modal keyword before the quote in the same paragraph (e.g. the lead
    # sentence of a bulleted list: "Staff should be able to: - ...")
    prefix = norm[:norm.find(head)] if norm else ""
    found = [(m.start(), level, m.group(0)) for level, pattern in PRIORITY_KEYWORDS
             for m in re.finditer(pattern, prefix)]
    if found:
        _, level, word = max(found)
        return level, f"keyword \"{word}\" in the source paragraph"
    # no wording in the source: neutral default; Must always needs textual evidence
    if hint == "Could":
        return "Could", "no priority wording in source; extractor judged it a wish"
    return "Should", "no priority wording in source; neutral default"


def collect_candidates(state: GraphState) -> dict:
    """Deterministic: stable candidate ids, quote verification against the source text
    (hallucination check for tracing), priority evidence from the source text,
    split valid items from extractor rejects."""
    norm, paras = {}, {}
    for d in state["documents"]:
        words = _words(d["text"])
        norm[d["doc_id"]] = (set(zip(*(words[i:] for i in range(4)))), " ".join(words))
        paras[d["doc_id"]] = [(p, " ".join(_words(p))) for p in re.split(r"\n\s*\n", d["text"])]
    items = sorted(state.get("raw_items", []), key=lambda it: it["chunk_id"])
    candidates, rejected = [], []
    for i, it in enumerate(items, 1):
        level, basis = _source_priority(it["quote"], paras[it["doc_id"]], it["priority_hint"])
        it = {**it, "cid": f"C{i:03d}",
              "quote_verified": _quote_found(it["quote"], *norm[it["doc_id"]]),
              "source_priority": level, "priority_basis": basis}
        (candidates if it["status"] == "valid" else rejected).append(it)
    unverified = sum(not c["quote_verified"] for c in candidates)
    levels = {p: sum(c["source_priority"] == p for c in candidates) for p in PRIORITIES}
    markers = sum(c["priority_basis"].startswith("explicit") for c in candidates)
    print(f"[collect] {len(candidates)} candidates ({unverified} with unverified quote), "
          f"{len(rejected)} rejected by extractor; source priority {levels}, "
          f"{markers} from explicit markers")
    return {"candidates": candidates, "rejected": rejected}


# --- structure: taxonomy + glossary (LLM) ----------------------------------------
def plan_structure(state: GraphState) -> dict:
    cands = state["candidates"]
    names = "\n".join(f"- {c['name']}" for c in cands)
    plan: StructurePlan = structured_call("structurer", StructurePlan, prompts.STRUCTURER,
                                          f"Candidate requirement names:\n{names}")
    areas = [{**a.model_dump(), "code": a.code.strip().upper()} for a in plan.areas]
    assignments = _assign(cands, areas)

    # deterministic balance check: split oversized areas so that one consolidation
    # call does not have to digest a large share of the corpus (prevents over-merging)
    limit = max(ASSIGN_BATCH // 2, int(MAX_AREA_SHARE * len(cands)))
    for area in list(areas):
        members = [c for c in cands if assignments[c["cid"]] == area["code"]]
        if len(members) <= limit or area is FALLBACK_AREA:
            continue
        names = "\n".join(f"- {c['name']}" for c in members)
        sub: StructurePlan = structured_call(
            "structurer", StructurePlan, prompts.SPLITTER,
            f"Area to split: {area['code']} - {area['name']}: {area['description']}\n"
            f"Existing area codes (do not reuse): {', '.join(a['code'] for a in areas)}\n\n"
            f"Candidate requirement names:\n{names}")
        taken = {a["code"] for a in areas}
        subareas = []
        for a in sub.areas:
            code = a.code.strip().upper()
            while code in taken:
                code += "X"
            taken.add(code)
            subareas.append({**a.model_dump(), "code": code})
        if len(subareas) < 2:
            continue
        areas[areas.index(area):areas.index(area) + 1] = subareas
        assignments.update(_assign(members, subareas))
        print(f"[structure] split {area['code']} ({len(members)} candidates) into "
              f"{', '.join(a['code'] for a in subareas)}")
    if FALLBACK_AREA["code"] in assignments.values():
        areas.append(FALLBACK_AREA)
    sizes = {a["code"]: sum(v == a["code"] for v in assignments.values()) for a in areas}
    print(f"[structure] {len(areas)} areas {sizes}, {len(plan.glossary)} glossary terms")
    return {"areas": areas, "glossary": [g.model_dump() for g in plan.glossary],
            "assignments": assignments, "revision": 0, "feedback": {}, "known_issues": []}


def _assign(cands: list[dict], areas: list[dict]) -> dict:
    """LLM assignment of candidates to areas in parallel batches; deterministic repair
    puts every unassigned / wrongly assigned candidate into the fallback area [OS8]."""
    codes = {a["code"] for a in areas}
    areas_txt = "\n".join(f"{a['code']}: {a['name']} - {a['description']}" for a in areas)

    def batch_call(batch):
        lines = "\n".join(f"{c['cid']} | {c['name']} | {c['statement']}" for c in batch)
        res: AssignmentBatch = structured_call("structurer", AssignmentBatch, prompts.ASSIGNER,
                                               f"Areas:\n{areas_txt}\n\nCandidates:\n{lines}")
        return res.assignments

    batches = [cands[i:i + ASSIGN_BATCH] for i in range(0, len(cands), ASSIGN_BATCH)]
    with ThreadPoolExecutor(MAX_CONCURRENCY) as pool:
        raw = {a.cid: a.area_code.strip().upper()
               for res in pool.map(batch_call, batches) for a in res}
    return {c["cid"]: raw[c["cid"]] if raw.get(c["cid"]) in codes else FALLBACK_AREA["code"]
            for c in cands}


# --- consolidation (LLM, fan-out per area) ---------------------------------------
def _area_payload(state: GraphState, area: dict, feedback: list[str]) -> dict:
    docs = _doc_index(state)
    cands = [{"cid": c["cid"], "name": c["name"], "statement": c["statement"],
              "source_priority": c["source_priority"], "priority_basis": c["priority_basis"],
              "doc_id": c["doc_id"],
              "doc_type": docs[c["doc_id"]]["doc_type"], "date": docs[c["doc_id"]]["date"],
              "authority": docs[c["doc_id"]]["authority"]}
             for c in state["candidates"] if state["assignments"][c["cid"]] == area["code"]]
    return {"area": area, "candidates": cands, "glossary": state["glossary"],
            "feedback": feedback,
            "previous": state.get("area_results", {}).get(area["code"]) if feedback else None}


def fan_out_consolidation(state: GraphState) -> list[Send]:
    return [Send("consolidate", p) for a in state["areas"]
            if (p := _area_payload(state, a, []))["candidates"]]


def consolidate(payload: dict) -> dict:
    area = payload["area"]
    glossary = "\n".join(f"- {g['term']}: {g['definition']} (avoid: {', '.join(g['synonyms_to_avoid']) or '-'})"
                         for g in payload["glossary"])
    user = (f"Feature area {area['code']} - {area['name']}: {area['description']}\n\n"
            f"Priority scale:\n{_priority_text()}\n\nGlossary:\n{glossary}\n\n"
            f"Candidates (JSON):\n{json.dumps(payload['candidates'], indent=1)}")
    if payload["feedback"]:
        user += ("\n\nYour previous output for this area:\n"
                 f"{json.dumps(payload['previous'], indent=1)}\n\n"
                 "A reviewer requires these fixes (apply them, keep everything else):\n- "
                 + "\n- ".join(payload["feedback"]))
    try:
        result: ConsolidationResult = structured_call("consolidator", ConsolidationResult,
                                                      prompts.CONSOLIDATOR, user)
    except Exception as exc:  # area stays unprocessed -> coverage gap -> critic loop retries
        print(f"[consolidate] {area['code']} FAILED: {exc}")
        return {"errors": [f"Consolidation of area {area['code']} failed: {exc}"]}
    # deterministic sanitising: only known candidate ids, valid and justified priorities
    by_cid = {c["cid"]: c for c in payload["candidates"]}
    data = result.model_dump()
    for r in data["requirements"]:
        r["candidate_ids"] = [c for c in r["candidate_ids"] if c in by_cid]
        if r["priority"] not in PRIORITIES:
            r["priority"] = "Should"
        # guard [OS6]: an explicit high-priority marker in a source always means Must;
        # Must is only allowed when some source text states the need as mandatory
        merged = [by_cid[c] for c in r["candidate_ids"]]
        marked = [c for c in merged if c["priority_basis"].startswith("explicit")
                  and c["source_priority"] == "Must"]
        if marked and r["priority"] != "Must":
            r["priority_rationale"] += (f" (Adjusted to Must: {marked[0]['priority_basis']} "
                                        f"in {marked[0]['doc_id']}.)")
            r["priority"] = "Must"
        elif r["priority"] == "Must" and merged and not any(
                c["source_priority"] == "Must" for c in merged):
            r["priority"] = "Should"
            r["priority_rationale"] += (" (Adjusted from Must: no source text states it as "
                                        "mandatory.)")
    data["requirements"] = [r for r in data["requirements"] if r["candidate_ids"]]
    for d in data["discarded"]:
        d["candidate_ids"] = [c for c in d["candidate_ids"] if c in by_cid]
    print(f"[consolidate] {area['code']}: {len(payload['candidates'])} candidates -> "
          f"{len(data['requirements'])} requirements, {len(data['discarded'])} discarded")
    return {"area_results": {area["code"]: data}}


# --- numbering, tracing, coverage (deterministic) ---------------------------------
def number_and_trace(state: GraphState) -> dict:
    by_cid = {c["cid"]: c for c in state["candidates"]}
    docs = _doc_index(state)
    requirements, gaps = [], {}
    for area in state["areas"]:
        res = state.get("area_results", {}).get(area["code"])
        assigned = {cid for cid, code in state["assignments"].items() if code == area["code"]}
        if not res:
            if assigned:
                gaps[area["code"]] = sorted(assigned)
            continue
        used = set()
        for n, r in enumerate(res["requirements"], 1):
            used.update(r["candidate_ids"])
            evidence, verified = {}, {}
            for cid in r["candidate_ids"]:   # per source keep a verified quote if any
                c = by_cid[cid]
                if c["doc_id"] not in evidence or (c["quote_verified"] and not verified[c["doc_id"]]):
                    evidence[c["doc_id"]] = c["quote"]
                    verified[c["doc_id"]] = c["quote_verified"]
            requirements.append({
                "id": f"REQ-{area['code']}-{n:03d}", "area": area["code"],
                "name": r["name"], "description": r["description"],
                "priority": r["priority"], "priority_rationale": r["priority_rationale"],
                "candidate_ids": r["candidate_ids"],
                "sources": sorted(evidence), "evidence": evidence,
                "evidence_verified": verified,
                "priority_evidence": sorted({f"{by_cid[c]['doc_id']}: {by_cid[c]['priority_basis']}"
                                             for c in r["candidate_ids"]
                                             if by_cid[c]["source_priority"] == r["priority"]})[:3],
                "authority": max(docs[d]["authority"] for d in evidence),
                "latest_date": max(docs[d]["date"] for d in evidence),
            })
        for d in res["discarded"]:
            used.update(d["candidate_ids"])
        if missing := sorted(assigned - used):
            gaps[area["code"]] = missing
    fidelity = _fidelity_gaps(requirements, by_cid)
    print(f"[trace] {len(requirements)} requirements, coverage gaps: "
          f"{sum(map(len, gaps.values()))} candidates, merge-fidelity warnings: "
          f"{sum(map(len, fidelity.values()))}")
    return {"requirements": requirements, "coverage_gaps": gaps, "fidelity_gaps": fidelity}


def _stems(text: str) -> set[str]:
    return {w[:-1] if w.endswith("s") and len(w) > 4 else w
            for w in _words(text) if w not in _STOP and len(w) > 3}


def _fidelity_gaps(requirements: list[dict], by_cid: dict) -> dict:
    """Deterministic merge-fidelity check [OS8]: a candidate merged into a requirement
    whose text reflects less than a third of the content words of the candidate's name
    was probably absorbed without its content (over-merging)."""
    out: dict[str, list[str]] = {}
    for r in requirements:
        text = _stems(f"{r['name']} {r['description']}")
        for cid in r["candidate_ids"]:
            name = _stems(by_cid[cid]["name"])
            if name and len(name & text) / len(name) < 1 / 3:
                out.setdefault(r["area"], []).append(
                    f"{cid} \"{by_cid[cid]['name']}\" was merged into {r['id']} "
                    f"\"{r['name']}\"")
    return out


# --- cross-area conflicts and duplicates (LLM) ------------------------------------
def _key(r: dict) -> str:
    """Identity of a requirement that survives renumbering between review rounds."""
    return f"{r['area']}::{r['name'].strip().lower()}"


def _remember(issues: list[dict], reqs: list[dict], known: list[dict]) -> list[dict]:
    """Add id-based issues to the persistent, name-keyed issue memory (deduplicated)."""
    by_id = {r["id"]: r for r in reqs}
    seen = {(k["kind"], frozenset(k["keys"])) for k in known}
    out = list(known)
    for i in issues:
        keys = [_key(by_id[x]) for x in i["requirement_ids"]]
        if (i["kind"], frozenset(keys)) not in seen:
            seen.add((i["kind"], frozenset(keys)))
            out.append({"kind": i["kind"], "keys": keys, "explanation": i["explanation"]})
    return out


_STOP = set("the a an and or of to for in on by with shall system be is are that this as from "
             "at it its can should must may each all any such which their they will not into "
             "via per".split())


def _similar_pairs(reqs: list[dict], k: int) -> list[tuple[int, int]]:
    """Deterministic blocking: TF-IDF cosine over name + description; for every
    requirement keep its k most similar requirements as candidate pairs."""
    toks = [[w for w in _words(f"{r['name']} {r['name']} {r['description']}")
             if w not in _STOP and len(w) > 2] for r in reqs]
    df = Counter(w for t in toks for w in set(t))
    vecs = []
    for t in toks:
        v = {w: (1 + math.log(c)) * math.log(len(reqs) / df[w]) for w, c in Counter(t).items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({w: x / norm for w, x in v.items()})
    pairs = set()
    for i, vi in enumerate(vecs):
        sims = sorted(((sum(x * vecs[j].get(w, 0.0) for w, x in vi.items()), j)
                       for j in range(len(vecs)) if j != i), reverse=True)[:k]
        pairs.update(tuple(sorted((i, j))) for s, j in sims if s > 0)
    return sorted(pairs)


def detect_conflicts(state: GraphState) -> dict:
    """Candidate pairs from deterministic similarity blocking, judged by the LLM in
    parallel batches (a single pass over all ~N^2/2 pairs is too shallow)."""
    docs = _doc_index(state)
    reqs = state["requirements"]

    def fmt(r):
        src = ", ".join(f"{d} {docs[d]['doc_type']} {docs[d]['date']}" for d in r["sources"])
        return f"{r['id']} {r['name']} (sources: {src}): {r['description']}"

    pairs = _similar_pairs(reqs, PAIR_NEIGHBORS)
    batches = [pairs[i:i + PAIR_BATCH] for i in range(0, len(pairs), PAIR_BATCH)]

    def judge(batch):
        involved = sorted({i for p in batch for i in p})
        user = ("Requirements:\n" + "\n".join(fmt(reqs[i]) for i in involved)
                + "\n\nPairs to check:\n"
                + "\n".join(f"- {reqs[a]['id']} vs {reqs[b]['id']}" for a, b in batch))
        allowed = {frozenset((reqs[a]["id"], reqs[b]["id"])) for a, b in batch}
        res: IssueList = structured_call("conflict", IssueList, prompts.CONFLICT, user)
        return [i.model_dump() for i in res.issues
                if len(set(i.requirement_ids)) == 2 and frozenset(i.requirement_ids) in allowed]

    new, errors = [], []
    with ThreadPoolExecutor(MAX_CONCURRENCY) as pool:
        for batch, fut in [(b, pool.submit(judge, b)) for b in batches]:
            try:
                new.extend(fut.result())
            except Exception as exc:
                print(f"[conflicts] batch FAILED: {exc}")
                errors.append(f"Conflict check of {len(batch)} pairs failed: {exc}")
    # issues found in earlier rounds (detector or critic) are re-applied while both
    # requirements still exist, so a merge or blacklist decision is not lost
    known = _remember(new, reqs, state.get("known_issues", []))
    id_of = {_key(r): r["id"] for r in reqs}
    issues = [{"kind": k["kind"], "requirement_ids": [id_of[x] for x in k["keys"]],
               "explanation": k["explanation"]}
              for k in known if all(x in id_of for x in k["keys"])]
    print(f"[conflicts] {len(pairs)} similar pairs checked in {len(batches)} batches: "
          f"{len(new)} issues found, {len(issues)} applicable in total")
    return {"issues": issues, "known_issues": known, "errors": errors}


def _strength(r: dict) -> tuple:
    return (r["authority"], r["latest_date"])


def resolve_conflicts(state: GraphState) -> dict:
    """Duplicates are merged. A reported conflict is first verified by an independent
    model; unconfirmed conflicts become open issues (both requirements kept). Confirmed
    conflicts are resolved by source authority and recency, the verifier decides ties."""
    docs = _doc_index(state)
    reqs = {r["id"]: dict(r) for r in state["requirements"]}
    blacklist, merged, tensions = [], [], []
    rank = {p: i for i, p in enumerate(reversed(PRIORITIES))}
    order = {"duplicate": 0, "conflict": 1, "tension": 2}
    rejected_dups = fused_count = 0

    def describe(r):
        return ", ".join(f"{d} ({docs[d]['doc_type']}, {docs[d]['date'] or 'undated'})"
                         for d in r["sources"])

    alias: dict[str, str] = {}      # merged duplicate -> requirement it was merged into

    def resolve(x):
        while x in alias:
            x = alias[x]
        return x

    for issue in sorted(state["issues"], key=lambda i: order[i["kind"]]):
        a_id, b_id = (resolve(x) for x in issue["requirement_ids"])
        if a_id == b_id or a_id not in reqs or b_id not in reqs:
            continue
        a, b = reqs[a_id], reqs[b_id]
        if issue["kind"] == "duplicate":
            keep, drop = sorted([a, b], key=lambda r: (rank[r["priority"]], len(r["sources"])),
                                reverse=True)
            try:   # merge only if an independent check confirms nothing would be lost
                check: DuplicateCheck = structured_call(
                    "verifier", DuplicateCheck, prompts.DUPLICATE_CHECK,
                    f"KEPT {keep['id']}: {keep['name']}\n{keep['description']}\n\n"
                    f"REMOVED {drop['id']}: {drop['name']}\n{drop['description']}")
            except Exception as exc:
                print(f"[resolve] duplicate check {drop['id']} FAILED: {exc}")
                continue
            if not check.genuine_duplicate:
                # same need, complementary details: fuse both texts into one requirement,
                # accepted only if the fused text reflects both original names
                try:
                    fused: FusedRequirement = structured_call(
                        "consolidator", FusedRequirement, prompts.FUSE,
                        "\n\n".join(f"{r['id']}: {r['name']}\n{r['description']}"
                                    for r in (keep, drop)))
                except Exception as exc:
                    print(f"[resolve] fusion {keep['id']}+{drop['id']} FAILED: {exc}")
                    rejected_dups += 1
                    continue
                text = _stems(f"{fused.name} {fused.description}")
                if any((n := _stems(r["name"])) and len(n & text) / len(n) < 1 / 3
                       for r in (keep, drop)):
                    rejected_dups += 1
                    continue
                keep["name"], keep["description"] = fused.name, fused.description
                issue = {**issue, "explanation": f"{issue['explanation']} Texts fused so that "
                                                 f"the details of both are kept: {check.reason}"}
                fused_count += 1
            keep["candidate_ids"] = keep["candidate_ids"] + drop["candidate_ids"]
            keep["evidence"] = {**drop["evidence"], **keep["evidence"]}
            keep["evidence_verified"] = {**drop["evidence_verified"], **keep["evidence_verified"]}
            keep["sources"] = sorted(keep["evidence"])
            merged.append({"removed_id": drop["id"], "name": drop["name"],
                           "kept_id": keep["id"], "explanation": issue["explanation"]})
            alias[drop["id"]] = keep["id"]
            del reqs[drop["id"]]
            continue
        if issue["kind"] == "tension":
            tensions.append({"ids": [a_id, b_id], "explanation": issue["explanation"],
                             "source": "detector"})
            continue
        try:
            decision: ArbiterDecision = structured_call(
                "verifier", ArbiterDecision, prompts.ARBITER,
                f"Reported conflict: {issue['explanation']}\n\n"
                + "\n\n".join(f"{r['id']}: {r['name']}\n{r['description']}\nSources: {describe(r)}"
                              for r in (a, b)))
        except Exception as exc:  # unverified conflicts never delete a requirement
            tensions.append({"ids": [a_id, b_id], "source": "verification failed",
                             "explanation": f"{issue['explanation']} (verification failed: {exc})"})
            continue
        if not decision.genuine_conflict:
            tensions.append({"ids": [a_id, b_id], "source": "conflict not confirmed by verifier",
                             "explanation": f"{issue['explanation']} Verifier: {decision.reason}"})
            continue
        if _strength(a) != _strength(b):
            win, lose = (a, b) if _strength(a) > _strength(b) else (b, a)
            reason = (f"Conflicts with {win['id']}: {issue['explanation']} Conflict confirmed by "
                      f"an independent verifier and resolved by source authority/recency: "
                      f"{win['id']} is backed by {describe(win)}, {lose['id']} only by "
                      f"{describe(lose)}.")
        elif decision.winner_id in (a_id, b_id):
            win, lose = (a, b) if decision.winner_id == a_id else (b, a)
            reason = (f"Conflicts with {win['id']}: {issue['explanation']} Sources are equally "
                      f"authoritative; verifier decision: {decision.reason}")
        else:
            tensions.append({"ids": [a_id, b_id], "source": "verifier gave no winner",
                             "explanation": f"{issue['explanation']} Verifier: {decision.reason}"})
            continue
        blacklist.append({"id": lose["id"], "name": lose["name"],
                          "description": lose["description"], "sources": lose["sources"],
                          "reason": reason})
        del reqs[lose["id"]]
    kept = [r for r in state["requirements"] if r["id"] in reqs]
    seen, unique = set(), []
    for t in tensions:   # one open issue per pair; verifier-checked entries come first
        pair = frozenset(t["ids"])
        if pair not in seen and all(x in reqs for x in t["ids"]):
            seen.add(pair)
            unique.append(t)
    tensions = unique
    for t in tensions:
        t["names"] = [reqs[x]["name"] for x in t["ids"]]
    print(f"[resolve] {len(blacklist)} confirmed conflicts blacklisted, {len(merged)} duplicates "
          f"merged ({fused_count} of them by fusing both texts; {rejected_dups} reported "
          f"duplicates kept apart), "
          f"{len(tensions)} open issues (tensions / unconfirmed conflicts)")
    return {"requirements": [reqs[r["id"]] for r in kept],
            "conflict_blacklist": blacklist, "merged_duplicates": merged, "tensions": tensions}


# --- critic (deterministic coverage check + LLM review) ----------------------------
def critic(state: GraphState) -> dict:
    gaps = state.get("coverage_gaps", {})
    by_cid = {c["cid"]: c for c in state["candidates"]}
    reqs_txt = "\n\n".join(f"{r['id']} [{r['priority']}] {r['name']} (sources: {', '.join(r['sources'])})\n"
                           f"{r['description']}" for r in state["requirements"])
    discarded = [f"{d['name']}: {d['reason']}" for res in state["area_results"].values()
                 for d in res["discarded"]]
    discarded += [f"{b['id']} {b['name']}: {b['reason']}" for b in state["conflict_blacklist"]]
    gaps_txt = "\n".join(f"{code}: " + "; ".join(f"{cid} {by_cid[cid]['statement']}" for cid in cids)
                         for code, cids in gaps.items()) or "none"
    glossary = ", ".join(g["term"] for g in state["glossary"])
    tensions = "\n".join(f"{' vs '.join(t['ids'])}: {t['explanation']}"
                         for t in state.get("tensions", [])) or "none"
    user = (f"Areas: {', '.join(a['code'] + ' ' + a['name'] for a in state['areas'])}\n"
            f"Glossary terms: {glossary}\n\nRequirements:\n{reqs_txt}\n\n"
            f"Discarded items:\n" + ("\n".join(discarded) or "none") +
            f"\n\nOpen issues already documented (both requirements kept on purpose; do not "
            f"re-report these pairs):\n{tensions}"
            f"\n\nCoverage gaps (candidates neither used nor discarded):\n{gaps_txt}")
    try:
        report: CriticReport = structured_call("critic", CriticReport, prompts.CRITIC, user)
    except Exception as exc:  # no review possible: keep deterministic gap feedback only
        print(f"[critic] FAILED: {exc}")
        report = CriticReport(passed=True, summary=f"Review failed: {exc}", issues=[])

    codes = {a["code"] for a in state["areas"]}
    ids = {r["id"] for r in state["requirements"]}
    feedback: dict[str, list[str]] = {}
    pair_issues = []
    for issue in ([] if report.passed else report.issues):
        if issue.kind in ("duplicate", "conflict"):
            if len(set(issue.requirement_ids)) == 2 and set(issue.requirement_ids) <= ids:
                pair_issues.append({"kind": issue.kind, "requirement_ids": issue.requirement_ids,
                                    "explanation": issue.problem})
            continue
        code = issue.area_code.strip().upper()
        if code not in codes:   # derive the area from a referenced requirement id
            code = next((r["area"] for r in state["requirements"]
                         if r["id"] in issue.requirement_ids), code)
        if code in codes:
            ref = f" ({', '.join(issue.requirement_ids)})" if issue.requirement_ids else ""
            feedback.setdefault(code, []).append(f"{issue.problem}{ref} -> {issue.fix_instruction}")
    known = _remember(pair_issues, state["requirements"], state.get("known_issues", []))
    new_pairs = len(known) - len(state.get("known_issues", []))
    for code, cids in gaps.items():
        feedback.setdefault(code, []).append(
            f"Candidates {', '.join(cids)} were neither used in a requirement nor discarded. "
            "Incorporate each of them or discard it with a reason.")
    fidelity = state.get("fidelity_gaps", {})
    for code, items in fidelity.items():
        if code in codes:
            feedback.setdefault(code, []).append(
                "Merge-fidelity check: the content of these candidates is not reflected in the "
                "requirement they were merged into: " + "; ".join(items) + ". For each, either "
                "state its specific content explicitly in that requirement's description or, "
                "if it is a distinct capability (e.g. a distinct report), make it a separate "
                "requirement.")
    revision = state.get("revision", 0) + 1
    history = state.get("critic_history", []) + [{
        "revision": revision, "passed": report.passed and not gaps and not fidelity,
        "summary": report.summary,
        "issues": sum(map(len, feedback.values())) + len(pair_issues)}]
    print(f"[critic] round {revision}: passed={report.passed}, gaps={len(gaps)}, "
          f"areas to revise={sorted(feedback)}, new duplicate/conflict pairs={new_pairs}")
    return {"feedback": feedback, "revision": revision, "known_issues": known,
            "pending_pairs": new_pairs,
            "critic_summary": report.summary, "critic_history": history}


def route_after_critic(state: GraphState):
    """Feedback loop: flagged areas go back to the consolidator; if the critic only found
    duplicate/conflict pairs, re-run tracing and resolution; otherwise finish."""
    if state["revision"] > MAX_REVISIONS:
        return "render"
    if state["feedback"]:
        areas = {a["code"]: a for a in state["areas"]}
        return [Send("consolidate", _area_payload(state, areas[code], fb))
                for code, fb in state["feedback"].items()]
    if state.get("pending_pairs"):
        return "number_and_trace"
    return "render"
