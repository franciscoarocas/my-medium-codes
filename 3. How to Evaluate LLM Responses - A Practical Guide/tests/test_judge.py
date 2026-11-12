import pytest

from evals.judge import judge
from tests.fakes import FakeLLM


QUESTION = "Can I return some sneakers I bought 2 months ago?"
ANSWER = "Of course! You can return them whenever you want."


def test_judge_parses_the_verdict():
    llm = FakeLLM(lambda prompt: 'Sure! {"score": 1, "reason": "It contradicts the 30-day return policy."}')

    verdict = judge(QUESTION, ANSWER, llm=llm)

    assert verdict == {"score": 1, "reason": "It contradicts the 30-day return policy."}


def test_judge_prompt_contains_criteria_question_and_answer():
    llm = FakeLLM(lambda prompt: '{"score": 1, "reason": "x"}')

    judge(QUESTION, ANSWER, llm=llm)

    prompt = llm.prompts[0]
    assert "30 days" in prompt and QUESTION in prompt and ANSWER in prompt


def test_judge_fails_if_no_json_is_returned():
    llm = FakeLLM(lambda prompt: "I think it is a bad answer")

    with pytest.raises(ValueError):
        judge(QUESTION, ANSWER, llm=llm)
