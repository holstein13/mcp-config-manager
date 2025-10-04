#!/usr/bin/env python3
"""
Quick test script to verify Issue #7 fix
Tests that HTTP and SSE servers don't require command field
"""

from src.mcp_config_manager.parsers.claude_parser import ClaudeConfigParser
from src.mcp_config_manager.parsers.gemini_parser import GeminiConfigParser
from src.mcp_config_manager.parsers.codex_parser import CodexConfigParser


def test_ref_http_server():
    """Test Ref HTTP server from issue #7"""
    print("Testing Ref HTTP server (from issue #7)...")

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

    parsers = {
        "Claude": ClaudeConfigParser(),
        "Gemini": GeminiConfigParser(),
        "Codex": CodexConfigParser()
    }

    for name, parser in parsers.items():
        result = parser.validate(config)
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name} parser: {status}")
        if not result:
            return False

    return True


def test_linear_sse_server():
    """Test Linear SSE server from issue #7"""
    print("\nTesting Linear SSE server (from issue #7)...")

    config = {
        "mcpServers": {
            "linear-server": {
                "type": "sse",
                "url": "https://mcp.linear.app/sse"
            }
        }
    }

    parsers = {
        "Claude": ClaudeConfigParser(),
        "Gemini": GeminiConfigParser(),
        "Codex": CodexConfigParser()
    }

    for name, parser in parsers.items():
        result = parser.validate(config)
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name} parser: {status}")
        if not result:
            return False

    return True


def test_exa_http_server():
    """Test Exa HTTP server from issue #7"""
    print("\nTesting Exa HTTP server (from issue #7)...")

    config = {
        "mcpServers": {
            "exa": {
                "type": "http",
                "url": "https://mcp.exa.ai/mcp",
                "headers": {}
            }
        }
    }

    parsers = {
        "Claude": ClaudeConfigParser(),
        "Gemini": GeminiConfigParser(),
        "Codex": CodexConfigParser()
    }

    for name, parser in parsers.items():
        result = parser.validate(config)
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name} parser: {status}")
        if not result:
            return False

    return True


def test_stdio_still_requires_command():
    """Verify stdio servers still require command field"""
    print("\nVerifying stdio servers still require command...")

    # Should fail without command
    config_invalid = {
        "mcpServers": {
            "test": {
                "type": "stdio",
                "args": []
            }
        }
    }

    # Should pass with command
    config_valid = {
        "mcpServers": {
            "test": {
                "type": "stdio",
                "command": "node",
                "args": []
            }
        }
    }

    parser = ClaudeConfigParser()

    invalid_result = parser.validate(config_invalid)
    valid_result = parser.validate(config_valid)

    print(f"  Without command: {'✗ FAIL (expected)' if not invalid_result else '✓ PASS (unexpected)'}")
    print(f"  With command: {'✓ PASS' if valid_result else '✗ FAIL'}")

    return not invalid_result and valid_result


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Issue #7 Fix: HTTP/SSE servers without command field")
    print("=" * 60)

    all_pass = True
    all_pass &= test_ref_http_server()
    all_pass &= test_linear_sse_server()
    all_pass &= test_exa_http_server()
    all_pass &= test_stdio_still_requires_command()

    print("\n" + "=" * 60)
    if all_pass:
        print("✓ All tests PASSED!")
        print("\nHTTP and SSE servers no longer require the command field.")
        print("You can now use configurations like:")
        print("  • Ref (HTTP): url + headers, no command needed")
        print("  • Linear (SSE): url only, no command needed")
        print("  • Exa (HTTP): url + headers, no command needed")
    else:
        print("✗ Some tests FAILED")
        exit(1)
    print("=" * 60)
