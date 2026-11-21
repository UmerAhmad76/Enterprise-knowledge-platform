"""Prompt registry: version ka naam se prompt lene ki jagah. Naya version aaye to yahan register hota hai."""
from core.llm.prompts import answer_v1

PROMPTS = {
    answer_v1.PROMPT_VERSION: answer_v1,
}

DEFAULT_PROMPT_VERSION = answer_v1.PROMPT_VERSION