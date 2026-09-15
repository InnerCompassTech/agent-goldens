from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "goldens" / "cases.json"


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    return json.loads((path or CASES_PATH).read_text())
