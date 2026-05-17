"""Tests for AI client module."""

import pytest
from unittest.mock import Mock, patch

from pdf_summarizer.ai_client import (
    BaseAIClient,
    OpenAIClient,
    ClaudeClient,
    KimiClient,
    create_client,
)
from pdf_summarizer.models import AIProvider


class TestAIClients:
    """Test cases for AI clients."""

    def test_openai_client_requires_api_key(self):
        """Test OpenAI client raises error without API key."""
        with pytest.raises(ValueError, match="API key not configured"):
            OpenAIClient(api_key="", model="gpt-4o")

    def test_claude_client_requires_api_key(self):
        """Test Claude client raises error without API key."""
        with pytest.raises(ValueError, match="API key not configured"):
            ClaudeClient(api_key="", model="claude-sonnet-4-6-20250514")

    def test_kimi_client_requires_api_key(self):
        """Test Kimi client raises error without API key."""
        with pytest.raises(ValueError, match="API key not configured"):
            KimiClient(api_key="", model="moonshot-v1-8k")

    def test_create_client_openai(self):
        """Test creating OpenAI client."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            client = create_client(AIProvider.OPENAI)
            assert isinstance(client, OpenAIClient)

    def test_create_client_claude(self):
        """Test creating Claude client."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            client = create_client(AIProvider.CLAUDE)
            assert isinstance(client, ClaudeClient)

    def test_create_client_kimi(self):
        """Test creating Kimi client."""
        with patch.dict("os.environ", {"KIMI_API_KEY": "test-key"}):
            client = create_client(AIProvider.KIMI)
            assert isinstance(client, KimiClient)

    def test_create_client_invalid_provider(self):
        """Test creating client with invalid provider raises error."""
        with pytest.raises(ValueError, match="Unsupported AI provider"):
            create_client("invalid")  # type: ignore


class TestOpenAIClient:
    """Test OpenAI client functionality."""

    @patch("openai.OpenAI")
    def test_generate_calls_api(self, mock_openai):
        """Test generate method calls OpenAI API correctly."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = OpenAIClient(
            api_key="test-key",
            model="gpt-4o",
        )
        result = client.generate("System prompt", "User prompt")

        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once()
