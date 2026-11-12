import re
import unicodedata


def normalize(text: str) -> str:
    """
        Normalize a short answer before comparing it:
        lowercase, remove accents, punctuation and extra spaces.
        Params:
            - text: Raw answer
        Returns:
            The normalized answer
    """

    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = re.sub(r"[^\w\s/]", "", text)
    return " ".join(text.split())


def exact_match(answer: str, valid_answers: list[str]) -> bool:
    """
        Check if the answer matches any of the valid answers after normalizing.
        Params:
            - answer: Answer returned by the model
            - valid_answers: List of answers we accept as correct
        Returns:
            True if the answer is one of the valid answers
    """

    normalized_valid = {normalize(valid) for valid in valid_answers}
    return normalize(answer) in normalized_valid
