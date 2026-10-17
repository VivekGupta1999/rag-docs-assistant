from eval_set import EVAL_QUESTIONS
from hybrid import vector_search, hybrid_search, ID_TO_INDEX, SOURCES


def is_hit(case, sources):
    found = [any(exp in src for src in sources) for exp in case.expected_sources]
    return all(found) if case.category == "multi_doc" else any(found)

def first_rank(case, sources):
    for rank, src in enumerate(sources, start=1):
        if any(exp in src for exp in case.expected_sources):
            return rank
    return None

def vector_sources(question, n=5):
    return [SOURCES[ID_TO_INDEX[i]] for i in vector_search(question, n=n)]


def hybrid_sources(question, n=5):
    return [source for _, source in hybrid_search(question, n=n)]


def main():
    cases = [c for c in EVAL_QUESTIONS if c.should_answer]
    vec_hits = hyb_hits = 0
    vec_rr = hyb_rr = 0.0

    print(f"{'id':<5} {'category':<12} {'vector':<10} {'hybrid':<10}")
    for case in cases:
        vs = vector_sources(case.question)
        hs = hybrid_sources(case.question)
        v, h = is_hit(case, vs), is_hit(case, hs)
        vr, hr = first_rank(case, vs), first_rank(case, hs)
        vec_hits += v
        hyb_hits += h
        vec_rr += 1 / vr if vr else 0
        hyb_rr += 1 / hr if hr else 0
        v_txt = f"hit@{vr}" if v else "MISS"
        h_txt = f"hit@{hr}" if h else "MISS"
        flag = ""
        if v != h:
            flag = "  <-- hybrid fixed" if h else "  <-- hybrid BROKE"
        elif vr and hr and vr != hr:
            flag = "  (hybrid higher)" if hr < vr else "  (hybrid lower)"
        print(f"{case.id:<5} {case.category:<12} {v_txt:<10} {h_txt:<10}{flag}")

    total = len(cases)
    print(f"\nVector hit@5: {vec_hits}/{total}   MRR: {vec_rr / total:.3f}")
    print(f"Hybrid hit@5: {hyb_hits}/{total}   MRR: {hyb_rr / total:.3f}")

    miss = next(c for c in cases if c.id == "q26")
    print(f"\nq26: {miss.question}")
    print(f"expected: {miss.expected_sources}")
    print("vector:", [s.split('/docs/')[-1] for s in vector_sources(miss.question)])
    print("hybrid:", [s.split('/docs/')[-1] for s in hybrid_sources(miss.question)])  
    print(f"Hybrid hit@5: {hyb_hits}/{total} ({hyb_hits / total:.0%})")


if __name__ == "__main__":
    main()