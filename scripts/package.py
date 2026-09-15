#!/usr/bin/env python3
"""Create deterministic Cloud Function source archives from tracked source files."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIRECTORY = ROOT / ".build"
FIXED_ZIP_TIMESTAMP = (2024, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class FunctionPackage:
    name: str
    source: Path
    archive: Path


PACKAGES = (
    FunctionPackage("resize", ROOT / "functions" / "resize", BUILD_DIRECTORY / "resize.zip"),
    FunctionPackage(
        "notification",
        ROOT / "functions" / "notification",
        BUILD_DIRECTORY / "notification.zip",
    ),
)


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "uncommitted"


def package_files(source: Path) -> list[Path]:
    required = (source / "main.py", source / "requirements.txt")
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Package source is missing required files: {', '.join(missing)}")

    files = [path for path in source.rglob("*.py") if path.is_file()]
    files.append(source / "requirements.txt")
    return sorted(set(files), key=lambda path: path.relative_to(source).as_posix())


def write_archive(package: FunctionPackage) -> dict[str, object]:
    files = package_files(package.source)
    package.archive.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(package.archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for file_path in files:
            archive_name = file_path.relative_to(package.source).as_posix()
            entry = ZipInfo(archive_name, date_time=FIXED_ZIP_TIMESTAMP)
            entry.compress_type = ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(
                entry,
                file_path.read_bytes(),
                compress_type=ZIP_DEFLATED,
                compresslevel=9,
            )

    digest = hashlib.sha256(package.archive.read_bytes()).hexdigest()
    return {
        "archive": package.archive.relative_to(ROOT).as_posix(),
        "sha256": digest,
        "files": [path.relative_to(package.source).as_posix() for path in files],
    }


def build() -> dict[str, object]:
    result: dict[str, object] = {"source_commit": git_commit(), "packages": {}}
    packages = result["packages"]
    assert isinstance(packages, dict)
    for package in PACKAGES:
        packages[package.name] = write_archive(package)
    manifest = BUILD_DIRECTORY / "manifest.json"
    manifest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        result = build()
    except (OSError, ValueError) as exc:
        print(f"Packaging failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
