"""Provider-agnostic LLM client abstraction for Chrysalis AI.

Supports Google AI Studio Gemini API via direct HTTP REST calls and an offline
MockLLMClient for zero-cost, deterministic unit testing.
"""

from __future__ import annotations
import abc
import json
import logging
import re
from typing import Any, Type, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from backend.app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ==============================================================================
# Custom Exceptions
# ==============================================================================

class LLMError(Exception):
    """Base exception for all LLM client operations."""
    pass


class LLMAuthenticationError(LLMError):
    """Raised when the API key is missing, invalid, or unauthorized."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when the provider rate limit or quota is exceeded."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when the LLM call times out."""
    pass


class LLMMalformedJSONError(LLMError):
    """Raised when the LLM response cannot be parsed as valid JSON."""
    def __init__(self, message: str, raw_content: str):
        super().__init__(message)
        self.raw_content = raw_content


class LLMValidationError(LLMError):
    """Raised when parsed JSON does not conform to the expected Pydantic schema."""
    def __init__(self, message: str, raw_content: str, validation_errors: Any):
        super().__init__(message)
        self.raw_content = raw_content
        self.validation_errors = validation_errors


class LLMProviderError(LLMError):
    """Raised on internal provider errors (e.g. HTTP 500, 503)."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


# ==============================================================================
# Helpers
# ==============================================================================

def clean_json_markdown(text: str) -> str:
    """Strip markdown code fence blocks if returned by the LLM."""
    trimmed = text.strip()
    # Match ```json ... ``` or ``` ... ```
    pattern = r"^```(?:json)?\s*([\s\S]*?)\s*```$"
    match = re.match(pattern, trimmed, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return trimmed


# ==============================================================================
# Abstract LLM Client
# ==============================================================================

class LLMClient(abc.ABC):
    """Abstract interface for LLM client implementations."""

    @abc.abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate unstructured text from a prompt."""
        raise NotImplementedError

    @abc.abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: str | None = None,
        temperature: float | None = None,
    ) -> T:
        """Generate structured output validated against a Pydantic schema."""
        raise NotImplementedError

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Verify provider connectivity and credentials."""
        raise NotImplementedError


# ==============================================================================
# Google Gemini REST Client
# ==============================================================================

class GeminiClient(LLMClient):
    """Google Gemini client using Google AI Studio REST API.
    
    Target endpoint:
    https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._api_key = self.settings.gemini_api_key.get_secret_value()
        self.model = self.settings.gemini_model
        self.timeout = self.settings.llm_timeout_seconds
        self.default_temperature = self.settings.llm_temperature

    def _get_url(self) -> str:
        if not self._api_key:
            raise LLMAuthenticationError(
                "GEMINI_API_KEY is not configured. Set GEMINI_API_KEY in your environment or .env file."
            )
        return f"{self.BASE_URL}/{self.model}:generateContent"

    def _build_payload(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None,
        force_json: bool = False,
    ) -> dict[str, Any]:
        temp = temperature if temperature is not None else self.default_temperature

        contents = [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ]

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temp,
            },
        }

        if force_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        if system_instruction:
            payload["systemInstruction"] = {
                "role": "system",
                "parts": [{"text": system_instruction}],
            }

        return payload

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None,
    ) -> str:
        url = self._get_url()
        payload = self._build_payload(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            force_json=False,
        )

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(f"Gemini API timed out after {self.timeout}s: {exc}") from exc
            except httpx.RequestError as exc:
                raise LLMError(f"Network error calling Gemini API: {exc}") from exc

        if response.status_code == 401 or response.status_code == 403:
            raise LLMAuthenticationError(
                f"Authentication failed with Gemini API (Status {response.status_code}). Verify GEMINI_API_KEY."
            )
        elif response.status_code == 429:
            raise LLMRateLimitError("Gemini API rate limit exceeded. Please back off or retry later.")
        elif response.status_code >= 500:
            raise LLMProviderError(
                f"Gemini service returned an internal error (Status {response.status_code}): {response.text}",
                status_code=response.status_code,
            )
        elif response.status_code != 200:
            raise LLMProviderError(
                f"Gemini API returned unexpected status {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise LLMProviderError(f"Gemini returned empty candidates. Prompt may have been blocked: {data}")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise LLMProviderError("Gemini candidate contains no parts.")
            return str(parts[0].get("text", ""))
        except (KeyError, IndexError) as exc:
            raise LLMProviderError(f"Malformed Gemini API response envelope: {exc}") from exc

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: str | None = None,
        temperature: float | None = None,
    ) -> T:
        schema_json_guidance = (
            f"\n\nReturn strictly valid JSON conforming to this schema:\n"
            f"{json.dumps(schema.model_json_schema(), indent=2)}\n"
            f"Do not include any commentary or explanation outside the JSON."
        )
        augmented_prompt = prompt + schema_json_guidance

        url = self._get_url()
        payload = self._build_payload(
            prompt=augmented_prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            force_json=True,
        )

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(f"Gemini API timed out after {self.timeout}s: {exc}") from exc
            except httpx.RequestError as exc:
                raise LLMError(f"Network error calling Gemini API: {exc}") from exc

        if response.status_code == 401 or response.status_code == 403:
            raise LLMAuthenticationError(
                f"Authentication failed with Gemini API (Status {response.status_code}). Verify GEMINI_API_KEY."
            )
        elif response.status_code == 429:
            raise LLMRateLimitError("Gemini API rate limit exceeded.")
        elif response.status_code >= 500:
            raise LLMProviderError(
                f"Gemini service returned internal error (Status {response.status_code})",
                status_code=response.status_code,
            )
        elif response.status_code != 200:
            raise LLMProviderError(
                f"Gemini API returned unexpected status {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise LLMProviderError("Gemini returned no candidates.")
            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except (KeyError, IndexError) as exc:
            raise LLMProviderError(f"Malformed Gemini response structure: {exc}") from exc

        cleaned = clean_json_markdown(raw_text)
        try:
            parsed_json = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMMalformedJSONError(
                f"Failed to decode LLM response as JSON: {exc}",
                raw_content=raw_text,
            ) from exc

        try:
            return schema.model_validate(parsed_json)
        except ValidationError as exc:
            raise LLMValidationError(
                f"LLM JSON output does not match expected schema '{schema.__name__}': {exc}",
                raw_content=raw_text,
                validation_errors=exc.errors(),
            ) from exc

    async def health_check(self) -> bool:
        if not self._api_key:
            return False
        try:
            response = await self.generate_text("Reply with 'OK'", temperature=0.0)
            return bool(response.strip())
        except Exception as exc:
            logger.warning("Gemini health check failed: %s", exc)
            return False


# ==============================================================================
# Mock LLM Client (Offline, Zero-Cost Testing)
# ==============================================================================

class MockLLMClient(LLMClient):
    """Deterministic, offline mock client for unit testing and CI without API keys."""

    def __init__(self):
        self.call_history: list[dict[str, Any]] = []
        self._text_responses: dict[str, str] = {}
        self._structured_responses: dict[str, BaseModel] = {}
        self._should_timeout: bool = False
        self._should_fail_auth: bool = False
        self._should_return_malformed_json: bool = False
        self._default_text: str = "Mock LLM Response"

    def set_text_response(self, substring: str, response: str) -> None:
        """Configure mock to return `response` when `substring` is in the prompt."""
        self._text_responses[substring] = response

    def set_structured_response(self, schema_or_key: Type[T] | str, instance: BaseModel) -> None:
        """Register a canned structured instance for a schema class or key."""
        key = schema_or_key if isinstance(schema_or_key, str) else schema_or_key.__name__
        self._structured_responses[key] = instance

    def simulate_timeout(self, flag: bool = True) -> None:
        self._should_timeout = flag

    def simulate_auth_failure(self, flag: bool = True) -> None:
        self._should_fail_auth = flag

    def simulate_malformed_json(self, flag: bool = True) -> None:
        self._should_return_malformed_json = flag

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None,
    ) -> str:
        self.call_history.append({
            "type": "text",
            "prompt": prompt,
            "system_instruction": system_instruction,
            "temperature": temperature,
        })

        if self._should_timeout:
            raise LLMTimeoutError("Simulated timeout in MockLLMClient")
        if self._should_fail_auth:
            raise LLMAuthenticationError("Simulated authentication failure in MockLLMClient")

        for key, resp in self._text_responses.items():
            if key in prompt:
                return resp
        return self._default_text

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: str | None = None,
        temperature: float | None = None,
    ) -> T:
        self.call_history.append({
            "type": "structured",
            "prompt": prompt,
            "schema": schema.__name__,
            "system_instruction": system_instruction,
            "temperature": temperature,
        })

        if self._should_timeout:
            raise LLMTimeoutError("Simulated timeout in MockLLMClient")
        if self._should_fail_auth:
            raise LLMAuthenticationError("Simulated authentication failure in MockLLMClient")
        if self._should_return_malformed_json:
            raise LLMMalformedJSONError(
                "Simulated malformed JSON response from LLM",
                raw_content="{ 'invalid': json, missing_quotes }",
            )

        # Check registered responses by schema name
        if schema.__name__ in self._structured_responses:
            instance = self._structured_responses[schema.__name__]
            if isinstance(instance, schema):
                return instance
            # If registered as dict or subclass
            return schema.model_validate(instance)

        raise LLMError(
            f"MockLLMClient has no registered structured response for schema '{schema.__name__}'. "
            f"Use mock_client.set_structured_response('{schema.__name__}', instance) to register one."
        )

    async def health_check(self) -> bool:
        return not (self._should_fail_auth or self._should_timeout)


# ==============================================================================
# Client Factory
# ==============================================================================

def get_llm_client(settings: Settings | None = None) -> LLMClient:
    """Factory creating the appropriate LLMClient based on active settings."""
    cfg = settings or get_settings()
    if cfg.llm_provider == "mock":
        return MockLLMClient()
    elif cfg.llm_provider == "gemini":
        return GeminiClient(settings=cfg)
    else:
        raise ValueError(f"Unsupported LLM provider: {cfg.llm_provider}. Use 'gemini' or 'mock'.")
