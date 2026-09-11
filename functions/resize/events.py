"""CloudEvent parsing for the resize function."""

from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

SOURCE_ARTIFACT_PREFIX = "_function-source/"


class EventValidationError(ValueError):
    """Raised when a CloudEvent cannot safely identify an input object."""


@dataclass(frozen=True)
class StorageObjectEvent:
    bucket: str
    name: str
    generation: int | None
    event_id: str | None


def _required_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EventValidationError(f"Event field '{field}' must be a non-empty string.")
    return value


def _optional_generation(payload: Mapping[str, Any]) -> int | None:
    value = payload.get("generation")
    if value is None or value == "":
        return None
    try:
        generation = int(value)
    except (TypeError, ValueError) as exc:
        raise EventValidationError("Event field 'generation' must be an integer.") from exc
    if generation < 1:
        raise EventValidationError("Event field 'generation' must be positive.")
    return generation


def _event_id(cloud_event: Any) -> str | None:
    attributes = getattr(cloud_event, "_attributes", None)
    if isinstance(attributes, Mapping):
        value = attributes.get("id")
        if value:
            return str(value)

    get = getattr(cloud_event, "get", None)
    if callable(get):
        value = get("id")
        if value:
            return str(value)
    return None


def _decode_pubsub_message(event_data: Mapping[str, Any]) -> Mapping[str, Any]:
    message = event_data.get("message")
    if not isinstance(message, Mapping):
        raise EventValidationError("Pub/Sub event is missing its message envelope.")

    encoded_data = message.get("data")
    if not isinstance(encoded_data, str) or not encoded_data:
        raise EventValidationError("Pub/Sub message is missing base64 data.")

    try:
        decoded = base64.b64decode(encoded_data, validate=True)
        payload = json.loads(decoded.decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EventValidationError("Pub/Sub message data is not valid UTF-8 JSON.") from exc

    if not isinstance(payload, Mapping):
        raise EventValidationError("Pub/Sub message JSON must be an object.")
    return payload


def parse_storage_event(cloud_event: Any) -> StorageObjectEvent:
    """Return a validated storage object from Pub/Sub or direct Storage event data."""

    event_data = getattr(cloud_event, "data", None)
    if not isinstance(event_data, Mapping):
        raise EventValidationError("CloudEvent data must be an object.")

    payload = _decode_pubsub_message(event_data) if "message" in event_data else event_data
    bucket = _required_text(payload, "bucket")
    name = _required_text(payload, "name")
    if name == SOURCE_ARTIFACT_PREFIX.rstrip("/") or name.startswith(SOURCE_ARTIFACT_PREFIX):
        raise EventValidationError("Reserved function-source paths cannot be processed as images.")

    return StorageObjectEvent(
        bucket=bucket,
        name=name,
        generation=_optional_generation(payload),
        event_id=_event_id(cloud_event),
    )
