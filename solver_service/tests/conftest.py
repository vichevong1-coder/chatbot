"""Make `app` importable when pytest runs from the repo root."""

import sys
from pathlib import Path

SERVICE_ROOT = str(Path(__file__).resolve().parents[1])
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)
