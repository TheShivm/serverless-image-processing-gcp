from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path

import pytest

NOTIFICATION_MAIN = Path(__file__).resolve().parents[2] / "functions" / "notification" / "main.py"
spec = importlib.util.spec_from_file_location("notification_main", NOTIFICATION_MAIN)
assert spec and spec.loader
notification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notification)


class CloudEvent:
    def __init__(self, data: object) -> None:
        self.data = data


def event(payload: object) -> CloudEvent:
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    return CloudEvent({"message": {"data": encoded}})


def test_notification_emits_structured_completion_record(
    capsys: pytest.CaptureFixture[str],
) -> None:
    notification.handler(
        event(
            {
                "bucket": "output",
                "object": "demo/photo.jpg",
                "status": "SUCCESS",
                "message": "done",
            }
        )
    )

    record = json.loads(capsys.readouterr().out)
    assert record["event"] == "IMAGE_RESIZE_NOTIFICATION"
    assert record["object"] == "demo/photo.jpg"


def test_notification_rejects_missing_required_fields() -> None:
    with pytest.raises(notification.NotificationValidationError):
        notification.handler(event({"bucket": "output"}))
