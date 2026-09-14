"""Pub/Sub-triggered completion logger for the image-resize pipeline."""

from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Mapping
from typing import Any

import functions_framework


class NotificationValidationError(ValueError):
    """Raised when a completion notification does not meet the contract."""


REQUIRED_FIELDS = ("bucket", "object", "status", "message")


def emit(event: str, **fields: Any) -> None:
    print(json.dumps({"event": event, **fields}, sort_keys=True), flush=True)


def parse_notification(cloud_event: Any) -> dict[str, Any]:
    event_data = getattr(cloud_event, "data", None)
    if not isinstance(event_data, Mapping):
        raise NotificationValidationError("CloudEvent data must be an object.")
    message = event_data.get("message")
    if not isinstance(message, Mapping) or not isinstance(message.get("data"), str):
        raise NotificationValidationError("Pub/Sub event is missing base64 message data.")

    try:
        payload = json.loads(base64.b64decode(message["data"], validate=True).decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NotificationValidationError("Pub/Sub message data is not valid UTF-8 JSON.") from exc
    if not isinstance(payload, dict):
        raise NotificationValidationError("Notification payload must be an object.")

    for field in REQUIRED_FIELDS:
        if not isinstance(payload.get(field), str) or not payload[field]:
            message = f"Notification field '{field}' must be a non-empty string."
            raise NotificationValidationError(message)
    return payload


@functions_framework.cloud_event
def handler(cloud_event: Any) -> None:
    """Write one structured completion record after validating the Pub/Sub payload."""

    try:
        message = parse_notification(cloud_event)
    except NotificationValidationError as exc:
        emit("IMAGE_RESIZE_NOTIFICATION_REJECTED", error=str(exc))
        raise

    emit("IMAGE_RESIZE_NOTIFICATION", **message)
