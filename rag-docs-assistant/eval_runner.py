from generate import answer_question
from eval_set import EVAL_QUESTIONS

def check_Retrieval(expected_source,sources):
    if expected_source is None:
        return None
    return any(expected_source in source for source in sources)

def check_Refusal(answer):
    return "i don't know" in answer.lower()


def run_eval():
    retrieval_total = 0
    generation_correct = 0
    retrieval_correct = 0
    for item in EVAL_QUESTIONS:
        question = item["question"]
        expected_source = item["expected_source"]
        should_answer = item["should_answer"]

        answer,sources = answer_question(question)

        retrieval_pass = check_Retrieval(expected_source,sources)
        refused = check_Refusal(answer)

        if should_answer:
            generation_pass = not refused
        else:
            generation_pass = refused

        print(question)
        print("Sources",sources)
        print("should_answer", should_answer)
        print("-----")

        if retrieval_pass is not None:
            retrieval_total +=1
            if retrieval_pass:
                retrieval_correct +=1

        if generation_pass:
                generation_correct +=1


        print("retrieval_pass:", retrieval_pass)
        print("generation_pass:", generation_pass)


    print("\n--- Summary ---")
    print(f"Retrieval: {retrieval_correct}/{retrieval_total}")
    print(f"Generation: {generation_correct}/{len(EVAL_QUESTIONS)}")    

if __name__ == "__main__":
    run_eval()