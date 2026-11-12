from evals.functional import GENERATED_CODE, functional_correctness, pass_at_k


WRONG_CODE = '''
def id_letter(number):
    return "A"
'''

BROKEN_CODE = "def id_letter(number) return 'A'"


def test_generated_code_passes():
    assert functional_correctness(GENERATED_CODE)


def test_wrong_code_fails():
    assert not functional_correctness(WRONG_CODE)


def test_broken_code_fails_instead_of_crashing():
    assert not functional_correctness(BROKEN_CODE)


def test_pass_at_k_needs_only_one_correct_sample():
    assert pass_at_k([WRONG_CODE, BROKEN_CODE, GENERATED_CODE])
    assert not pass_at_k([WRONG_CODE, BROKEN_CODE])
