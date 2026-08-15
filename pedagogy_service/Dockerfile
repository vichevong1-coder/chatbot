# pedagogy_service — the ONLY service that talks to Gemini.
#
# BUILD CONTEXT: this image needs the shared dal/ package, which lives at the repo
# root, outside this directory. Build from the REPO ROOT:
#
#   docker build -f pedagogy_service/Dockerfile -t tunsay-pedagogy .
#
# (docker-compose currently says `build: ./pedagogy_service`; it needs
#  `context: .` + `dockerfile: pedagogy_service/Dockerfile` for dal to be copyable.)

FROM python:3.12-slim

WORKDIR /srv/pedagogy_service

COPY dal /srv/dal
COPY pedagogy_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt /srv/dal

COPY pedagogy_service/app ./app

EXPOSE 8006

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
