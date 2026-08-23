"""Task flow request logging middleware for gateway."""

from __future__ import annotations

import logging
import sys
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("tunsay.gateway")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [GATEWAY] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Logs incoming user request entry, student identity, and task flow completion latency."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip noisy health probes
        if request.url.path == "/health":
            return await call_next(request)

        started = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        student_id = getattr(request.state, "student_id", None) or "anonymous"

        sys.stderr.write(
            f"INFO:     [GATEWAY INBOUND] ---> {request.method} {request.url.path} | Student: {student_id} | IP: {client_ip}\n"
        )
        sys.stderr.flush()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - started) * 1000
            sys.stderr.write(
                f"INFO:     [GATEWAY OUTBOUND] <--- {request.method} {request.url.path} | Status: {response.status_code} | Student: {student_id} | Latency: {duration_ms:.2f}ms\n"
            )
            sys.stderr.flush()
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - started) * 1000
            sys.stderr.write(
                f"ERROR:    [GATEWAY ERROR] <--- {request.method} {request.url.path} | Exception: {type(exc).__name__} | Latency: {duration_ms:.2f}ms\n"
            )
            sys.stderr.flush()
            raise
