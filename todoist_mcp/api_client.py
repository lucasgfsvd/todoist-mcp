import os
import uuid

import httpx

TODOIST_BASE_URL = "https://api.todoist.com/api/v1"


class TodoistAPIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Todoist API error {status_code}: {detail}")


def create_client() -> httpx.AsyncClient:
    token = os.environ.get("TODOIST_API_TOKEN")
    if not token:
        raise RuntimeError(
            "TODOIST_API_TOKEN environment variable is not set. "
            "Get your token from https://todoist.com/prefs/integrations"
        )
    return httpx.AsyncClient(
        base_url=TODOIST_BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    status = response.status_code
    messages = {
        401: "Authentication failed — check your TODOIST_API_TOKEN",
        403: "Forbidden — insufficient permissions",
        404: "Resource not found",
        410: "Endpoint deprecated — check Todoist API version",
        429: "Rate limited — too many requests, please wait",
    }
    if status in messages:
        raise TodoistAPIError(status, messages[status])
    if status >= 500:
        raise TodoistAPIError(status, "Todoist server error — try again later")
    raise TodoistAPIError(status, response.text)


async def todoist_get(
    client: httpx.AsyncClient,
    path: str,
    params: dict | None = None,
) -> list | dict:
    response = await client.get(path, params=params)
    _raise_for_status(response)
    return response.json()


async def todoist_post(
    client: httpx.AsyncClient,
    path: str,
    json_body: dict | None = None,
) -> dict:
    headers = {"X-Request-Id": str(uuid.uuid4())}
    response = await client.post(path, json=json_body, headers=headers)
    _raise_for_status(response)
    if response.status_code == 204:
        return {}
    return response.json()
