from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest
from events import StorageObjectEvent
from main import Settings, process_event
from PIL import Image


class InputBlob:
    def __init__(self, calls: list[object]) -> None:
        self.calls = calls

    def download_to_filename(self, destination: str, **kwargs: object) -> None:
        self.calls.append(("download", kwargs))
        Image.new("RGB", (1600, 1000), color="purple").save(destination)


class OutputBlob:
    def __init__(self, calls: list[object]) -> None:
        self.calls = calls
        self.data = b""

    def upload_from_filename(self, source: str) -> None:
        self.calls.append("upload")
        self.data = Path(source).read_bytes()


class Bucket:
    def __init__(self, name: str, input_blob: InputBlob, output_blob: OutputBlob) -> None:
        self.name = name
        self.input_blob = input_blob
        self.output_blob = output_blob

    def blob(self, _: str) -> InputBlob | OutputBlob:
        return self.input_blob if self.name == "input" else self.output_blob


class StorageClient:
    def __init__(self, calls: list[object], output_blob: OutputBlob) -> None:
        self.input_blob = InputBlob(calls)
        self.output_blob = output_blob

    def bucket(self, name: str) -> Bucket:
        return Bucket(name, self.input_blob, self.output_blob)


class Future:
    def __init__(self, calls: list[object], failure: Exception | None = None) -> None:
        self.calls = calls
        self.failure = failure

    def result(self, **kwargs: object) -> None:
        self.calls.append(("publish-result", kwargs))
        if self.failure:
            raise self.failure


class Publisher:
    def __init__(self, calls: list[object], failure: Exception | None = None) -> None:
        self.calls = calls
        self.failure = failure
        self.message: dict[str, object] | None = None

    def topic_path(self, project: str, topic: str) -> str:
        return f"projects/{project}/topics/{topic}"

    def publish(self, topic: str, message: bytes) -> Future:
        self.calls.append(("publish", topic))
        self.message = json.loads(message)
        return Future(self.calls, self.failure)


def settings() -> Settings:
    return Settings("output", "project", "success", 30)


def event() -> StorageObjectEvent:
    return StorageObjectEvent("input", "demo/photo.jpg", 7, "event-1")


def test_processes_generation_aware_event_and_awaits_publication() -> None:
    calls: list[object] = []
    output_blob = OutputBlob(calls)
    publisher = Publisher(calls)

    dimensions = process_event(event(), settings(), StorageClient(calls, output_blob), publisher)

    assert dimensions == (800, 500)
    assert calls == [
        ("download", {"if_generation_match": 7}),
        "upload",
        ("publish", "projects/project/topics/success"),
        ("publish-result", {"timeout": 30}),
    ]
    assert publisher.message is not None
    assert publisher.message["object"] == "demo/photo.jpg"
    assert publisher.message["generation"] == 7
    with Image.open(BytesIO(output_blob.data)) as image:
        assert image.size == (800, 500)


def test_surfaces_publish_failure_after_output_upload() -> None:
    calls: list[object] = []
    output_blob = OutputBlob(calls)

    with pytest.raises(RuntimeError, match="publish failed"):
        process_event(
            event(),
            settings(),
            StorageClient(calls, output_blob),
            Publisher(calls, RuntimeError("publish failed")),
        )

    assert output_blob.data
    assert "upload" in calls
    assert any(call[0] == "publish-result" for call in calls if isinstance(call, tuple))
