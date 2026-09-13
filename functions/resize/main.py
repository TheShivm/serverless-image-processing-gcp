"""Pub/Sub-triggered Cloud Function that resizes a Cloud Storage image."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import functions_framework
from events import EventValidationError, StorageObjectEvent, parse_storage_event
from google.cloud import pubsub_v1, storage
from processing import resize_image


class ConfigurationError(ValueError):
    """Raised when the function environment is incomplete."""


@dataclass(frozen=True)
class Settings:
    output_bucket: str
    project_id: str
    success_topic_name: str
    publish_timeout_seconds: int

    @classmethod
    def from_environment(cls) -> Settings:
        values = {
            "output_bucket": os.getenv("OUTPUT_BUCKET", ""),
            "project_id": os.getenv("PROJECT_ID", ""),
            "success_topic_name": os.getenv("SUCCESS_TOPIC_NAME", ""),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            names = ", ".join(missing)
            raise ConfigurationError(f"Missing required environment variables: {names}")

        try:
            timeout = int(os.getenv("PUBLISH_TIMEOUT_SECONDS", "30"))
        except ValueError as exc:
            raise ConfigurationError("PUBLISH_TIMEOUT_SECONDS must be an integer.") from exc
        if timeout < 1 or timeout > 55:
            raise ConfigurationError("PUBLISH_TIMEOUT_SECONDS must be between 1 and 55.")

        return cls(publish_timeout_seconds=timeout, **values)


def emit(event: str, **fields: Any) -> None:
    """Emit a JSON object per line for Cloud Run / Cloud Logging collection."""

    print(json.dumps({"event": event, **fields}, sort_keys=True), flush=True)


def _download_object(
    storage_client: storage.Client,
    event: StorageObjectEvent,
    destination: Path,
) -> None:
    blob = storage_client.bucket(event.bucket).blob(event.name)
    kwargs = {"if_generation_match": event.generation} if event.generation else {}
    blob.download_to_filename(str(destination), **kwargs)


def process_event(
    event: StorageObjectEvent,
    settings: Settings,
    storage_client: storage.Client,
    publisher_client: pubsub_v1.PublisherClient,
) -> tuple[int, int]:
    """Perform the ordered download, transform, upload, and completion publication."""

    with TemporaryDirectory(prefix="image-resize-") as temporary_directory:
        temporary_path = Path(temporary_directory)
        filename = Path(event.name).name
        download_path = temporary_path / filename
        upload_path = temporary_path / f"RESIZED-{filename}"

        emit(
            "IMAGE_RESIZE_STARTED",
            bucket=event.bucket,
            object=event.name,
            generation=event.generation,
            event_id=event.event_id,
        )
        _download_object(storage_client, event, download_path)
        dimensions = resize_image(download_path, upload_path)

        output_blob = storage_client.bucket(settings.output_bucket).blob(event.name)
        output_blob.upload_from_filename(str(upload_path))
        emit(
            "IMAGE_RESIZE_OUTPUT_UPLOADED",
            bucket=settings.output_bucket,
            object=event.name,
            generation=event.generation,
            width=dimensions[0],
            height=dimensions[1],
            event_id=event.event_id,
        )

        topic_path = publisher_client.topic_path(settings.project_id, settings.success_topic_name)
        message = {
            "bucket": settings.output_bucket,
            "object": event.name,
            "generation": event.generation,
            "event_id": event.event_id,
            "status": "SUCCESS",
            "message": "Image resized successfully",
            "function": "image-resizing-function",
            "width": dimensions[0],
            "height": dimensions[1],
        }
        encoded_message = json.dumps(message, sort_keys=True).encode("utf-8")
        future = publisher_client.publish(topic_path, encoded_message)
        future.result(timeout=settings.publish_timeout_seconds)
        emit("IMAGE_RESIZE_COMPLETED", **message)
        return dimensions


@functions_framework.cloud_event
def handler(cloud_event: Any) -> None:
    """Validate a CloudEvent before any side effects, then resize the named object."""

    try:
        event = parse_storage_event(cloud_event)
        settings = Settings.from_environment()
    except (ConfigurationError, EventValidationError) as exc:
        emit("IMAGE_RESIZE_REJECTED", error=str(exc))
        raise

    try:
        process_event(event, settings, storage.Client(), pubsub_v1.PublisherClient())
    except Exception as exc:
        emit(
            "IMAGE_RESIZE_FAILED",
            bucket=event.bucket,
            object=event.name,
            generation=event.generation,
            event_id=event.event_id,
            error=str(exc),
        )
        raise
