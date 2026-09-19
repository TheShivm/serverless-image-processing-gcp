from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]


def archive_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_packaging_is_deterministic_and_uses_only_function_source() -> None:
    command = [sys.executable, str(ROOT / "scripts" / "package.py")]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    resize_archive = ROOT / ".build" / "resize.zip"
    notification_archive = ROOT / ".build" / "notification.zip"
    first_hashes = (archive_digest(resize_archive), archive_digest(notification_archive))

    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    assert first_hashes == (archive_digest(resize_archive), archive_digest(notification_archive))

    with ZipFile(resize_archive) as archive:
        assert archive.namelist() == ["events.py", "main.py", "processing.py", "requirements.txt"]
    with ZipFile(notification_archive) as archive:
        assert archive.namelist() == ["main.py", "requirements.txt"]

    manifest = json.loads((ROOT / ".build" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["packages"]["resize"]["sha256"] == first_hashes[0]
