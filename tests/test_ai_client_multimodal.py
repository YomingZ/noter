"""Tests for AI client multimodal support."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from pdf_summarizer.ai_client import (
    OpenAIClient,
    ClaudeClient,
    KimiClient,
    generate_multimodal_summary,
    BaseAIClient,
)
from pdf_summarizer.models import AIProvider, ContentPart


class TestMultimodalBaseClient:
    """Behavior: BaseAIClient multimodal interface."""

    def test_abstract_method_requires_implementation(self):
        with pytest.raises(TypeError):
            BadClient = type("BadClient", (BaseAIClient,), {"_call_api": lambda s, a, b: ""})
            BadClient(api_key="test", model="test", provider="test")

    def test_supports_vision_openai(self):
        client = OpenAIClient(api_key="sk-test", model="gpt-4o")
        assert client.supports_vision() is True

    def test_supports_vision_openai_mini(self):
        client = OpenAIClient(api_key="sk-test", model="gpt-4o-mini")
        assert client.supports_vision() is True

    def test_supports_vision_claude_sonnet(self):
        client = ClaudeClient(api_key="sk-ant-test", model="claude-sonnet-4-6-20250514")
        assert client.supports_vision() is True

    def test_supports_vision_kimi_false(self):
        client = KimiClient(api_key="sk-test", model="moonshot-v1-128k")
        assert client.supports_vision() is False


class TestContentPart:
    """Behavior: ContentPart multimodal format conversion."""

    def test_text_to_openai(self):
        part = ContentPart(type="text", text="describe this image")
        result = part.to_openai_format()
        assert result == {"type": "text", "text": "describe this image"}

    def test_image_to_openai(self):
        part = ContentPart(type="image", image_base64="fakebase64data")
        result = part.to_openai_format()
        assert result["type"] == "image_url"
        assert "data:image/png;base64,fakebase64data" == result["image_url"]["url"]

    def test_image_to_claude(self):
        part = ContentPart(type="image", image_base64="fakebase64data")
        result = part.to_claude_format()
        assert result["type"] == "image"
        assert result["source"]["type"] == "base64"
        assert result["source"]["media_type"] == "image/png"
        assert result["source"]["data"] == "fakebase64data"


class TestGenerateMultimodalSummary:
    """Behavior: generate_multimodal_summary handles vision and fallback."""

    def test_multimodal_with_vision_model(self):
        parts = [
            ContentPart(type="text", text="课件内容"),
            ContentPart(type="image", image_base64="imgdata"),
        ]
        with patch("pdf_summarizer.ai_client.create_client") as mock_create:
            mock_client = MagicMock(spec=OpenAIClient)
            mock_client.supports_vision.return_value = True
            mock_client.generate_multimodal.return_value = "AI response with image analysis"
            mock_create.return_value = mock_client

            result = generate_multimodal_summary(
                content_parts=parts,
                provider=AIProvider.OPENAI,
            )

            assert result == "AI response with image analysis"
            mock_client.generate_multimodal.assert_called_once()

    def test_multimodal_fallback_to_text(self):
        parts = [
            ContentPart(type="text", text="课件内容"),
        ]
        with patch("pdf_summarizer.ai_client.create_client") as mock_create:
            mock_client = MagicMock(spec=KimiClient)
            mock_client.supports_vision.return_value = False
            mock_client.generate_multimodal.return_value = "text-only response"
            mock_create.return_value = mock_client

            result = generate_multimodal_summary(
                content_parts=parts,
                provider=AIProvider.KIMI,
            )

            assert result == "text-only response"
