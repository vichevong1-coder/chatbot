# content_service — problem catalog + seeding. Internal admin CRUD is never
# published to the host (`expose:` in compose, not `ports:`).
#
# BUILD CONTEXT: this image installs the shared `dal` package from the monorepo, which
# lives OUTSIDE this directory. The build context must therefore be the REPO ROOT:
#
#     docker build -f content_service/Dockerfile .
#
# docker-compose.yml's `build: ./content_service` must become
#     build: { context: ., dockerfile: content_service/Dockerfile }
# for this service (the dal-free services can keep their local context).

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/content_service

# The shared data-access layer first — it changes less often than app code.
COPY dal /srv/dal
RUN pip install --no-cache-dir /srv/dal

COPY content_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY content_service/app ./app
COPY content_service/scripts ./scripts
COPY content_service/seed_data ./seed_data

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
