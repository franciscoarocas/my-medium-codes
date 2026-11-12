from typing import Callable

from evals.llm import LLMClient


class FakeLLM(LLMClient):
    """
        A mock of an LLM that follows the same interface as ChatGPTClient.
        It lets us test OUR code (prompts, parsing, logic) without calling
        a real model. It says nothing about the quality of a real judge.
    """

    def __init__(self, reply: Callable[[str], str]):
        """
            Params:
                - reply: Function that receives the prompt and returns the fake answer
        """

        self.reply = reply
        self.prompts: list[str] = []

    def ask(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.reply(prompt)
