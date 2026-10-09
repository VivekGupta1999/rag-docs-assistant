import json
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from generate import get_context
from eval_set import EVAL_QUESTIONS

load_dotenv()
client = Anthropic()
JUDGE_MODEL = "claude-sonnet-4-5"
RESULTS_FILE = Path("results/v2_20261009_2247.json")
JUDGED_FILE = Path("results/v2_judged.json")


FAITHFULNESS_TOOL = {
    "name": "record_faithfulness",
    "description": "Record whether every claim in the answer is supported by the context",
    "input_schema": {
        "type": "object",
        "properties": {
            "critique": {
                "type": "string",
                "description": "Go through the answer's claims one by one and check each against the context",
            },
            "unsupported_claims": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Claims not supported by the context. Empty list if none",
            },
            "faithful": {
                "type": "boolean",
                "description": "True only if unsupported_claims is empty.",
            },
        },
        "required": ["critique", "unsupported_claims", "faithful"],
    },
}

CORRECTNESS_TOOL = {
    "name": "record_correctness",
    "description": "Record whether the answer contains each required key fact.",
    "input_schema": {
        "type": "object",
        "properties": {
            "critique": {
                "type": "string",
                "description": "Check the answer against each key fact, one by one, before deciding.",
            },
            "facts": {                          # a list...
                "type": "array",
                "items": {                      # ...where each element is:
                    "type": "object",
                    "properties": {
                        "fact": {"type": "string"},
                        "present": {"type": "boolean"},
                    },
                    "required": ["fact", "present"],
                },
            },
        },
        "required": ["critique", "facts"],
    },
}


def load_results(path: Path) -> list[dict]:
    # read the file, parse the json and return the "results" list
    data = json.loads(path.read_text())
    return data["results"]


def judge_correctness(case, answer: str) -> dict:
    prompt = build_correctness_prompt(case, answer)

    message = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=1500,
        temperature=0,
        tools=[CORRECTNESS_TOOL],
        tool_choice={"type": "tool", "name": "record_correctness"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in message.content:
        if block.type == "tool_use":
            return block.input
    raise ValueError(f"Judge returned no tool_use block for {case.id}")


def judge_faithfulness(question, context, answer):
    prompt = build_faithfulness_prompt(question, context, answer)

    message = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=1500,
        temperature=0,
        tools=[FAITHFULNESS_TOOL],
        tool_choice={"type": "tool", "name": "record_faithfulness"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in message.content:
        if block.type == "tool_use":
            return block.input
    raise ValueError(f"Judge returned no tool_use block for: {question}")


def build_faithfulness_prompt(question, context, answer):
    return f"""You are checking whether an answer from a FastAPI documentation assistant
is grounded in the documentation chunks it was given.

<question>{question}</question>

<context>
{context}
</context>

<answer>
{answer}
</answer>

Rules:
- Check each technical claim in the answer (APIs, parameters, behaviour, code) against the context.
- A claim is supported if the context states it, or it follows directly from the context.
  Paraphrasing and summarising are fine.
- A claim is unsupported if it is not in the context, even if it is true in real life.
  Use only the context, not your own knowledge of FastAPI.
- Code that uses functions or parameters not shown or described in the context is unsupported.
- Ignore greetings, headings, source citations and generic framing sentences.
- If the answer says it doesn't know, it is faithful (it claims nothing).
List every unsupported claim. The answer is faithful only if that list is empty."""


def build_correctness_prompt(case, answer: str) -> str:
    # turn case.key_facts into one string, one fact per line, each starting with -
    facts = "\n".join(f"- {f}" for f in case.key_facts)

    return f"""You are grading an answer from a FastAPI documentation assistant.

<question>
{case.question}
</question>

<key_facts>
{facts}
</key_facts>

<answer>
{answer}
</answer>

For each key fact, decide whether the answer states it or clearly shows it (for example in a code sample).
A fact counts as present if the answer conveys the same meaning, even without the exact words
(for example, "a Pydantic model class" means a class inheriting from BaseModel).
Do not mark a fact present just because related words appear; the meaning must be there.
A fact that is only vaguely hinted at does NOT count.
Judge only what is written in the answer. Do not fill gaps with your own knowledge of FastAPI."""


def main():
    results = load_results(RESULTS_FILE)
    cases = {c.id: c for c in EVAL_QUESTIONS}

    # load saved verdicts, if any, so re-runs don't pay twice
    cache = {}
    if JUDGED_FILE.exists():
        cache = {rec["id"]: rec for rec in json.loads(JUDGED_FILE.read_text())}

    records = []
    total = 0
    correct = 0
    faithful_count = 0

    for r in results:
        case = cases[r["id"]]
        if not case.should_answer:
            continue

        saved = cache.get(case.id)

        # ---------- correctness ----------
        # reuse a saved verdict only if the facts and answer haven't changed
        if saved and saved["key_facts"] == case.key_facts and saved["answer"] == r["answer"]:
            verdict = saved["verdict"]
        else:
            verdict = judge_correctness(case, r["answer"])

        present = sum(f["present"] for f in verdict["facts"])
        n_facts = len(verdict["facts"])
        passed = present == n_facts

        # ---------- faithfulness ----------
        context, _ = get_context(case.question)  # same chunks the bot saw
        if saved and saved.get("context") == context and saved["answer"] == r["answer"]:
            faith = saved["faith"]
        else:
            faith = judge_faithfulness(case.question, context, r["answer"])

        claims = faith["unsupported_claims"]
        if isinstance(claims, str):                # judge sometimes returns the list as a JSON string
            try:
                claims = json.loads(claims)
            except json.JSONDecodeError:
                claims = [claims]
            faith["unsupported_claims"] = claims

        is_faithful = faith["faithful"] and not faith["unsupported_claims"]



        # ---------- counters + output ----------
        total += 1
        if passed:
            correct += 1
        if is_faithful:
            faithful_count += 1

        status = "PASS" if passed else "FAIL"
        grounded = "faithful" if is_faithful else "UNFAITHFUL"
        print(f"{case.id}  {case.category:<12}  {status}  {present}/{n_facts} facts  {grounded}")
        for claim in faith["unsupported_claims"][:2]:
            print(f"      unsupported: {claim[:110]}")

        records.append({
            "id": case.id,
            "category": case.category,
            "key_facts": case.key_facts,
            "answer": r["answer"],
            "passed": passed,
            "verdict": verdict,
            "context": context,
            "faith": faith,
        })

    JUDGED_FILE.write_text(json.dumps(records, indent=2))
    print(f"\nCorrect:  {correct}/{total}")
    print(f"Faithful: {faithful_count}/{total}")
    print(f"Saved {JUDGED_FILE}")


if __name__ == "__main__":
    main()