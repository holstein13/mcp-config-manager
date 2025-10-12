"""
Test validation of HTTP and SSE server configurations (Issue #7)
"""

import pytest
from pathlib import Path
import tempfile
import json
from src.mcp_config_manager.parsers.claude_parser import ClaudeConfigParser
from src.mcp_config_manager.parsers.gemini_parser import GeminiConfigParser
from src.mcp_config_manager.parsers.codex_parser import CodexConfigParser


class TestHTTPServerValidation:
    """Test HTTP server validation across all parsers"""

    def test_claude_parser_http_server_without_command(self):
        """Test that Claude parser accepts HTTP servers without command field"""
        parser = ClaudeConfigParser()

        # HTTP server config without command (should be valid)
        config = {
            "mcpServers": {
                "ref": {
                    "type": "http",
                    "url": "https://api.ref.tools/mcp",
                    "headers": {
                        "x-ref-api-key": "API_KEY_HERE"
                    }
                }
            }
        }

        assert parser.validate(config) is True

    def test_claude_parser_http_server_requires_url(self):
        """Test that Claude parser requires URL for HTTP servers"""
        parser = ClaudeConfigParser()

        # HTTP server config without url (should be invalid)
        config = {
            "mcpServers": {
                "ref": {
                    "type": "http",
                    "headers": {}
                }
            }
        }

        assert parser.validate(config) is False

    def test_claude_parser_stdio_server_requires_command(self):
        """Test that Claude parser still requires command for stdio servers"""
        parser = ClaudeConfigParser()

        # stdio server without command (should be invalid)
        config = {
            "mcpServers": {
                "test": {
                    "type": "stdio",
                    "args": []
                }
            }
        }

        assert parser.validate(config) is False

        # stdio server with command (should be valid)
        config_valid = {
            "mcpServers": {
                "test": {
                    "type": "stdio",
                    "command": "node",
                    "args": []
                }
            }
        }

        assert parser.validate(config_valid) is True


class TestSSEServerValidation:
    """Test SSE server validation across all parsers"""

    def test_claude_parser_sse_server_without_command(self):
        """Test that Claude parser accepts SSE servers without command field"""
        parser = ClaudeConfigParser()

        # SSE server config without command (should be valid)
        config = {
            "mcpServers": {
                "linear-server": {
                    "type": "sse",
                    "url": "https://mcp.linear.app/sse"
                }
            }
        }

        assert parser.validate(config) is True

    def test_gemini_parser_sse_server_without_command(self):
        """Test that Gemini parser accepts SSE servers without command field"""
        parser = GeminiConfigParser()

        # SSE server config without command (should be valid)
        config = {
            "mcpServers": {
                "linear-server": {
                    "type": "sse",
                    "url": "https://mcp.linear.app/sse"
                }
            }
        }

        assert parser.validate(config) is True

    def test_codex_parser_sse_server_without_command(self):
        """Test that Codex parser accepts SSE servers without command field"""
        parser = CodexConfigParser()

        # SSE server config without command (should be valid)
        config = {
            "mcpServers": {
                "linear-server": {
                    "type": "sse",
                    "url": "https://mcp.linear.app/sse"
                }
            }
        }

        assert parser.validate(config) is True


class TestRealWorldExamples:
    """Test real-world examples from issue #7"""

    def test_ref_server_example(self):
        """Test the Ref server example from issue #7"""
        parser = ClaudeConfigParser()

        # Exact example from issue #7
        config = {
            "mcpServers": {
                "Ref": {
                    "type": "http",
                    "url": "https://api.ref.tools/mcp",
                    "headers": {
                        "x-ref-api-key": "API_KEY_HERE"
                    }
                }
            }
        }

        assert parser.validate(config) is True

    def test_linear_server_example(self):
        """Test the Linear server example from issue #7"""
        parser = ClaudeConfigParser()

        # Example from issue #7 comments
        config = {
            "mcpServers": {
                "linear-server": {
                    "type": "sse",
                    "url": "https://mcp.linear.app/sse"
                }
            }
        }

        assert parser.validate(config) is True

    def test_exa_server_example(self):
        """Test the Exa server example from issue #7"""
        parser = ClaudeConfigParser()

        # Example from issue #7 comments
        config = {
            "mcpServers": {
                "exa": {
                    "type": "http",
                    "url": "https://mcp.exa.ai/mcp",
                    "headers": {}
                }
            }
        }

        assert parser.validate(config) is True

    def test_codex_parser_preserves_http_without_command(self):
        """Test that Codex parser can write HTTP servers without adding default command"""
        parser = CodexConfigParser()

        config = {
            "mcpServers": {
                "ref": {
                    "type": "http",
                    "url": "https://api.ref.tools/mcp",
                    "headers": {
                        "x-ref-api-key": "API_KEY_HERE"
                    }
                }
            }
        }

        # Validate the config
        assert parser.validate(config) is True

        # Write and read back
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            temp_path = Path(f.name)

        try:
            parser.write(config, temp_path)
            result = parser.parse(temp_path)

            # Should preserve the HTTP server without adding a command
            assert "ref" in result["mcpServers"]
            assert result["mcpServers"]["ref"]["type"] == "http"
            assert result["mcpServers"]["ref"]["url"] == "https://api.ref.tools/mcp"
            # Command should either be absent or empty, not a default value
            assert result["mcpServers"]["ref"].get("command", "") in ("", None)
        finally:
            temp_path.unlink()
