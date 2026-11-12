def rouge_1(reference: str, answer: str) -> float:
    """
        Lexical similarity with a simplified ROUGE-1 (F1): how many unique words
        both texts share. The full metric also takes repeated words into account.
        It measures if two texts LOOK alike, not if they MEAN the same.
        Params:
            - reference: Reference answer we know is correct
            - answer: Answer returned by the model
        Returns:
            F1 score between 0 and 1
    """

    reference_words = set(reference.lower().split())
    answer_words = set(answer.lower().split())

    shared = len(reference_words & answer_words)
    if shared == 0:
        return 0.0

    precision = shared / len(answer_words)
    recall = shared / len(reference_words)
    return 2 * precision * recall / (precision + recall)
