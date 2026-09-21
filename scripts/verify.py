#!/usr/bin/env python3
"""Opt-in live verification for the deployed image-resize pipeline.

The script changes only the configured input bucket by uploading unique test
objects. It never alters IAM, Terraform state, or cloud resources.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Fixture:
    name: str
    image_format: str
    dimensions: tuple[int, int]

    @property
    def expected_dimensions(self) -> tuple[int, int]:
        return (max(1, self.dimensions[0] // 2), max(1, self.dimensions[1] // 2))


FIXTURES = (
    Fixture("sample-landscape.jpg", "JPEG", (1600, 1000)),
    Fixture("odd-dimensions.png", "PNG", (641, 481)),
    Fixture("tiny.png", "PNG", (1, 1)),
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def run(*command: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if check and result.returncode:
        rendered = " ".join(command)
        raise RuntimeError(f"Command failed ({result.returncode}): {rendered}\n{result.stderr}")
    return result


def terraform_outputs(terraform_directory: Path) -> dict[str, Any]:
    result = run("terraform", f"-chdir={terraform_directory}", "output", "-json")
    raw = json.loads(result.stdout)
    return {name: value["value"] for name, value in raw.items()}


def gcloud_json(*arguments: str) -> Any:
    result = run("gcloud", *arguments, "--format=json")
    return json.loads(result.stdout or "null")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_fixture(path: Path, fixture: Fixture) -> None:
    color = (35, 99, 235) if fixture.image_format == "JPEG" else (16, 185, 129, 255)
    mode = "RGB" if fixture.image_format == "JPEG" else "RGBA"
    image = Image.new(mode, fixture.dimensions, color=color)
    image.save(path, format=fixture.image_format)


def wait_for(
    description: str, predicate: Callable[[], Any], timeout_seconds: int, interval_seconds: int = 5
) -> Any:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            value = predicate()
            if value:
                return value
        except Exception as exc:  # transient control-plane/data-plane response
            last_error = exc
        time.sleep(interval_seconds)
    detail = f" Last transient error: {last_error}" if last_error else ""
    raise TimeoutError(f"Timed out waiting for {description}.{detail}")


def object_metadata(project_id: str, bucket: str, object_name: str) -> dict[str, Any] | None:
    result = run(
        "gcloud",
        "storage",
        "objects",
        "describe",
        f"gs://{bucket}/{object_name}",
        f"--project={project_id}",
        "--format=json",
        check=False,
    )
    return json.loads(result.stdout) if result.returncode == 0 else None


def notification_exists(project_id: str, function_name: str, object_name: str) -> bool:
    escaped_object = object_name.replace('"', '\\"')
    query = " AND ".join(
        [
            'resource.type="cloud_run_revision"',
            f'resource.labels.service_name="{function_name}"',
            'jsonPayload.event="IMAGE_RESIZE_NOTIFICATION"',
            'jsonPayload.status="SUCCESS"',
            f'jsonPayload.object="{escaped_object}"',
        ]
    )
    entries = gcloud_json(
        "logging",
        "read",
        query,
        f"--project={project_id}",
        "--freshness=1h",
        "--limit=20",
    )
    return bool(entries)


def upload(project_id: str, source: Path, bucket: str, object_name: str) -> dict[str, Any]:
    run(
        "gcloud",
        "storage",
        "cp",
        str(source),
        f"gs://{bucket}/{object_name}",
        f"--project={project_id}",
    )
    metadata = object_metadata(project_id, bucket, object_name)
    if metadata is None:
        raise RuntimeError("Uploaded input object could not be described.")
    return metadata


def verify_fixture(
    fixture: Fixture,
    run_directory: Path,
    outputs: dict[str, Any],
    run_id: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    project_id = outputs["project_id"]
    input_bucket = outputs["input_bucket_name"]
    output_bucket = outputs["output_bucket_name"]
    notification_function = outputs["notification_function_name"]
    object_name = f"demo/{run_id}/{fixture.name}"
    source = run_directory / "input" / fixture.name
    source.parent.mkdir(parents=True, exist_ok=True)
    create_fixture(source, fixture)

    input_metadata = upload(project_id, source, input_bucket, object_name)

    output_metadata = wait_for(
        f"resized object {object_name}",
        lambda: object_metadata(project_id, output_bucket, object_name),
        timeout_seconds,
    )
    output_file = run_directory / "output" / fixture.name
    output_file.parent.mkdir(parents=True, exist_ok=True)
    run(
        "gcloud",
        "storage",
        "cp",
        f"gs://{output_bucket}/{object_name}",
        str(output_file),
        f"--project={project_id}",
    )
    with Image.open(output_file) as output_image:
        actual_dimensions = output_image.size
    if actual_dimensions != fixture.expected_dimensions:
        raise AssertionError(
            f"{fixture.name}: expected {fixture.expected_dimensions}, got {actual_dimensions}."
        )

    wait_for(
        f"notification log for {object_name}",
        lambda: notification_exists(project_id, notification_function, object_name),
        timeout_seconds,
    )
    return {
        "fixture": asdict(fixture),
        "object": object_name,
        "input_generation": input_metadata.get("generation"),
        "output_generation": output_metadata.get("generation"),
        "source_sha256": sha256(source),
        "output_sha256": sha256(output_file),
        "actual_dimensions": actual_dimensions,
        "notification_observed": True,
        "status": "PASS",
    }


def verify_invalid_input(
    run_directory: Path,
    outputs: dict[str, Any],
    run_id: str,
    observation_seconds: int,
) -> dict[str, Any]:
    project_id = outputs["project_id"]
    input_bucket = outputs["input_bucket_name"]
    output_bucket = outputs["output_bucket_name"]
    notification_function = outputs["notification_function_name"]
    object_name = f"demo/{run_id}/invalid-input.bin"
    source = run_directory / "input" / "invalid-input.bin"
    source.write_bytes(b"this is intentionally not an image")
    upload(project_id, source, input_bucket, object_name)

    deadline = time.monotonic() + observation_seconds
    while time.monotonic() < deadline:
        if object_metadata(project_id, output_bucket, object_name):
            raise AssertionError("Invalid input produced an output object.")
        if notification_exists(project_id, notification_function, object_name):
            raise AssertionError("Invalid input produced a SUCCESS notification.")
        time.sleep(5)

    return {
        "object": object_name,
        "observation_seconds": observation_seconds,
        "output_observed": False,
        "success_notification_observed": False,
        "status": "PASS",
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terraform-dir", type=Path, default=ROOT / "infra" / "terraform")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--invalid-observation-seconds", type=int, default=90)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run_directory = arguments.output or ROOT / ".local" / "evidence" / run_id
    run_directory.mkdir(parents=True, exist_ok=False)
    results: dict[str, Any] = {
        "run_id": run_id,
        "started_at": utc_now(),
        "terraform_directory": str(arguments.terraform_dir),
        "cases": [],
        "status": "INCOMPLETE",
    }

    try:
        outputs = terraform_outputs(arguments.terraform_dir)
        results["terraform_outputs"] = outputs
        manifest = ROOT / ".build" / "manifest.json"
        if manifest.exists():
            results["package_manifest"] = json.loads(manifest.read_text(encoding="utf-8"))
            shutil.copy2(manifest, run_directory / "package-manifest.json")
        for fixture in FIXTURES:
            results["cases"].append(
                verify_fixture(fixture, run_directory, outputs, run_id, arguments.timeout_seconds)
            )
        results["cases"].append(
            verify_invalid_input(
                run_directory,
                outputs,
                run_id,
                arguments.invalid_observation_seconds,
            )
        )
        results["status"] = "PASS"
    except Exception as exc:
        results["error"] = str(exc)
        print(f"Verification failed: {exc}", file=sys.stderr)
    finally:
        results["finished_at"] = utc_now()
        (run_directory / "verification.json").write_text(
            json.dumps(results, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
        )
        (run_directory / "summary.txt").write_text(
            f"run_id: {run_id}\nstatus: {results['status']}\nstarted_at: {results['started_at']}\n"
            f"finished_at: {results['finished_at']}\n",
            encoding="utf-8",
        )

    print(json.dumps(results, indent=2, sort_keys=True, default=str))
    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
