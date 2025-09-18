# Configuring MCP Servers for Codex CLI

Codex CLI loads its Model Context Protocol (MCP) configuration from `~/.codex/config.toml`. This file is a standard TOML document with three common sections:

- The root keys (for example `model = "gpt-5-codex"`).
- Optional project trust scopes under `[projects."/absolute/path"]`.
- One table per MCP server definition under `[mcp_servers.<name>]`.

Understanding the shape of that last section is the key to getting MCP servers to start reliably inside Codex.

## MCP server table anatomy

Each server lives inside a dedicated TOML table named after the server identifier you want to expose to Codex. The following keys are recognized:

| Key | Required? | Purpose |
| --- | --- | --- |
| `type` | ✅ | Transport to use. Typical values are `"http"` when Codex talks to an already running HTTP endpoint, or `"stdio"` when Codex must spawn a subprocess that speaks MCP over standard I/O. |
| `url` | ➕ (HTTP) | Full URL for `type = "http"`. Codex connects directly; it does **not** run a command when `url` is present. |
| `command` | ➕ (stdio) | Executable to launch when `type = "stdio"`. |
| `args` | ➕ (stdio) | Array of extra command-line arguments. Include package name (`npx`, `uvx`, etc.) flags, and target script here. |
| `env` | ➕ (stdio) | Table of environment variables to expose to the spawned process. |
| `headers` | ➕ (HTTP) | Table of HTTP headers, typically for API keys or custom auth. |
| `enabled` | Optional | Boolean toggle. When omitted, Codex treats the server as enabled. |

Codex inherits the standard MCP expectations: `stdio` transports must produce MCP responses over stdout, while `http` transports expect an MCP 1.0-compatible HTTP endpoint.

### Why HTTP servers must use `url`

When `type = "http"`, Codex assumes it should connect to a remote service; supplying `command`/`args` in that scenario causes Codex to wait for a URL that never appears, resulting in timeouts. If you need to launch a helper process, declare the server as `type = "stdio"` instead.

## Translating JSON MCP configs to Codex TOML

Claude Desktop and Gemini store MCP definitions in JSON (e.g. `~/.claude.json` or `~/.gemini/settings.json`). To reuse those servers in Codex:

1. **Pick the server name** – this becomes the TOML table suffix `context7` → `[mcp_servers.context7]`.
2. **Copy the transport fields**:
   - If the JSON object has a `"type": "http"` and `"url"`, keep those values and omit `command`/`args`.
   - If it contains `"command"`/`"args"`, use `type = "stdio"` (or keep the existing `"type"` if it already says `stdio`).
3. **Translate nested maps**:
   - JSON `headers` becomes a nested table (`[mcp_servers.<name>.headers]`).
   - JSON `env` becomes `[mcp_servers.<name>.env]`.
4. **Preserve arrays** – JSON arrays map directly to TOML arrays (`args = ["-y", "pkg"]`).
5. **Keep flags like `enabled`** – copy boolean fields as-is.

### Example: HTTP server copy

JSON source (`~/.claude.json`):

```json
"context7": {
  "type": "http",
  "url": "https://mcp.context7.com/mcp",
  "headers": {
    "CONTEXT7_API_KEY": "ctx7sk-..."
  }
}
```

Codex TOML (`~/.codex/config.toml`):

```toml
[mcp_servers.context7]
type = "http"
url = "https://mcp.context7.com/mcp"

[mcp_servers.context7.headers]
CONTEXT7_API_KEY = "ctx7sk-..."
```

### Example: stdio server copy

JSON source (`disabled_servers.json` or an MCP preset):

```json
"browsermcp": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@browsermcp/mcp@latest"],
  "env": {
    "BROWSER_MCP_LOG_LEVEL": "info"
  }
}
```

Codex TOML:

```toml
[mcp_servers.browsermcp]
type = "stdio"
command = "npx"
args = ["-y", "@browsermcp/mcp@latest"]

[mcp_servers.browsermcp.env]
BROWSER_MCP_LOG_LEVEL = "info"
```

### Quick conversion checklist

- `type` stays the same; only switch to `"stdio"` if you need Codex to spawn the process.
- Remove any JSON-only metadata that Codex does not understand (e.g. app-specific UI hints).
- Ensure all strings are quoted; TOML accepts single or double quotes, but double quotes avoid escaping issues.
- If using `npx`, include `"-y"` to prevent interactive prompts that would stall the stdio bridge.

## Validating and reloading

After editing `config.toml`:

1. Run `codex config --show mcp` (or simply restart Codex CLI) to confirm the server loads.
2. Watch the CLI output for `failed to start` messages—timeouts usually point to an HTTP/stdio mismatch or an executable that cannot be found.
3. Keep secrets (API keys) scoped to headers/env; TOML supports inline comments if you need context, but avoid committing secrets to version control.

With these conventions, you can translate existing MCP setups from other clients into Codex quickly and avoid the common timeout pitfalls.

## Known Issues and Limitations

### HTTP Transport Bug

**Issue**: As of January 2025, Codex has a critical bug with HTTP transport type. Even when properly configured with `type = "http"` and `url`, Codex incorrectly requires a `command` field and then attempts to execute it as a subprocess instead of connecting to the HTTP endpoint.

**Symptoms**:
- Error: `missing field 'command'` for HTTP servers
- Error: `No such file or directory (os error 2)` when adding dummy command
- MCP client fails to start for HTTP-only services

**Affected Services**:
- context7 (HTTP-only API service)
- Any MCP server that only provides HTTP transport

### Workarounds

#### Option 1: Disable HTTP-only servers
Comment out HTTP servers until the bug is fixed:

```toml
# Context7 disabled due to codex HTTP transport bug
# [mcp_servers.context7]
# type = "http"
# url = "https://mcp.context7.com/mcp"
# [mcp_servers.context7.headers]
# CONTEXT7_API_KEY = "ctx7sk-..."
```

#### Option 2: Use alternative clients
HTTP transport works correctly in:
- Claude Desktop (`~/.claude.json`)
- Cursor IDE (built-in MCP support)
- Gemini (`~/.gemini/settings.json`)

#### Option 3: Use stdio wrappers (Recommended)
Many HTTP services have community-created stdio wrappers on npm. For example, Context7 can be used via `@upstash/context7-mcp`:

```toml
[mcp_servers.context7]
type = "stdio"
command = "npx"
args = ["-y", "@upstash/context7-mcp", "--api-key", "YOUR_API_KEY"]
```

This approach bypasses the HTTP bug entirely by using a stdio wrapper that handles the HTTP communication internally.

To find wrappers for other services:
```bash
npm search <service-name> mcp stdio
```

## Troubleshooting Guide

### "missing field 'command'" for HTTP servers
This is the HTTP transport bug. The server is correctly configured but codex incorrectly validates it as stdio. See workarounds above.

### "No such file or directory" after adding dummy command
Adding `command = ""` or any placeholder makes codex try to execute it. Don't add dummy fields to work around the validation error.

### "failed to start" with timeout
Common causes:
1. **Wrong transport type**: HTTP servers need `url`, stdio servers need `command`
2. **Missing executable**: For stdio, ensure the command exists (`which <command>`)
3. **Interactive prompts**: Add `-y` flag to npm/npx commands
4. **Wrong package name**: Verify the exact package name from npm or the service docs

### Server starts but doesn't work
Check:
1. **API keys**: Ensure they're in the right section (headers for HTTP, env for stdio)
2. **URL format**: HTTP URLs must be complete (`https://...`)
3. **Version conflicts**: Some servers require specific Node/Python versions

### Testing configurations
Before reporting issues:
1. Test the same config in Claude Desktop to verify it's codex-specific
2. Run the stdio command manually to check for errors:
   ```bash
   CONTEXT7_API_KEY=xxx npx -y @some/package
   ```
3. Check codex logs for detailed error messages
