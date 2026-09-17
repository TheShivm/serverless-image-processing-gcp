from __future__ import annotations

import base64
import json

import pytest
from events import EventValidationError, parse_storage_event


class CloudEvent:
    def __init__(self, data: object, event_id: str = "event-123") -> None:
        self.data = data
        self._attributes = {"id": event_id}


def pubsub_event(payload: object) -> CloudEvent:
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    return CloudEvent({"message": {"data": encoded}})


def test_parses_pubsub_storage_notification_with_generation() -> None:
    event = parse_storage_event(
        pubsub_event({"bucket": "input", "name": "demo/photo.png", "generation": "42"})
    )

    assert event.bucket == "input"
    assert event.name == "demo/photo.png"
    assert event.generation == 42
    assert event.event_id == "event-123"


def test_retains_direct_storage_event_fallback() -> None:
    event = parse_storage_event(CloudEvent({"bucket": "input", "name": "photo.jpg"}))

    assert event.bucket == "input"
    assert event.name == "photo.jpg"
    assert event.generation is None


@pytest.mark.parametrize(
    "event",
    [
        CloudEvent({"message": {"data": "not base64"}}),
        CloudEvent({"message": {"data": base64.b64encode(b"not json").decode("ascii")}}),
        pubsub_event({"bucket": "input"}),
        pubsub_event({"bucket": "input", "name": "_function-source/resize.zip"}),
    ],
)
def test_rejects_invalid_or_reserved_events(event: CloudEvent) -> None:
    with pytest.raises(EventValidationError):
        parse_storage_event(event)
