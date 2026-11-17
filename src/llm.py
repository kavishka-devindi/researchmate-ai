import time

from google import genai
from google.genai import types, errors

from src.config import GEMINI_API_KEY, CHAT_MODEL, FALLBACK_MODEL, TEMPERATURE

client = genai.Client(api_key=GEMINI_API_KEY)


class LLMError(Exception):
    """Raised with a user-friendly message when the LLM call fails."""


def generate_answer(prompt, system_instruction="You are a helpful assistant."):
    """Send a prompt to Gemini and return the answer as text.

    Tries the main model first, then the fallback model.
    Raises LLMError with a readable message if everything fails.
    """
    last_code = None

    for model in [CHAT_MODEL, FALLBACK_MODEL]:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=TEMPERATURE,
                        system_instruction=system_instruction,
                    ),
                )
            except errors.APIError as e:
                last_code = e.code
                if e.code in (400, 401, 403):
                    raise LLMError(
                        "The request was rejected. Check your API key and your input."
                    ) from e
                if e.code in (500, 503, 504) and attempt == 0:
                    time.sleep(2)  # wait, then retry the same model once
                    continue
                break  # move on to the fallback model
            except Exception as e:
                raise LLMError(
                    "Could not reach the Gemini service. Check your internet connection."
                ) from e
            else:
                if not response.text:
                    raise LLMError("The model returned an empty answer. Try rephrasing.")
                return response.text

    if last_code == 429:
        raise LLMError("Rate limit reached on both models. Please wait a minute and try again.")
    raise LLMError("The AI service is temporarily unavailable. Please try again shortly.")