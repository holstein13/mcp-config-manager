"""
Tests for CLI command parser
"""

import pytest
from src.mcp_config_manager.parsers.cli_parser import ClaudeCliParser, parse_cli_to_json


class TestClaudeCliParser:
    """Test cases for Claude CLI command parser"""

    def test_is_cli_command_valid(self):
        """Test detection of valid CLI commands"""
        assert ClaudeCliParser.is_cli_command("claude mcp add servername -- npx test")
        assert ClaudeCliParser.is_cli_command("  claude mcp add server  ")
        assert ClaudeCliParser.is_cli_command("claude mcp add --transport sse linear https://example.com")

    def test_is_cli_command_invalid(self):
        """Test detection of invalid CLI commands"""
        assert not ClaudeCliParser.is_cli_command('{"server": {}}')
        assert not ClaudeCliParser.is_cli_command("some other command")
        assert not ClaudeCliParser.is_cli_command("")
        assert not ClaudeCliParser.is_cli_command("claude mcp list")

    def test_is_cli_command_false_positive_prevention(self):
        """Test that JSON starting with { or [ is not mistaken for CLI command"""
        # JSON object that happens to contain the CLI prefix as a key
        assert not ClaudeCliParser.is_cli_command('{"claude mcp add": "value"}')
        # JSON array
        assert not ClaudeCliParser.is_cli_command('["claude mcp add", "something"]')
        # JSON with whitespace
        assert not ClaudeCliParser.is_cli_command('  {"server": "claude mcp add test"}')
        assert not ClaudeCliParser.is_cli_command('  ["data"]')

    def test_parse_basic_stdio_command(self):
        """Test parsing a basic stdio command"""
        command = "claude mcp add myserver -- npx -y @package/name"
        result = ClaudeCliParser.parse_cli_command(command)

        assert "myserver" in result
        assert result["myserver"]["command"] == "npx"
        assert result["myserver"]["args"] == ["-y", "@package/name"]
        assert "env" not in result["myserver"]

    def test_parse_command_with_single_env_var(self):
        """Test parsing command with single environment variable"""
        command = "claude mcp add firecrawl -e FIRECRAWL_API_KEY=test-key -- npx -y firecrawl-mcp"
        result = ClaudeCliParser.parse_cli_command(command)

        assert "firecrawl" in result
        assert result["firecrawl"]["command"] == "npx"
        assert result["firecrawl"]["args"] == ["-y", "firecrawl-mcp"]
        assert result["firecrawl"]["env"]["FIRECRAWL_API_KEY"] == "test-key"

    def test_parse_command_with_multiple_env_vars(self):
        """Test parsing command with multiple environment variables"""
        command = "claude mcp add myserver -e KEY1=value1 -e KEY2=value2 -- node server.js"
        result = ClaudeCliParser.parse_cli_command(command)

        assert "myserver" in result
        assert result["myserver"]["env"]["KEY1"] == "value1"
        assert result["myserver"]["env"]["KEY2"] == "value2"

    def test_parse_command_with_env_flag_variant(self):
        """Test parsing command with --env flag (not just -e)"""
        command = "claude mcp add myserver --env API_KEY=test -- npx package"
        result = ClaudeCliParser.parse_cli_command(command)

        assert result["myserver"]["env"]["API_KEY"] == "test"

    def test_parse_sse_transport(self):
        """Test parsing SSE transport command"""
        command = "claude mcp add --transport sse linear-server https://mcp.linear.app/sse"
        result = ClaudeCliParser.parse_cli_command(command)

        assert "linear-server" in result
        assert result["linear-server"]["type"] == "sse"
        assert result["linear-server"]["url"] == "https://mcp.linear.app/sse"
        assert "command" not in result["linear-server"]

    def test_parse_sse_with_https(self):
        """Test parsing SSE command with HTTPS URL"""
        command = "claude mcp add --transport sse my-sse-server https://example.com/sse"
        result = ClaudeCliParser.parse_cli_command(command)

        assert result["my-sse-server"]["type"] == "sse"
        assert result["my-sse-server"]["url"] == "https://example.com/sse"

    def test_parse_command_with_scope(self):
        """Test parsing command with --scope flag"""
        command = "claude mcp add --scope global myserver -- npx package"
        result = ClaudeCliParser.parse_cli_command(command)

        # Scope doesn't affect the JSON structure, just ensure command parses
        assert "myserver" in result
        assert result["myserver"]["command"] == "npx"

    def test_parse_complex_command(self):
        """Test parsing complex command with multiple flags"""
        command = "claude mcp add myserver -e KEY1=val1 -e KEY2=val2 --scope project -- npx -y @org/package arg1 arg2"
        result = ClaudeCliParser.parse_cli_command(command)

        assert "myserver" in result
        assert result["myserver"]["command"] == "npx"
        assert result["myserver"]["args"] == ["-y", "@org/package", "arg1", "arg2"]
        assert result["myserver"]["env"]["KEY1"] == "val1"
        assert result["myserver"]["env"]["KEY2"] == "val2"

    def test_parse_command_without_separator(self):
        """Test parsing command without -- separator (edge case)"""
        command = "claude mcp add myserver npx -y package"
        result = ClaudeCliParser.parse_cli_command(command)

        # Without --, the parser should treat remaining tokens as command
        assert "myserver" in result
        assert result["myserver"]["command"] == "npx"
        assert "-y" in result["myserver"]["args"]
        assert "package" in result["myserver"]["args"]

    def test_parse_command_with_quoted_args(self):
        """Test parsing command with quoted arguments"""
        command = 'claude mcp add myserver -- node server.js --arg "value with spaces"'
        result = ClaudeCliParser.parse_cli_command(command)

        assert result["myserver"]["command"] == "node"
        assert "server.js" in result["myserver"]["args"]
        assert "--arg" in result["myserver"]["args"]
        assert "value with spaces" in result["myserver"]["args"]

    def test_error_on_empty_command(self):
        """Test error when command is empty after prefix"""
        with pytest.raises(ValueError, match="No server configuration provided"):
            ClaudeCliParser.parse_cli_command("claude mcp add")

    def test_error_on_invalid_prefix(self):
        """Test error when command doesn't start with correct prefix"""
        with pytest.raises(ValueError, match="must start with 'claude mcp add'"):
            ClaudeCliParser.parse_cli_command("something else")

    def test_error_on_missing_server_name(self):
        """Test error when server name is missing"""
        with pytest.raises(ValueError, match="No server name provided"):
            ClaudeCliParser.parse_cli_command("claude mcp add -- npx package")

    def test_error_on_missing_env_value(self):
        """Test error when -e flag has no value"""
        with pytest.raises(ValueError, match="flag requires a value"):
            ClaudeCliParser.parse_cli_command("claude mcp add myserver -e")

    def test_error_on_invalid_env_format(self):
        """Test error when env var doesn't have = separator"""
        with pytest.raises(ValueError, match="Invalid environment variable format"):
            ClaudeCliParser.parse_cli_command("claude mcp add myserver -e INVALIDFORMAT -- npx pkg")

    def test_error_on_missing_transport_value(self):
        """Test error when --transport flag has no value"""
        with pytest.raises(ValueError, match="--transport flag requires a value"):
            ClaudeCliParser.parse_cli_command("claude mcp add --transport")

    def test_error_on_sse_without_url(self):
        """Test error when SSE transport has no URL"""
        with pytest.raises(ValueError, match="SSE transport requires a valid URL"):
            ClaudeCliParser.parse_cli_command("claude mcp add --transport sse myserver")

    def test_error_on_stdio_without_command(self):
        """Test error when stdio transport has no command"""
        with pytest.raises(ValueError, match="No command provided"):
            ClaudeCliParser.parse_cli_command("claude mcp add myserver --")

    def test_parse_cli_to_json_convenience_function(self):
        """Test the convenience function"""
        command = "claude mcp add testserver -- npx test-package"
        result = parse_cli_to_json(command)

        assert "testserver" in result
        assert result["testserver"]["command"] == "npx"

    def test_real_world_example_firecrawl(self):
        """Test real-world example from issue #6: Firecrawl"""
        command = "claude mcp add firecrawl -e FIRECRAWL_API_KEY=your-api-key -- npx -y firecrawl-mcp"
        result = ClaudeCliParser.parse_cli_command(command)

        expected = {
            "firecrawl": {
                "command": "npx",
                "args": ["-y", "firecrawl-mcp"],
                "env": {
                    "FIRECRAWL_API_KEY": "your-api-key"
                }
            }
        }

        assert result == expected

    def test_real_world_example_linear(self):
        """Test real-world example from issue #6: Linear"""
        command = "claude mcp add --transport sse linear-server https://mcp.linear.app/sse"
        result = ClaudeCliParser.parse_cli_command(command)

        expected = {
            "linear-server": {
                "type": "sse",
                "url": "https://mcp.linear.app/sse"
            }
        }

        assert result == expected

    def test_env_var_with_equals_in_value(self):
        """Test environment variable with = in the value"""
        command = "claude mcp add myserver -e KEY=value=with=equals -- npx pkg"
        result = ClaudeCliParser.parse_cli_command(command)

        # Should split on first = only
        assert result["myserver"]["env"]["KEY"] == "value=with=equals"

    def test_env_var_with_empty_value(self):
        """Test environment variable with empty value"""
        command = "claude mcp add myserver -e KEY= -- npx pkg"
        result = ClaudeCliParser.parse_cli_command(command)

        assert result["myserver"]["env"]["KEY"] == ""

    def test_command_with_many_args(self):
        """Test command with many arguments"""
        command = "claude mcp add myserver -- node script.js --arg1 val1 --arg2 val2 --flag"
        result = ClaudeCliParser.parse_cli_command(command)

        assert result["myserver"]["command"] == "node"
        assert len(result["myserver"]["args"]) == 6
        assert "--flag" in result["myserver"]["args"]

    def test_server_name_with_special_chars(self):
        """Test server name with hyphens and underscores"""
        command = "claude mcp add my-special_server-123 -- npx pkg"
        result = ClaudeCliParser.parse_cli_command(command)

        assert "my-special_server-123" in result

    def test_parse_command_strips_whitespace(self):
        """Test that command handles extra whitespace"""
        command = "  claude   mcp   add   myserver   --   npx   package  "
        result = ClaudeCliParser.parse_cli_command(command)

        assert "myserver" in result
        assert result["myserver"]["command"] == "npx"

    # mcp-remote conversion tests
    def test_mcp_remote_conversion_disabled_default(self):
        """Test mcp-remote command preserved when conversion disabled (default)"""
        command = "claude mcp add linear -- npx -y mcp-remote https://mcp.linear.app/sse"
        result = ClaudeCliParser.parse_cli_command(command)

        assert "linear" in result
        assert result["linear"]["command"] == "npx"
        assert result["linear"]["args"] == ["-y", "mcp-remote", "https://mcp.linear.app/sse"]
        assert "type" not in result["linear"]
        assert "url" not in result["linear"]

    def test_mcp_remote_conversion_disabled_explicit(self):
        """Test mcp-remote command preserved when explicitly disabled"""
        command = "claude mcp add linear -- npx -y mcp-remote https://mcp.linear.app/sse"
        result = ClaudeCliParser.parse_cli_command(command, convert_mcp_remote=False)

        assert "linear" in result
        assert result["linear"]["command"] == "npx"
        assert result["linear"]["args"] == ["-y", "mcp-remote", "https://mcp.linear.app/sse"]
        assert "type" not in result["linear"]
        assert "url" not in result["linear"]

    def test_mcp_remote_conversion_enabled(self):
        """Test mcp-remote command conversion when enabled"""
        command = "claude mcp add linear -- npx -y mcp-remote https://mcp.linear.app/sse"
        result = ClaudeCliParser.parse_cli_command(command, convert_mcp_remote=True)

        assert "linear" in result
        assert result["linear"]["type"] == "sse"
        assert result["linear"]["url"] == "https://mcp.linear.app/sse"
        assert "command" not in result["linear"]
        assert "args" not in result["linear"]

    def test_mcp_remote_conversion_without_y_flag(self):
        """Test mcp-remote conversion works without -y flag"""
        command = "claude mcp add linear -- npx mcp-remote https://mcp.linear.app/sse"
        result = ClaudeCliParser.parse_cli_command(command, convert_mcp_remote=True)

        assert result["linear"]["type"] == "sse"
        assert result["linear"]["url"] == "https://mcp.linear.app/sse"

    def test_mcp_remote_conversion_with_env(self):
        """Test mcp-remote conversion preserves environment variables"""
        command = "claude mcp add linear -e API_KEY=test -- npx -y mcp-remote https://mcp.linear.app/sse"
        result = ClaudeCliParser.parse_cli_command(command, convert_mcp_remote=True)

        assert result["linear"]["type"] == "sse"
        assert result["linear"]["url"] == "https://mcp.linear.app/sse"
        assert result["linear"]["env"]["API_KEY"] == "test"

    def test_regular_npx_not_converted(self):
        """Test that regular npx commands are not mistakenly converted"""
        command = "claude mcp add firecrawl -- npx -y @mendable/firecrawl-mcp"
        result = ClaudeCliParser.parse_cli_command(command, convert_mcp_remote=True)

        # Should remain as command/args since it's not mcp-remote
        assert result["firecrawl"]["command"] == "npx"
        assert result["firecrawl"]["args"] == ["-y", "@mendable/firecrawl-mcp"]
        assert "type" not in result["firecrawl"]

    def test_native_sse_transport_still_works(self):
        """Test that native SSE transport flag still works"""
        command = "claude mcp add linear --transport sse https://mcp.linear.app/sse"
        result = ClaudeCliParser.parse_cli_command(command, convert_mcp_remote=False)

        assert result["linear"]["type"] == "sse"
        assert result["linear"]["url"] == "https://mcp.linear.app/sse"
        assert "command" not in result["linear"]

    def test_is_mcp_remote_command(self):
        """Test _is_mcp_remote_command helper"""
        assert ClaudeCliParser._is_mcp_remote_command(["npx", "-y", "mcp-remote", "https://test.com"])
        assert ClaudeCliParser._is_mcp_remote_command(["npx", "mcp-remote", "https://test.com"])
        assert not ClaudeCliParser._is_mcp_remote_command(["npx", "-y", "@package/name"])
        assert not ClaudeCliParser._is_mcp_remote_command(["node", "server.js"])
        assert not ClaudeCliParser._is_mcp_remote_command([])

    def test_extract_mcp_remote_url(self):
        """Test _extract_mcp_remote_url helper"""
        url = ClaudeCliParser._extract_mcp_remote_url(["npx", "-y", "mcp-remote", "https://mcp.linear.app/sse"])
        assert url == "https://mcp.linear.app/sse"

        url = ClaudeCliParser._extract_mcp_remote_url(["npx", "mcp-remote", "http://localhost:3000"])
        assert url == "http://localhost:3000"

    def test_extract_mcp_remote_url_missing(self):
        """Test _extract_mcp_remote_url raises error when URL is missing"""
        with pytest.raises(ValueError, match="No URL provided after mcp-remote"):
            ClaudeCliParser._extract_mcp_remote_url(["npx", "mcp-remote"])

    def test_extract_mcp_remote_url_invalid(self):
        """Test _extract_mcp_remote_url raises error for invalid URL"""
        with pytest.raises(ValueError, match="Invalid URL for mcp-remote"):
            ClaudeCliParser._extract_mcp_remote_url(["npx", "mcp-remote", "not-a-url"])

    def test_extract_mcp_remote_url_invalid_prefix(self):
        """Test _extract_mcp_remote_url raises error for URLs with invalid prefix"""
        # Should reject URLs that start with 'http' but aren't valid http:// or https://
        with pytest.raises(ValueError, match="Invalid URL for mcp-remote"):
            ClaudeCliParser._extract_mcp_remote_url(["npx", "mcp-remote", "httpgarbage"])

        with pytest.raises(ValueError, match="Invalid URL for mcp-remote"):
            ClaudeCliParser._extract_mcp_remote_url(["npx", "mcp-remote", "httpsomething"])
