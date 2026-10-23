"""Unit tests for LLM client abstractions, Gemini REST adapter, and Mock client."""

import pytest
from pydantic import BaseModel, SecretStr

from backend.app.core.config import Settings
from backend.app.integrations.llm_client import (
    GeminiClient,
    LLMAuthenticationError,
    LLMError,
    LLMMalformedJSONError,
    LLMTimeoutError,
    MockLLMClient,
    clean_json_markdown,
    get_llm_client,
)
from backend.app.schemas import RequirementAnalysisResult


class SimpleTestSchema(BaseModel):
    message: str
    count: int


@pytest.mark.asyncio
async def test_mock_llm_client_text_generation():
    client = MockLLMClient()
    client.set_text_response("Hello", "Hi there, engineer!")

    res = await client.generate_text("Hello model")
    assert res == "Hi there, engineer!"
    assert len(client.call_history) == 1
    assert client.call_history[0]["type"] == "text"


@pytest.mark.asyncio
async def test_mock_llm_client_structured_generation(sample_analysis_result: RequirementAnalysisResult):
    client = MockLLMClient()
    client.set_structured_response(RequirementAnalysisResult, sample_analysis_result)

    result = await client.generate_structured(
        prompt="Analyze this invoice spec",
        schema=RequirementAnalysisResult,
    )
    assert isinstance(result, RequirementAnalysisResult)
    assert result.project_name == "FinDoc Invoice Reconciliation System"
    assert len(result.modules) == 2
    assert len(client.call_history) == 1
    assert client.call_history[0]["schema"] == "RequirementAnalysisResult"


@pytest.mark.asyncio
async def test_mock_llm_client_unregistered_schema_raises_error():
    client = MockLLMClient()
    with pytest.raises(LLMError) as exc_info:
        await client.generate_structured(
            prompt="Test prompt",
            schema=SimpleTestSchema,
        )
    assert "no registered structured response" in str(exc_info.value)


@pytest.mark.asyncio
async def test_mock_llm_client_simulated_timeout():
    client = MockLLMClient()
    client.simulate_timeout(True)

    with pytest.raises(LLMTimeoutError):
        await client.generate_text("Should timeout")


@pytest.mark.asyncio
async def test_mock_llm_client_simulated_auth_failure():
    client = MockLLMClient()
    client.simulate_auth_failure(True)

    with pytest.raises(LLMAuthenticationError):
        await client.generate_text("Should fail auth")


@pytest.mark.asyncio
async def test_mock_llm_client_simulated_malformed_json():
    client = MockLLMClient()
    client.simulate_malformed_json(True)

    with pytest.raises(LLMMalformedJSONError) as exc_info:
        await client.generate_structured(
            prompt="Generate JSON",
            schema=SimpleTestSchema,
        )
    assert "malformed JSON" in str(exc_info.value)
    assert exc_info.value.raw_content is not None


def test_clean_json_markdown():
    # Case 1: Plain JSON
    raw_plain = '{"key": "value"}'
    assert clean_json_markdown(raw_plain) == '{"key": "value"}'

    # Case 2: ```json ... ``` code fence
    raw_fenced = '```json\n{"key": "value"}\n```'
    assert clean_json_markdown(raw_fenced) == '{"key": "value"}'

    # Case 3: ``` ... ``` code fence without language
    raw_no_lang = '```\n{"key": "value"}\n```'
    assert clean_json_markdown(raw_no_lang) == '{"key": "value"}'

    # Case 4: Extra whitespace
    raw_spaced = '   ```json\n  {"key": "value"}  \n```  '
    assert clean_json_markdown(raw_spaced) == '{"key": "value"}'


def test_gemini_client_payload_construction():
    settings = Settings(
        gemini_api_key=SecretStr("test-key"),
        gemini_model="gemini-2.0-flash",
        llm_temperature=0.3,
    )
    client = GeminiClient(settings=settings)

    payload = client._build_payload(
        prompt="Analyze specifications",
        system_instruction="You are an AI architect.",
        temperature=0.5,
        force_json=True,
    )

    assert payload["contents"][0]["role"] == "user"
    assert payload["contents"][0]["parts"][0]["text"] == "Analyze specifications"
    assert payload["systemInstruction"]["parts"][0]["text"] == "You are an AI architect."
    assert payload["generationConfig"]["temperature"] == 0.5
    assert payload["generationConfig"]["responseMimeType"] == "application/json"


def test_gemini_client_missing_api_key_raises_auth_error():
    empty_settings = Settings(gemini_api_key=SecretStr(""))
    client = GeminiClient(settings=empty_settings)

    with pytest.raises(LLMAuthenticationError) as exc_info:
        client._get_url()
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)


def test_get_llm_client_factory():
    mock_settings = Settings(llm_provider="mock")
    client1 = get_llm_client(mock_settings)
    assert isinstance(client1, MockLLMClient)

    gemini_settings = Settings(llm_provider="gemini", gemini_api_key=SecretStr("abc"))
    client2 = get_llm_client(gemini_settings)
    assert isinstance(client2, GeminiClient)
