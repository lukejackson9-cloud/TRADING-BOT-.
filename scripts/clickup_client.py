"""
ClickUp API client — posts the daily report as a comment on a fixed task.
Docs: https://developer.clickup.com/

Requires env var: CLICKUP_API_TOKEN
Requires /config/settings.json to have "clickup_task_id" set.
Install: pip install requests --break-system-packages
"""

import os
import json
import requests

API_TOKEN = os.environ["CLICKUP_API_TOKEN"]
BASE_URL = "https://api.clickup.com/api/v2"


def _get_task_id():
    with open("/config/settings.json") as f:
        settings = json.load(f)
    task_id = settings.get("clickup_task_id")
    if not task_id:
        raise ValueError("Set clickup_task_id in /config/settings.json first")
    return task_id


def post_report(summary: str):
    """Post the daily summary as a comment on the configured ClickUp task."""
    task_id = _get_task_id()
    resp = requests.post(
        f"{BASE_URL}/task/{task_id}/comment",
        headers={"Authorization": API_TOKEN, "Content-Type": "application/json"},
        json={"comment_text": summary},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    print(post_report("Test report from trading agent."))
