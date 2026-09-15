from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESIZE_DIRECTORY = ROOT / "functions" / "resize"

if str(RESIZE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(RESIZE_DIRECTORY))
