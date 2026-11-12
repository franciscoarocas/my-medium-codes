import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv


load_dotenv()

DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))


class LLMClient(ABC):
    """
        Common interface for any LLM used as a judge.
        The judge and the comparative evaluation only depend on this class,
        so switching provider means writing a new subclass, nothing else.
        It also lets us use a fake LLM in the tests (a mock).
    """

    @abstractmethod
    def ask(self, prompt: str) -> str:
        """
            Send a prompt to the model and return its text answer.
            Params:
                - prompt: Full prompt to send to the model
            Returns:
                The text returned by the model
        """


class ChatGPTClient(LLMClient):
    """
        LLMClient implementation for OpenAI's ChatGPT models.
        Configuration is read from the .env file:
            - OPENAI_API_KEY: your OpenAI API key (required)
            - LLM_MODEL: model to use (default: gpt-4o-mini)
            - LLM_TEMPERATURE: sampling temperature (default: 0)
    """

    def __init__(self, model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
        """
            Params:
                - model: Name of the OpenAI model
                - temperature: Sampling temperature. 0 makes the judge more consistent
        """

        from openai import OpenAI

        self.client = OpenAI()  # Reads OPENAI_API_KEY from the environment
        self.model = model
        self.temperature = temperature

    def ask(self, prompt: str) -> str:
        """
            Send a prompt to ChatGPT and return its text answer.
            Params:
                - prompt: Full prompt to send to the model
            Returns:
                The text returned by the model
        """

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
