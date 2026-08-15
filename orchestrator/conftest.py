"""Make `app` importable when pytest runs from the repo root."""

import sys
from pathlib import Path

SERVICE_ROOT = str(Path(__file__).resolve().parent)
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)
