"""PIN hashing.

The filename is inherited from the service scaffold, but there is **no password** in this
product (.claude/contracts.md section 4): what gets hashed is the optional 4-digit PIN a
child sets. bcrypt is deliberate even though the input space is tiny — the hash is not the
defence (10,000 combinations cannot be), the attempt throttle in
:mod:`app.core.throttle` is. The hash only keeps PINs out of the database in plaintext.

Pure module: no FastAPI, no I/O.
"""

from __future__ import annotations

import bcrypt


def hash_pin(pin: str) -> str:
    """Return a bcrypt hash of the 4-digit PIN, as a UTF-8 string for the DB column."""
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_pin(pin: str, pin_hash: str) -> bool:
    """Constant-time check of ``pin`` against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(pin.encode("utf-8"), pin_hash.encode("utf-8"))
    except ValueError:
        # A malformed stored hash must fail closed, not raise into the request path.
        return False
