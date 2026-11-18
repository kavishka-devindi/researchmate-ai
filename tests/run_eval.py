"""Evaluation of retrieval, RAG answers and agent tool choices.

Run from the project root, with your virtual environment active:
    python -m tests.run_eval                   full run (RAG and agent)
    python -m tests.run_eval --skip-agent      retrieval and RAG only (fewer AI requests)
    python -m tests.run_eval --limit 5         only the first 5 questions
    python -m tests.run_eval --score-faithfulness    after you filled in the manual sheet
"""
import argparse
import csv
import json
import os
import re
import time
from datetime import datetime

from src import config
from src.agent import run_agent
from src.pdf_processing import CHUNK_SIZE, CHUNK_OVERLAP
from src.rag import answer_question, NOT_FOUND, CITATION_PATTERN, TOP_K, MIN_SCORE, _norm
from src.vector_store import search_chunks, stored_documents, get_document_chunks

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_PATH = os.path.join(TESTS_DIR, "eval_questions.json")
RESULTS_DIR = os.path.join(TESTS_DIR, "results")
SHEET_PATH = os.path.join(RESULTS_DIR, "faithfulness_sheet.csv")
SEARCH_TOOLS = {"answer_from_documents", "search_documents"}


# ---------- small helpers ----------
def ratio(num, den):
    return "n/a" if den == 0 else f"{num}/{den} ({100 * num / den:.1f}%)"


def is_refusal(answer):
    return NOT_FOUND.lower() in answer.lower()


def parse_citations(answer):
    """All (file, page) pairs the answer cites, with file names normalised."""
    found = []
    for m in CITATION_PATTERN.finditer(answer):
        for number in re.findall(r"\d+", m.group(2)):
            found.append((_norm(m.group(1)), int(number)))
    return found


def build_page_index():
    """{normalised file name: set of pages that have stored text}"""
    return {
        _norm(d["File"]): {c["page"] for c in get_document_chunks(d["File"])}
        for d in stored_documents()
    }


def cites_expected(cited, source_norm, pages):
    return any(f == source_norm and p in pages for f, p in cited)


def outcome_ok(q, refused):
    """Unanswerable questions should be refused. Answerable ones should not."""
    return refused if q["type"] == "unanswerable" else not refused


def citation_stats(cited, page_index):
    exist = sum(1 for f, p in cited if p in page_index.get(f, set()))
    return {"citations": len(cited), "citations_exist": exist}


# ---------- one question ----------
def evaluate_question(q, page_index, run_agent_too, pause):
    source_norm = _norm(q["source"]) if q["source"] else None
    expected_pages = set(q["pages"])
    has_target = q["type"] == "answerable" and source_norm and expected_pages
    entry = {"id": q["id"], "question": q["question"], "type": q["type"]}

    # 1. Retrieval: is the expected page among the top-k passages?
    hits = search_chunks(q["question"], k=TOP_K)
    if has_target:
        rank = next(
            (i for i, h in enumerate(hits, start=1)
             if _norm(h["source"]) == source_norm and h["page"] in expected_pages),
            None,
        )
        entry["retrieval"] = {"hit": rank is not None, "rank": rank}
    else:
        entry["retrieval"] = None
    entry["top_score"] = hits[0]["score"] if hits else None

    # 2. Direct RAG answer
    if set(q["tools"]) & SEARCH_TOOLS:
        t0 = time.perf_counter()
        res = answer_question(q["question"])
        seconds = time.perf_counter() - t0
        
        answer = res["answer"]
        refused = is_refusal(answer)
        cited = parse_citations(answer)
        retrieved = {(_norm(h["source"]), h["page"]) for h in hits if h["score"] >= MIN_SCORE}
        entry["rag"] = {
            "answer": answer,
            "seconds": round(seconds, 1),
            "refused": refused,
            "outcome_ok": outcome_ok(q, refused),
            "citations_grounded": sum(1 for c in cited if c in retrieved),
            "expected_page_cited": cites_expected(cited, source_norm, expected_pages) if has_target else None,
            **citation_stats(cited, page_index),
        }
        time.sleep(pause)

    # 3. Agent
    if run_agent_too:
        t0 = time.perf_counter()
        res = run_agent(q["question"])
        seconds = time.perf_counter() - t0
        
        answer = res["answer"]
        refused = is_refusal(answer)
        cited = parse_citations(answer)
        tools = [c["tool"] for c in res["tool_calls"]]
        entry["agent"] = {
            "answer": answer,
            "seconds": round(seconds, 1),
            "tools": tools,
            "tool_ok": any(t in q["tools"] for t in tools),
            "refused": refused,
            "outcome_ok": outcome_ok(q, refused),
            "expected_page_cited": cites_expected(cited, source_norm, expected_pages) if has_target else None,
            **citation_stats(cited, page_index),
        }
        time.sleep(pause)
    return entry


# ---------- results ----------
def summarise(entries, run_agent_too):
    answerable = [e for e in entries if e["type"] == "answerable"]
    unanswerable = [e for e in entries if e["type"] == "unanswerable"]
    rows = []

    scored = [e for e in entries if e.get("retrieval")]
    hits = sum(1 for e in scored if e["retrieval"]["hit"])
    mrr = sum(1 / e["retrieval"]["rank"] for e in scored if e["retrieval"]["rank"]) / len(scored) if scored else None
    rows.append((f"Retrieval hit rate @{TOP_K} (expected page in top results)", ratio(hits, len(scored))))
    rows.append(("Retrieval mean reciprocal rank", "n/a" if mrr is None else f"{mrr:.2f}"))

    def block(mode, label):
        data = [e[mode] for e in entries if mode in e]
        out = []
        ans = [e[mode] for e in answerable if mode in e]
        una = [e[mode] for e in unanswerable if mode in e]
        out.append((f"{label}: answered when answerable", ratio(sum(d["outcome_ok"] for d in ans), len(ans))))
        out.append((f"{label}: refused when unanswerable", ratio(sum(d["outcome_ok"] for d in una), len(una))))
        total = sum(d["citations"] for d in data)
        out.append((f"{label}: citations pointing to a real page", ratio(sum(d["citations_exist"] for d in data), total)))
        if mode == "rag":
            out.append((f"{label}: citations found in the retrieved passages",
                        ratio(sum(d["citations_grounded"] for d in data), total)))
        tgt = [d for d in data if d["expected_page_cited"] is not None]
        out.append((f"{label}: expected page cited", ratio(sum(d["expected_page_cited"] for d in tgt), len(tgt))))
        
        # Response time summary
        times = sorted(d["seconds"] for d in data if "seconds" in d)
        if times:
            out.append((f"{label}: median / slowest response time", f"{times[len(times) // 2]:.1f} s / {times[-1]:.1f} s"))
            
        return out

    rows += block("rag", "Direct RAG")
    if run_agent_too:
        rows += block("agent", "Agent")
        agent = [e["agent"] for e in entries if "agent" in e]
        rows.append(("Agent: acceptable tool chosen", ratio(sum(a["tool_ok"] for a in agent), len(agent))))
    return rows


def failures(entries):
    out = []
    for e in entries:
        for mode in ("rag", "agent"):
            d = e.get(mode)
            if not d:
                continue
            if not d["outcome_ok"]:
                out.append((e["id"], mode, "wrong answer/refusal decision", e["question"]))
            if mode == "agent" and not d["tool_ok"]:
                out.append((e["id"], mode, f"tools used: {d['tools'] or 'none'}", e["question"]))
            if d["expected_page_cited"] is False:
                out.append((e["id"], mode, "expected page not cited", e["question"]))
            if d["citations_exist"] < d["citations"]:
                out.append((e["id"], mode, "cited a page that does not exist", e["question"]))
            if mode == "rag" and d["citations_grounded"] < d["citations"]:
                out.append((e["id"], mode, "cited a page that was not retrieved", e["question"]))
        if e.get("retrieval") and not e["retrieval"]["hit"]:
            out.append((e["id"], "retrieval", "expected page not in top results", e["question"]))
    return out


def write_faithfulness_sheet(entries, page_index_names):
    """A sheet for you to fill in by hand: is every claim supported by the cited text?"""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(SHEET_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "mode", "question", "answer", "cited_passages", "faithful (1 or 0)", "notes"])
        for e in entries:
            for mode in ("rag", "agent"):
                d = e.get(mode)
                if not d or d["refused"]:
                    continue
                passages = []
                for file_key, page in dict.fromkeys(parse_citations(d["answer"])):
                    real = page_index_names.get(file_key)
                    if real:
                        text = " ".join(c["text"] for c in get_document_chunks(real) if c["page"] == page)
                        passages.append(f"[{real}, page {page}] {text[:700]}")
                writer.writerow([e["id"], mode, e["question"], d["answer"], "\n\n".join(passages[:3]), "", ""])


def score_faithfulness():
    if not os.path.exists(SHEET_PATH):
        print("No sheet found. Run the evaluation first.")
        return
    counts = {}
    with open(SHEET_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            mark = (row.get("faithful (1 or 0)") or "").strip()
            if mark in ("0", "1"):
                yes, total = counts.get(row["mode"], (0, 0))
                counts[row["mode"]] = (yes + int(mark), total + 1)
    if not counts:
        print("The sheet has no scores yet. Fill the 'faithful (1 or 0)' column first.")
    for mode, (yes, total) in counts.items():
        print(f"Faithfulness ({mode}): {ratio(yes, total)}")


def write_report(entries, skipped, rows, run_agent_too, started):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    answerable = sum(e["type"] == "answerable" for e in entries)
    lines = [
        "# Evaluation report",
        "",
        f"- Date: {started:%Y-%m-%d %H:%M}",
        f"- Chat model: `{getattr(config, 'CHAT_MODEL', '?')}`, agent model: `{getattr(config, 'AGENT_MODEL', '?')}`, "
        f"embedding model: `{getattr(config, 'EMBEDDING_MODEL', '?')}`",
        f"- Retrieval: top {TOP_K} passages, minimum similarity {MIN_SCORE}, chunk size {CHUNK_SIZE}, overlap {CHUNK_OVERLAP}",
        f"- Questions run: {len(entries)} ({answerable} answerable, {len(entries) - answerable} unanswerable)"
        + (f", skipped: {len(skipped)} (document not stored)" if skipped else ""),
        f"- Agent evaluated: {'yes' if run_agent_too else 'no'}",
        "",
        "| Measure | Result |",
        "|---|---|",
    ]
    lines += [f"| {name} | {value} |" for name, value in rows]
    lines += ["", "Answer faithfulness is judged by hand. See `faithfulness_sheet.csv`.", "", "## Failures", ""]
    fails = failures(entries)
    if fails:
        lines += ["| Question id | Where | What went wrong | Question |", "|---|---|---|---|"]
        lines += [f"| {i} | {mode} | {what} | {q} |" for i, mode, what, q in fails]
    else:
        lines.append("None in this run.")
    with open(os.path.join(RESULTS_DIR, "eval_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(RESULTS_DIR, "eval_results.json"), "w", encoding="utf-8") as f:
        json.dump({"date": started.isoformat(), "entries": entries, "skipped": skipped}, f, indent=1)


# ---------- main ----------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-agent", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--pause", type=float, default=4.0, help="seconds between AI calls (free-tier limit)")
    parser.add_argument("--score-faithfulness", action="store_true")
    args = parser.parse_args()

    if args.score_faithfulness:
        score_faithfulness()
        return

    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        questions = json.load(f)[: args.limit]
    page_index = build_page_index()
    names = {_norm(d["File"]): d["File"] for d in stored_documents()}
    print("Stored documents:", ", ".join(names.values()) or "none")

    started, entries, skipped = datetime.now(), [], []
    for q in questions:
        if q["source"] and _norm(q["source"]) not in page_index:
            print(f"  skip  #{q['id']}: '{q['source']}' is not stored")
            skipped.append(q["id"])
            continue
        try:
            entry = evaluate_question(q, page_index, not args.skip_agent, args.pause)
            entries.append(entry)
            print(f"  done  #{q['id']}: {q['question']}")
        except Exception as e:  # keep going, and record what failed
            print(f"  ERROR #{q['id']}: {e}")
            skipped.append(q["id"])

    rows = summarise(entries, not args.skip_agent)
    write_report(entries, skipped, rows, not args.skip_agent, started)
    write_faithfulness_sheet(entries, names)
    print("\n=== Results ===")
    for name, value in rows:
        print(f"{name}: {value}")
    print(f"\nSaved to {RESULTS_DIR}")


if __name__ == "__main__":
    main()