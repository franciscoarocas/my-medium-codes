"""
    Run every evaluation method from the article on the online store examples.
    Usage (from the project folder):
        python -m examples.run_all            -> methods that run locally
        python -m examples.run_all --llm      -> also LLM as a judge and A/B (needs OPENAI_API_KEY in .env)
"""

import sys

from evals.exact_match import exact_match
from evals.functional import GENERATED_CODE, functional_correctness
from evals.lexical import rouge_1


REFERENCE = "The order will arrive on Tuesday"
CORRECT = "Your package will be delivered on Tuesday"
OPPOSITE = "The order will not arrive on Tuesday"


def main():
    print("1. Functional correctness")
    print("   Generated id_letter() passes the tests:", functional_correctness(GENERATED_CODE))

    print("\n2. Exact match")
    valid = ["Santa Cruz de Tenerife", "Santa Cruz", "S/C de Tenerife"]
    for answer in ["santa cruz", "S/C de Tenerife", "La Laguna"]:
        print(f"   {answer!r:<20} ->", exact_match(answer, valid))

    print("\n3. Lexical similarity (ROUGE-1)")
    print(f"   Same meaning:     {rouge_1(REFERENCE, CORRECT):.2f}")
    print(f"   Opposite meaning: {rouge_1(REFERENCE, OPPOSITE):.2f}")

    print("\n4. Semantic similarity (embeddings)")
    from evals.semantic import semantic_similarity
    print(f"   Same meaning:     {semantic_similarity(REFERENCE, CORRECT):.2f}")
    print(f"   Opposite meaning: {semantic_similarity(REFERENCE, OPPOSITE):.2f}")

    if "--llm" not in sys.argv:
        print("\nRun with --llm to try LLM as a judge and comparative evaluation.")
        return

    from evals.comparative import compare
    from evals.judge import judge
    from evals.llm import ChatGPTClient

    llm = ChatGPTClient()  # Model and API key are read from .env

    print("\n5. LLM as a judge")
    print("  ", judge(
        "Can I return some sneakers I bought 2 months ago?",
        "Of course! You can return them whenever you want.",
        llm=llm,
    ))

    print("\n6. Comparative evaluation (order swapped to reduce position bias)")
    print("   Winner:", compare(
        "How do I return an item I bought online?",
        "You can return items within 30 days. Please contact customer service.",
        "Go to My orders, choose the item and click Return. You have 30 days.",
        llm=llm,
    ))


if __name__ == "__main__":
    main()
