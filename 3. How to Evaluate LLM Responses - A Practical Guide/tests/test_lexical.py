from evals.lexical import rouge_1


REFERENCE = "The order will arrive on Tuesday"


def test_lexical_similarity_rewards_the_wrong_answer():
    correct = rouge_1(REFERENCE, "Your package will be delivered on Tuesday")
    opposite = rouge_1(REFERENCE, "The order will not arrive on Tuesday")

    assert round(correct, 2) == 0.46
    assert round(opposite, 2) == 0.92
    assert opposite > correct  # the problem shown in the article
