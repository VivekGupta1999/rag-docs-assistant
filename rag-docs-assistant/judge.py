import json
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from eval_set import EVAL_QUESTIONS

load_dotenv()
client = Anthropic()
JUDGE_MODEL = "claude-sonnet-4-5"
RESULTS_FILE = Path("results/v1_baseline.json")
JUDGED_FILE = Path("results/v1_baseline_judged.json")

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

# print(CORRECTNESS_TOOL["input_schema"]["properties"]["facts"]["items"]["properties"].keys())

def load_results(path: Path) -> list[dict]:
    #read the file , parse the json and return "results list"
    data = json.loads(path.read_text())
    return data["results"]


def judge_correctness(case,answer:str) -> dict:
    prompt = build_correctness_prompt(case,answer)

    message = client.messages.create(
        model= JUDGE_MODEL,
        max_tokens=1500,
        temperature=0,
        tools = [CORRECTNESS_TOOL],
        tool_choice={
            "type":"tool",
            "name":"record_correctness"
        },
        messages=[
            {"role":"user","content":prompt}
        ]
    )

    for block in message.content:
        if block.type =="tool_use":
            return block.input
    raise ValueError(f"Judge returned no tool_use block for {case.id}")

    


def build_correctness_prompt(case, answer:str) ->str:
    #turn case.key_facts into one string, one fact per line each starting with -

    facts = "\n".join(f"- {f}" for f in case.key_facts)

    #fill in the tags
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

    for r in results:
        case = cases[r["id"]]
        if not case.should_answer:
            continue

        # reuse a saved verdict only if the facts and answer haven't changed
        saved = cache.get(case.id)
        if saved and saved["key_facts"] == case.key_facts and saved["answer"] == r["answer"]:
            verdict = saved["verdict"]
        else:
            verdict = judge_correctness(case, r["answer"])

        present = sum(f["present"] for f in verdict["facts"])
        n_facts = len(verdict["facts"])
        passed = present == n_facts

        total += 1
        if passed:
            correct += 1

        status = "PASS" if passed else "FAIL"
        print(f"{case.id}  {case.category:<12}  {status}  {present}/{n_facts} facts")

        records.append({
            "id": case.id,
            "category": case.category,
            "key_facts": case.key_facts,
            "answer": r["answer"],
            "passed": passed,
            "verdict": verdict,
        })

    JUDGED_FILE.write_text(json.dumps(records, indent=2))
    print(f"\nCorrect: {correct}/{total}")
    print(f"Saved {JUDGED_FILE}")
if __name__ == "__main__":
    main()