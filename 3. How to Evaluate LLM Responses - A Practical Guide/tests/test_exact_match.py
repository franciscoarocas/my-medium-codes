from evals.exact_match import exact_match


VALID = ["Santa Cruz de Tenerife", "Santa Cruz", "S/C de Tenerife"]


def test_all_valid_variants_match():
    for answer in ["Santa Cruz de Tenerife", "santa cruz", "S/C de Tenerife."]:
        assert exact_match(answer, VALID)


def test_wrong_answer_does_not_match():
    assert not exact_match("La Laguna", VALID)
