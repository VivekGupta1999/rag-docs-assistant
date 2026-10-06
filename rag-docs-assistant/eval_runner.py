import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from generate import answer_question
from eval_set import EVAL_QUESTIONS, EvalCase




def check_retrieval(case: EvalCase, sources: list[str]) -> bool | None:
    """True if expected sources were retrieved.
    multi_doc needs ALL of them; other categories need at least one.
    None when the case has no expected sources (out_of_scope / near_miss)."""
    if not case.expected_sources:
        return None
    found = [any(exp in src for src in sources) for exp in case.expected_sources]
    return all(found) if case.category == "multi_doc" else any(found)


def check_refusal(answer: str) -> bool:
    # Temporary: replaced by the LLM judge tomorrow.
    return "i don't know" in answer.lower()


def run_eval(tag: str = "v1") -> dict:
    results = []
    for case in EVAL_QUESTIONS:
        answer, sources = answer_question(case.question)

        retrieval_pass = check_retrieval(case, sources)
        refused = check_refusal(answer)
        behaviour_pass = (not refused) if case.should_answer else refused

        results.append({
            "id": case.id,
            "category": case.category,
            "question": case.question,
            "sources": sources,
            "answer": answer,
            "retrieval_pass": retrieval_pass,
            "behaviour_pass": behaviour_pass,
        })

        mark = "PASS" if behaviour_pass else "FAIL"
        print(f"[{mark}] {case.id} ({case.category}) retrieval={retrieval_pass}  {case.question}")

    summary = summarize(results)
    print_summary(summary)

    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{tag}_{datetime.now():%Y%m%d_%H%M}.json"
    out_file.write_text(json.dumps({"summary": summary, "results": results}, indent=2))
    print(f"\nSaved {out_file}")
    return summary


def summarize(results: list[dict]) -> dict:
    by_cat = defaultdict(lambda: {"n": 0, "behaviour": 0, "retrieval": 0, "retrieval_n": 0})
    for r in results:
        c = by_cat[r["category"]]
        c["n"] += 1
        c["behaviour"] += r["behaviour_pass"]
        if r["retrieval_pass"] is not None:
            c["retrieval_n"] += 1
            c["retrieval"] += r["retrieval_pass"]

    retrieval_n = sum(c["retrieval_n"] for c in by_cat.values())
    return {
        "total": len(results),
        "behaviour": sum(c["behaviour"] for c in by_cat.values()),
        "retrieval": sum(c["retrieval"] for c in by_cat.values()),
        "retrieval_n": retrieval_n,
        "by_category": dict(by_cat),
    }


def print_summary(s: dict) -> None:
    print("\n--- Summary ---")
    print(f"Retrieval: {s['retrieval']}/{s['retrieval_n']}")
    print(f"Behaviour (answer vs refuse): {s['behaviour']}/{s['total']}")
    print("\nBy category:")
    for cat, c in s["by_category"].items():
        ret = f"{c['retrieval']}/{c['retrieval_n']}" if c["retrieval_n"] else "-"
        print(f"  {cat:<13} behaviour {c['behaviour']}/{c['n']}   retrieval {ret}")


if __name__ == "__main__":
    run_eval()