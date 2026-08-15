"""Tunsay shared data-access layer.

`dal` is a library, not a service. It holds the SQLAlchemy models, Pydantic schemas,
repositories and outbound clients that every Tunsay Python service imports, so that one
data model is used across the whole backend. It is installed into each service image
(`pip install -e ./dal`) and is never run or deployed on its own — it exposes no FastAPI
app, no HTTP port and no entrypoint. It imports nothing else from this repository.
"""

__version__ = "0.1.0"
