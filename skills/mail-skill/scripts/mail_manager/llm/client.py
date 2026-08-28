"""LLM client abstraction for all AI-powered features.

Provides a thin wrapper around OpenAI SDK for external API access,
with graceful fallback to Agent mode when no API key is configured.

In Agent mode (default): AI features output structured data for
the Agent (Claude) to process using its own reasoning.
In External mode: AI features call configured LLM APIs directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from mail_manager.errors import MailSkillError


class AIConfigError(Exception):
    """Raised when AI features are not configured."""

    pass


def is_ai_enabled() -> bool:
    """Check if AI features are enabled.

    AI features are always enabled — the Agent (Claude) provides
    LLM capabilities by default. External API keys are optional.

    Returns:
        Always True.
    """
    return True


def is_external_llm_configured() -> bool:
    """Check if an external LLM API key is configured.

    When configured, LLM-dependent features call the external API
    directly for faster, automated results. When not configured,
    features output structured data for the Agent to process.

    Returns:
        True if LLM_API_KEY is set in environment/config.
    """
    return bool(os.getenv("LLM_API_KEY"))


@dataclass
class LLMResponse:
    """Standard LLM response structure."""

    content: str
    model: str
    usage: dict[str, int]
    finish_reason: str


class LLMClient:
    """LLM client supporting both Agent mode and external API mode.

    In Agent mode (no LLM_API_KEY): the client is a no-op placeholder.
    Callers should check is_external_llm_configured() before calling
    chat/chat_with_history and fall back to Agent-oriented output.

    In External mode (LLM_API_KEY configured): wraps OpenAI SDK for
    direct API calls.
    """

    def __init__(self) -> None:
        """Initialize LLM client.

        Without LLM_API_KEY: operates in Agent mode (no external API).
        With LLM_API_KEY: wraps OpenAI SDK for direct API access.
        """
        api_key = os.getenv("LLM_API_KEY")
        self._agent_mode = not bool(api_key)

        if self._agent_mode:
            self.client = None
            self.model = "agent"
        else:
            from openai import OpenAI

            api_base = os.getenv("LLM_API_BASE")
            try:
                timeout = int(os.getenv("LLM_TIMEOUT", "30"))
            except (ValueError, TypeError):
                timeout = 30

            self.client = OpenAI(api_key=api_key, base_url=api_base, timeout=timeout)
            self.model = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")

    @property
    def is_agent_mode(self) -> bool:
        """Whether this client is in Agent mode (no external API)."""
        return self._agent_mode

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Send chat completion request.

        In Agent mode: returns empty response (caller should use
        Agent-oriented fallback).

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens in response.

        Returns:
            LLMResponse with content, model, usage, and finish_reason.

        Raises:
            MailSkillError: If API call fails.
        """
        if self._agent_mode:
            return LLMResponse(
                content="",
                model="agent",
                usage={},
                finish_reason="agent_mode",
            )

        from openai import APIError, RateLimitError

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if not response.choices:
                raise MailSkillError("LLM returned empty response choices")

            choice = response.choices[0]
            usage = response.usage
            return LLMResponse(
                content=choice.message.content or "",
                model=response.model or self.model,
                usage={
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "total_tokens": usage.total_tokens if usage else 0,
                },
                finish_reason=choice.finish_reason or "unknown",
            )
        except (APIError, RateLimitError) as e:
            raise MailSkillError(f"LLM API error: {e}") from e
        except (IndexError, AttributeError, KeyError) as e:
            raise MailSkillError(f"Unexpected LLM response format: {e}") from e

    def chat_with_history(
        self,
        system_prompt: str,
        conversation: list[dict[str, str]],
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Chat with conversation history context.

        Args:
            system_prompt: System prompt to set behavior.
            conversation: List of prior messages with 'role' and 'content'.
            user_message: Current user message.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens in response.

        Returns:
            LLMResponse with content, model, usage, and finish_reason.
        """
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation)
        messages.append({"role": "user", "content": user_message})
        return self.chat(messages, temperature=temperature, max_tokens=max_tokens)
