from __future__ import annotations

from pathlib import Path

from functions_framework import create_app

ROOT = Path(__file__).resolve().parents[2]
HEADERS = {
    "ce-specversion": "1.0",
    "ce-id": "invalid-event",
    "ce-source": "//storage.googleapis.com/projects/_/buckets/input",
    "ce-type": "google.cloud.pubsub.topic.v1.messagePublished",
}


def test_resize_function_framework_reports_invalid_event_failure() -> None:
    app = create_app("handler", str(ROOT / "functions" / "resize" / "main.py"), "cloudevent")

    response = app.test_client().post("/", json={"bucket": "input"}, headers=HEADERS)

    assert response.status_code >= 400


def test_notification_function_framework_reports_invalid_event_failure() -> None:
    app = create_app("handler", str(ROOT / "functions" / "notification" / "main.py"), "cloudevent")

    response = app.test_client().post("/", json={"message": {}}, headers=HEADERS)

    assert response.status_code >= 400
