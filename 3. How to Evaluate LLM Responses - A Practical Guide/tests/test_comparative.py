from evals.comparative import FIRST, MODEL_B, SECOND, TIE, compare, win_rate, MODEL_A
from tests.fakes import FakeLLM


QUESTION = "How do I return an item I bought online?"
GOOD = "Go to My orders, choose the item and click Return."
VAGUE = "Contact customer service."


def prefers_good_answer(prompt: str) -> str:
    # A consistent judge: always picks the good answer, wherever it appears
    first_answer = prompt.split(f"Answer {FIRST}:")[1].split(f"Answer {SECOND}:")[0]
    return FIRST if GOOD in first_answer else SECOND


def always_first(prompt: str) -> str:
    # A judge with position bias: always picks whatever it reads first
    return FIRST


def test_consistent_judge_picks_the_good_answer():
    assert compare(QUESTION, VAGUE, GOOD, llm=FakeLLM(prefers_good_answer)) == MODEL_B


def test_position_bias_is_detected_as_a_tie():
    assert compare(QUESTION, VAGUE, GOOD, llm=FakeLLM(always_first)) == TIE


def test_judge_is_asked_twice_with_the_order_swapped():
    llm = FakeLLM(prefers_good_answer)

    compare(QUESTION, VAGUE, GOOD, llm=llm)

    assert len(llm.prompts) == 2
    assert llm.prompts[0].index(VAGUE) < llm.prompts[0].index(GOOD)
    assert llm.prompts[1].index(GOOD) < llm.prompts[1].index(VAGUE)


def test_win_rate_counts_ties_as_half():
    assert win_rate([MODEL_A, MODEL_B, TIE, MODEL_B], MODEL_B) == 0.625
