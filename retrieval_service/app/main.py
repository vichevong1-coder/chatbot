"""FastAPI application for retrieval_service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.core.retriever import VectorRetriever
from app.core.textbook_chunker import TextbookChunk
from app.ingest.seed_textbooks import DEFAULT_CHUNKS

SERVICE_NAME = "retrieval_service"


class RetrieveRequest(BaseModel):
    query: str
    grade: int | None = None
    subject: str | None = None
    top_k: int = Field(default=3, ge=1, le=10)


class RetrieveResponse(BaseModel):
    results: list[TextbookChunk]
    total_found: int


class IngestRequest(BaseModel):
    chunks: list[TextbookChunk]


class IngestResponse(BaseModel):
    indexed_count: int


def create_app(retriever: VectorRetriever | None = None) -> FastAPI:
    instance_retriever = retriever or VectorRetriever()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Auto-seed default curriculum chunks on startup if empty
        if not instance_retriever.chunks:
            await instance_retriever.add_chunks(DEFAULT_CHUNKS)
        yield

    app = FastAPI(title=SERVICE_NAME, lifespan=lifespan)
    app.state.retriever = instance_retriever

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": SERVICE_NAME,
            "chunks_indexed": str(len(app.state.retriever.chunks)),
        }

    @app.post("/retrieve", response_model=RetrieveResponse)
    async def retrieve(req: RetrieveRequest) -> RetrieveResponse:
        try:
            chunks = await app.state.retriever.retrieve(
                query=req.query,
                grade=req.grade,
                subject=req.subject,
                top_k=req.top_k,
            )
            return RetrieveResponse(results=chunks, total_found=len(chunks))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Retrieval error: {str(exc)}")

    @app.post("/ingest", response_model=IngestResponse)
    async def ingest(req: IngestRequest) -> IngestResponse:
        try:
            await app.state.retriever.add_chunks(req.chunks)
            return IngestResponse(indexed_count=len(req.chunks))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Ingestion error: {str(exc)}")

    return app


app = create_app()
