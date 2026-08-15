"""Recursive JSON key case translation — the gateway's one boundary job.

Services speak ``snake_case`` on the wire; the browser speaks ``camelCase``
(.claude/claude.md section 5). The gateway is the ONLY place this translation
happens. Keys only — values are NEVER transformed, so Khmer strings pass
through byte-identical.

Pure module: no FastAPI, no I/O.
"""

from __future__ import annotations

import re
from typing import Any

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])([A-Z])")


def camel_to_snake(key: str) -> str:
    """``textKhmer`` -> ``text_khmer``. Already-snake keys pass unchanged."""
    return _CAMEL_BOUNDARY.sub(lambda m: "_" + m.group(1).lower(), key)


def snake_to_camel(key: str) -> str:
    """``text_khmer`` -> ``textKhmer``. Already-camel keys pass unchanged."""
    first, _, rest = key.partition("_")
    if not rest:
        return key
    parts = rest.split("_")
    return first + "".join(p[:1].upper() + p[1:] for p in parts)


def _translate(obj: Any, key_fn) -> Any:
    if isinstance(obj, dict):
        return {
            (key_fn(k) if isinstance(k, str) else k): _translate(v, key_fn)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_translate(item, key_fn) for item in obj]
    return obj  # scalar values untouched, always


def to_snake_keys(obj: Any) -> Any:
    """Inbound: browser camelCase -> service snake_case. Recursive, keys only."""
    return _translate(obj, camel_to_snake)


def to_camel_keys(obj: Any) -> Any:
    """Outbound: service snake_case -> browser camelCase. Recursive, keys only."""
    return _translate(obj, snake_to_camel)
