import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from mcp.server.fastmcp import Context, FastMCP

from todoist_mcp.api_client import (
    TodoistAPIError,
    create_client,
    todoist_get,
    todoist_post,
)


@dataclass
class AppContext:
    client: httpx.AsyncClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    client = create_client()
    try:
        yield AppContext(client=client)
    finally:
        await client.aclose()


mcp = FastMCP("todoist", lifespan=app_lifespan)


def _client(ctx) -> httpx.AsyncClient:
    return ctx.request_context.lifespan_context.client


def _json(data) -> str:
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Tool 1: List projects
# ---------------------------------------------------------------------------
@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def todoist_list_projects(ctx: Context) -> str:
    """List all projects in your Todoist account."""
    try:
        result = await todoist_get(_client(ctx), "/projects")
        return _json(result)
    except TodoistAPIError as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 2: Get tasks (with optional filters)
# ---------------------------------------------------------------------------
@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def todoist_get_tasks(
    ctx: Context,
    project_id: str | None = None,
    filter: str | None = None,
    label: str | None = None,
) -> str:
    """Get active tasks from Todoist.

    Args:
        project_id: Filter by project ID.
        filter: Todoist filter query (e.g. "today", "overdue", "p1", "#Work").
        label: Filter by label name.
    """
    try:
        params = {}
        if project_id:
            params["project_id"] = project_id
        if filter:
            params["filter"] = filter
        if label:
            params["label"] = label
        result = await todoist_get(_client(ctx), "/tasks", params or None)
        return _json(result)
    except TodoistAPIError as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 3: Get a single task by ID
# ---------------------------------------------------------------------------
@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def todoist_get_task(ctx: Context, task_id: str) -> str:
    """Get a single task by its ID.

    Args:
        task_id: The task ID.
    """
    try:
        result = await todoist_get(_client(ctx), f"/tasks/{task_id}")
        return _json(result)
    except TodoistAPIError as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 4: Create a task
# ---------------------------------------------------------------------------
@mcp.tool(
    annotations={
        "destructiveHint": False,
        "openWorldHint": True,
    }
)
async def todoist_create_task(
    ctx: Context,
    content: str,
    description: str | None = None,
    project_id: str | None = None,
    section_id: str | None = None,
    parent_id: str | None = None,
    label_ids: list[str] | None = None,
    priority: int | None = None,
    due_string: str | None = None,
    due_date: str | None = None,
    due_datetime: str | None = None,
) -> str:
    """Create a new task in Todoist.

    Args:
        content: Task title (required).
        description: Task description/notes.
        project_id: Project to add the task to (defaults to Inbox).
        section_id: Section within a project.
        parent_id: Parent task ID to create a subtask.
        label_ids: List of label IDs to apply (use todoist_get_labels to find IDs).
        priority: Priority 1 (normal) to 4 (urgent). Note: API values are inverted from the UI.
        due_string: Natural language due date (e.g. "tomorrow", "every monday").
        due_date: Due date in YYYY-MM-DD format.
        due_datetime: Due datetime in RFC3339 format (e.g. "2024-01-15T09:00:00Z").
    """
    try:
        body: dict = {"content": content}
        if description is not None:
            body["description"] = description
        if project_id is not None:
            body["project_id"] = project_id
        if section_id is not None:
            body["section_id"] = section_id
        if parent_id is not None:
            body["parent_id"] = parent_id
        if label_ids is not None:
            body["label_ids"] = label_ids
        if priority is not None:
            body["priority"] = priority
        if due_string is not None:
            body["due_string"] = due_string
        if due_date is not None:
            body["due_date"] = due_date
        if due_datetime is not None:
            body["due_datetime"] = due_datetime
        result = await todoist_post(_client(ctx), "/tasks", body)
        return _json(result)
    except TodoistAPIError as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 5: Update a task
# ---------------------------------------------------------------------------
@mcp.tool(
    annotations={
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def todoist_update_task(
    ctx: Context,
    task_id: str,
    content: str | None = None,
    description: str | None = None,
    label_ids: list[str] | None = None,
    priority: int | None = None,
    due_string: str | None = None,
    due_date: str | None = None,
    due_datetime: str | None = None,
) -> str:
    """Update an existing task.

    Args:
        task_id: The task ID to update.
        content: New task title.
        description: New description.
        label_ids: New label IDs (replaces existing labels; use todoist_get_labels to find IDs).
        priority: Priority 1 (normal) to 4 (urgent).
        due_string: Natural language due date.
        due_date: Due date in YYYY-MM-DD format.
        due_datetime: Due datetime in RFC3339 format.
    """
    try:
        body: dict = {}
        if content is not None:
            body["content"] = content
        if description is not None:
            body["description"] = description
        if label_ids is not None:
            body["label_ids"] = label_ids
        if priority is not None:
            body["priority"] = priority
        if due_string is not None:
            body["due_string"] = due_string
        if due_date is not None:
            body["due_date"] = due_date
        if due_datetime is not None:
            body["due_datetime"] = due_datetime
        result = await todoist_post(_client(ctx), f"/tasks/{task_id}", body)
        return _json(result)
    except TodoistAPIError as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 6: Complete a task
# ---------------------------------------------------------------------------
@mcp.tool(
    annotations={
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def todoist_complete_task(ctx: Context, task_id: str) -> str:
    """Mark a task as complete.

    Args:
        task_id: The task ID to complete.
    """
    try:
        await todoist_post(_client(ctx), f"/tasks/{task_id}/close")
        return _json({"success": True, "task_id": task_id, "action": "completed"})
    except TodoistAPIError as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 7: Reopen a task
# ---------------------------------------------------------------------------
@mcp.tool(
    annotations={
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def todoist_reopen_task(ctx: Context, task_id: str) -> str:
    """Reopen a previously completed task.

    Args:
        task_id: The task ID to reopen.
    """
    try:
        await todoist_post(_client(ctx), f"/tasks/{task_id}/reopen")
        return _json({"success": True, "task_id": task_id, "action": "reopened"})
    except TodoistAPIError as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 8: List labels
# ---------------------------------------------------------------------------
@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def todoist_get_labels(ctx: Context) -> str:
    """List all personal labels in your Todoist account."""
    try:
        result = await todoist_get(_client(ctx), "/labels")
        return _json(result)
    except TodoistAPIError as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 9: Get sections
# ---------------------------------------------------------------------------
@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def todoist_get_sections(ctx: Context, project_id: str | None = None) -> str:
    """List sections, optionally filtered by project.

    Args:
        project_id: Filter sections by project ID.
    """
    try:
        params = {}
        if project_id:
            params["project_id"] = project_id
        result = await todoist_get(_client(ctx), "/sections", params or None)
        return _json(result)
    except TodoistAPIError as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
