# orchestrator — the LangGraph brain behind POST /chat.
#
# BUILD CONTEXT: this image needs the shared dal/ package, which lives at the
# repo root, outside this directory. Build from the REPO ROOT:
#
#   docker build -f orchestrator/Dockerfile -t tunsay-orchestrator .
#
# (docker-compose must use `context: .` + `dockerfile: orchestrator/Dockerfile`
#  for dal to be copyable — same fix the other dal-dependent services need.)

FROM python:3.12-slim

WORKDIR /srv/orchestrator

COPY dal /srv/dal
COPY orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt /srv/dal

COPY orchestrator/app ./app

EXPOSE 9001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9001"]
