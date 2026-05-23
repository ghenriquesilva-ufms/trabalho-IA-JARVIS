import logging
import time
from typing import List, Optional, Dict, Any

from openai import OpenAI


logger = logging.getLogger(__name__)

_DEFAULT_SYSTEM_PROMPT = (
    "Voce e o JARVIS, um assistente academico que ajuda estudantes a organizar estudos. "
    "Forneca respostas claras, organizadas e com foco em planejamento e aprendizagem."
)


_client = OpenAI(
    base_url="https://llm.liaufms.org/v1/gemma-3-12b-it",
    api_key="Cxt2ftLF7d3mHS2JdiFqB-eSDAQeZvFATPXPs02lV9A",
)


def _ensure_system_prompt(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not messages or messages[0].get("role") != "system":
        return [{"role": "system", "content": _DEFAULT_SYSTEM_PROMPT}] + messages
    return messages


def send_message(messages: list, tools: list = None) -> dict:
    """Send a chat request and return the first response message object."""
    prepared_messages = _ensure_system_prompt(messages)
    request_kwargs: Dict[str, Any] = {
        "model": "google/gemma-3-12b-it",
        "messages": prepared_messages,
    }
    if tools is not None:
        request_kwargs["tools"] = tools
        request_kwargs["tool_choice"] = "auto"
        request_kwargs["extra_headers"] = {
            "x-enable-auto-tool-choice": "true",
            "x-tool-call-parser": "json",
        }
        request_kwargs["extra_body"] = {
            "enable_auto_tool_choice": True,
            "tool_call_parser": "json",
        }

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = _client.chat.completions.create(**request_kwargs)
            return response.choices[0].message
        except Exception as exc:
            last_error = exc
            message = str(exc)
            if "503" in message or "not accepting requests" in message:
                time.sleep(1.5 * (attempt + 1))
                continue
            logger.exception("Failed to send message to LLM")
            raise

    logger.exception("Failed to send message to LLM after retries")
    raise last_error
