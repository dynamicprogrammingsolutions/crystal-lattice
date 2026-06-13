When the work becomes repetitive, use the same running Crystal Lattice instance from Python. Run batch drafting, evaluations, internal review tools, or data enrichment without rebuilding the harness from scratch.

This example reads LinkedIn leads from a CSV and asks a configured agent to draft a first message for each person.

```python
import csv
import time
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:9000"
AGENT_ID = "codex-openrouter"


def create_session() -> str:
    response = requests.post(
        f"{BASE_URL}/sessions",
        json={"agent_id": AGENT_ID},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["session"]["session_id"]


def send_prompt(session_id: str, prompt: str) -> str:
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/send_message",
        json={"message": {"role": "user", "content": prompt}},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["request_id"]


def wait_for_reply(session_id: str, timeout_seconds: int = 180) -> str:
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        response = requests.get(
            f"{BASE_URL}/sessions/{session_id}/messages",
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        messages = data.get("messages", [])
        assistant_messages = [
            item["message"]["content"]
            for item in messages
            if item.get("message", {}).get("role") == "assistant"
        ]

        if assistant_messages and not data.get("active_request_id"):
            return assistant_messages[-1]

        time.sleep(1)

    raise TimeoutError(f"Timed out waiting for session {session_id}")


def build_prompt(lead: dict[str, str]) -> str:
    return f"""Write a concise, friendly first LinkedIn message.

Use the lead details, avoid hype, and do not invent facts.

Name: {lead.get("name", "")}
Role: {lead.get("role", "")}
Company: {lead.get("company", "")}
Notes: {lead.get("notes", "")}
"""


with Path("leads.csv").open(newline="") as input_file, Path("messages.csv").open("w", newline="") as output_file:
    reader = csv.DictReader(input_file)
    writer = csv.DictWriter(output_file, fieldnames=["name", "company", "message"])
    writer.writeheader()

    for lead in reader:
        session_id = create_session()
        send_prompt(session_id, build_prompt(lead))
        message = wait_for_reply(session_id)

        writer.writerow(
            {
                "name": lead.get("name", ""),
                "company": lead.get("company", ""),
                "message": message,
            }
        )
```
