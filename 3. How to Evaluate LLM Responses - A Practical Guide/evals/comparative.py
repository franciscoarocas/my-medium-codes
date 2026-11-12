from evals.llm import LLMClient


# What the judge answers in each round: which POSITION it prefers
FIRST = "1"
SECOND = "2"
TIE = "tie"

# Final result of the comparison: which MODEL wins (TIE is shared)
MODEL_A = "A"
MODEL_B = "B"


COMPARE_PROMPT = f"""Given the customer's question and two answers, decide which answer is better
for an online store's customer support. Ignore the length and the order of the answers.

Question: {{question}}
Answer {FIRST}: {{first}}
Answer {SECOND}: {{second}}

Reply ONLY with "{FIRST}", "{SECOND}" or "{TIE}"."""


def ask_judge(question: str, first: str, second: str, llm: LLMClient) -> str:
    """
        Ask the judge which of two answers is better.
        Params:
            - question: Question asked by the user
            - first: Answer shown first
            - second: Answer shown second
            - llm: LLM client used as the judge
        Returns:
            FIRST, SECOND or TIE
    """

    prompt = COMPARE_PROMPT.format(question=question, first=first, second=second)
    choice = llm.ask(prompt).strip().strip('"').lower()

    if choice not in (FIRST, SECOND, TIE):
        raise ValueError(f"Unexpected answer from the judge: {choice!r}")

    return choice


def compare(question: str, answer_a: str, answer_b: str, llm: LLMClient) -> str:
    """
        Compare two answers twice, swapping their order, to reduce position bias.
        If the judge changes its mind when the order changes, it is a tie.
        Params:
            - question: Question asked by the user
            - answer_a: Answer from model A
            - answer_b: Answer from model B
            - llm: LLM client used as the judge
        Returns:
            MODEL_A, MODEL_B or TIE
    """

    round_1 = ask_judge(question, first=answer_a, second=answer_b, llm=llm)  # A shown first
    round_2 = ask_judge(question, first=answer_b, second=answer_a, llm=llm)  # B shown first

    if round_1 == FIRST and round_2 == SECOND:
        return MODEL_A
    if round_1 == SECOND and round_2 == FIRST:
        return MODEL_B
    return TIE  # The judge just picked whatever came first (or said tie)


def win_rate(results: list[str], model: str) -> float:
    """
        Percentage of matches won by a model. Ties count as half a win.
        Params:
            - results: Winner of each match (MODEL_A, MODEL_B or TIE)
            - model: MODEL_A or MODEL_B
        Returns:
            Win rate between 0 and 1
    """

    if not results:
        return 0.0

    wins = sum(1 for result in results if result == model)
    ties = sum(1 for result in results if result == TIE)
    return (wins + 0.5 * ties) / len(results)
