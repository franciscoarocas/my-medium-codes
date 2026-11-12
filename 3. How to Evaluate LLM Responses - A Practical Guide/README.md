# How to Evaluate LLM Responses: A Practical Guide

Companion code for the Medium article **"How to Evaluate LLM Responses: A Practical Guide"**.

A traditional function can be tested with a simple `assert add(2, 2) == 4`. LLM answers are open-ended, so that kind of test is no longer enough. This project implements, in small and readable Python files, every evaluation method discussed in the article, using the same examples: an online store's customer-support chatbot.

## Methods

| File | Method | Needs an API key? |
|---|---|---|
| `evals/functional.py` | **Functional correctness**: run generated code against known test cases, plus `pass@k` | No |
| `evals/exact_match.py` | **Exact match**: normalize short answers and compare with a list of valid ones | No |
| `evals/lexical.py` | **Lexical similarity**: ROUGE-1, counting shared words | No |
| `evals/semantic.py` | **Semantic similarity**: embeddings + cosine similarity | No (downloads a small model the first time) |
| `evals/judge.py` | **LLM as a judge**: a second model scores the answer from 1 to 5 and explains why | Yes (OpenAI) |
| `evals/comparative.py` | **Comparative evaluation**: A vs B, asking twice with the order swapped to reduce position bias | Yes (OpenAI) |
| `evals/llm.py` | `LLMClient` (abstract interface) and `ChatGPTClient` (OpenAI implementation) | Yes (OpenAI) |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # then add your API key
```

Fill in `.env`:

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key | — (required for the judge) |
| `LLM_MODEL` | Model used as the judge | `gpt-4o-mini` |
| `LLM_TEMPERATURE` | Sampling temperature. `0` gives more consistent scores | `0` |

## Using another LLM provider

The judge and the comparative evaluation only depend on the abstract class `LLMClient`:

```python
class LLMClient(ABC):
    @abstractmethod
    def ask(self, prompt: str) -> str: ...
```

`ChatGPTClient` is the implementation for OpenAI. To use another provider, create a new subclass that implements `ask()` and pass it to `judge()` or `compare()`:

```python
from evals.judge import judge
from evals.llm import ChatGPTClient

verdict = judge(
    "Can I return some sneakers I bought 2 months ago?",
    "Of course! You can return them whenever you want.",
    llm=ChatGPTClient(),
)
# {"score": 1, "reason": "It contradicts the 30-day return policy."}
```

## Run the examples

```bash
# Methods that run locally
python -m examples.run_all

# Also LLM as a judge and comparative evaluation
python -m examples.run_all --llm
```

Expected output for the local methods:

```text
1. Functional correctness
   Generated id_letter() passes the tests: True

2. Exact match
   'santa cruz'         -> True
   'S/C de Tenerife'    -> True
   'La Laguna'          -> False

3. Lexical similarity (ROUGE-1)
   Same meaning:     0.46
   Opposite meaning: 0.92

4. Semantic similarity (embeddings)
   Same meaning:     0.80
   Opposite meaning: 0.90
```

The lexical similarity result is the problem shown in the article: the answer that means the **opposite** gets the **higher** score, because it shares more words with the reference.

Semantic similarity (with `all-MiniLM-L6-v2`) gives a high score to the correct answer, but the negated sentence scores even higher: embeddings capture the topic very well, but often miss a negation.

## Run the tests

```bash
pytest
```

The tests for the judge and the comparative evaluation use `FakeLLM` (`tests/fakes.py`), a **mock** that implements the same `LLMClient` interface as `ChatGPTClient`. Just like the article explains, a mock lets us test *our* code (prompts, parsing, logic) without calling a real model, but it says nothing about the quality of the model's answers.

One of the tests uses a fake judge that always picks the first answer, to show how asking twice with the order swapped detects position bias.

## Notes

- `evals/functional.py` runs generated code with `exec` to keep the example short. In a real system, run untrusted code inside a sandbox.
- A judge is the **model + the prompt**. If you change either one, the scores are no longer comparable with previous ones.
