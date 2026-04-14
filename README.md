# Todoist MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that lets Claude (or any MCP-compatible client) read and write your Todoist tasks through natural conversation.

Runs locally on your machine over stdio — your API token never leaves your computer. Backed by the [Todoist REST API v1](https://developer.todoist.com/api/v1/).

## What you can ask Claude

Once installed, just talk to Claude naturally:

- *"What's on my plate today?"* — fetches tasks due today
- *"Add a task to buy groceries tomorrow with high priority"* — creates a task with a due date and priority
- *"Show me everything in my Work project"* — lists tasks filtered by project
- *"Mark 'Send invoice' as done"* — completes a task
- *"Move that task to next Monday and add the @waiting label"* — updates due date and labels
- *"What projects do I have?"* — lists all your projects
- *"Reopen the task I just completed, I wasn't done"* — reopens a completed task

## Tools exposed to the MCP client

| Tool | What it does |
|------|--------------|
| `todoist_list_projects` | List all your projects |
| `todoist_get_tasks` | Get tasks with optional filters (project, label, or Todoist filter query) |
| `todoist_get_task` | Get full details of a single task |
| `todoist_create_task` | Create a task with title, description, due date, priority, labels, and more |
| `todoist_update_task` | Modify any field on an existing task |
| `todoist_complete_task` | Mark a task as done |
| `todoist_reopen_task` | Reopen a previously completed task |
| `todoist_get_labels` | List all your personal labels |
| `todoist_get_sections` | List sections within a project |

Each tool is annotated with MCP hints (`readOnlyHint`, `destructiveHint`, `idempotentHint`) so clients can reason about what's safe to call without confirmation.

## Prerequisites

- **Python 3.10+**
- A **Todoist account** (free or Pro)
- **Claude Desktop**, **Claude Code**, or any other MCP-compatible client

## Getting your API token

1. Open [Todoist Settings → Integrations → Developer](https://todoist.com/prefs/integrations)
2. Copy your **API token**

Keep this token private — it grants full read/write access to your Todoist account.

## Installation

```bash
git clone https://github.com/lucasgfsvd/todoist-mcp.git
cd todoist-mcp
pip install .
```

Or with [`uv`](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/lucasgfsvd/todoist-mcp.git
cd todoist-mcp
uv pip install .
```

After install, you can delete the clone if you want — the package is in your site-packages and the `todoist-mcp` entry-point script is on your PATH (inside Python's Scripts directory).

The only runtime dependency is `mcp>=1.26.0`, which brings its own transitive dependencies (httpx, pydantic, etc.).

## Configuration

### Claude Desktop

Config file location:

| OS | Path |
|----|------|
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

Add an entry under `mcpServers`:

```json
{
  "mcpServers": {
    "todoist": {
      "command": "todoist-mcp",
      "args": [],
      "env": {
        "TODOIST_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

If `todoist-mcp` isn't on Claude Desktop's PATH (common on Windows, where user-site Scripts aren't exported), use the absolute path to the script — e.g. `C:\Users\<you>\AppData\Roaming\Python\Python311\Scripts\todoist-mcp.exe` — or fall back to invoking the module:

```json
{
  "mcpServers": {
    "todoist": {
      "command": "python",
      "args": ["-m", "todoist_mcp"],
      "env": {
        "TODOIST_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

Then restart Claude Desktop. The Todoist tools will be available in every conversation.

### Claude Desktop with `uv` (no global install needed)

Point `uv` at the repo directory and let it run the package in an ephemeral environment:

```json
{
  "mcpServers": {
    "todoist": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/todoist-mcp", "todoist-mcp"],
      "env": {
        "TODOIST_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add todoist -- todoist-mcp
```

Then either export the token in your shell before launching:

```bash
export TODOIST_API_TOKEN="your-token-here"
claude
```

…or put it in your project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "todoist": {
      "command": "todoist-mcp",
      "args": [],
      "env": {
        "TODOIST_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

## Verifying it works

Start a new conversation with Claude and ask:

> "List my Todoist projects"

Claude should call `todoist_list_projects` and show them. If not:

1. **Token check** — `curl -s -H "Authorization: Bearer YOUR_TOKEN" https://api.todoist.com/api/v1/projects`
2. **Server check** — run `todoist-mcp` in a terminal. It should start silently and wait for stdio input (Ctrl+C to exit).
3. **Client check** — restart Claude Desktop; validate your config is valid JSON (no trailing commas).

## Filter syntax reference

`todoist_get_tasks` accepts the same [Todoist filter queries](https://todoist.com/help/articles/introduction-to-filters-V98wIH) you'd type into the Todoist app:

| Filter | Returns |
|--------|---------|
| `today` | Tasks due today |
| `overdue` | Overdue tasks |
| `tomorrow` | Tasks due tomorrow |
| `next 7 days` | Tasks due in the next week |
| `p1` | Urgent priority tasks |
| `#Work` | Tasks in the "Work" project |
| `@email` | Tasks with the "email" label |
| `no date` | Tasks without a due date |
| `today \| overdue` | Combine with OR |
| `today & #Work` | Combine with AND |
| `assigned to: me` | Tasks assigned to you (shared projects) |

## Priority values — a Todoist gotcha

Todoist's API and UI use **inverted** priority numbers:

| What you mean | API value | Todoist UI label |
|---------------|-----------|------------------|
| Urgent (red) | `4` | Priority 1 |
| High (orange) | `3` | Priority 2 |
| Medium (blue) | `2` | Priority 3 |
| Normal (no color) | `1` | Priority 4 |

When talking to Claude, just say "urgent" or "high priority" — it maps the words to the right API value.

## Project layout

```
todoist-mcp/
├── todoist_mcp/
│   ├── __init__.py       # Package marker, exposes __version__
│   ├── __main__.py       # `python -m todoist_mcp` entry point
│   ├── server.py         # FastMCP server, 9 tool definitions, stdio transport
│   └── api_client.py     # httpx-based Todoist REST client with auth + error handling
├── pyproject.toml        # Build config, single runtime dep: mcp>=1.26.0
├── LICENSE               # MIT
└── README.md
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `TODOIST_API_TOKEN environment variable is not set` | Put the token in your MCP config's `env` block — exporting it in a shell does not propagate to Claude Desktop's launched subprocess. |
| `Authentication failed` (401) | Token is invalid or revoked — regenerate it in Todoist settings. |
| `Rate limited` (429) | Todoist throttles API calls — back off and retry. |
| Tools don't appear in Claude | Restart Claude Desktop; validate your `claude_desktop_config.json` is syntactically correct JSON. |
| `ModuleNotFoundError: todoist_mcp` | Re-run `pip install .` from the repo root using the same Python interpreter Claude uses. |
| `'todoist-mcp' is not recognized` | The install location isn't on Claude's PATH — use the absolute path to the script in your config, or fall back to `python -m todoist_mcp`. |

## Development

Install in editable mode so your changes take effect without re-installing:

```bash
pip install -e .
```

The server is a single-file FastMCP app. Each tool is a decorated async function in `todoist_mcp/server.py` — adding a new tool means writing one function and letting FastMCP do the schema inference. The HTTP layer lives in `todoist_mcp/api_client.py`.

To smoke-test without Claude, run it directly and speak MCP over stdio:

```bash
TODOIST_API_TOKEN=... todoist-mcp
```

## License

MIT — see [LICENSE](LICENSE).
