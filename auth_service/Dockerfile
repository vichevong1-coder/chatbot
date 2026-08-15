# auth_service — port 8002.
#
# NOTE: this Dockerfile expects the **repo root** as the build context so it can copy
# the monorepo `dal/` package (not on PyPI). The root docker-compose.yml may need its
# auth_service build stanza adjusted accordingly, e.g.
#   build:
#     context: .
#     dockerfile: auth_service/Dockerfile
# (docker-compose.yml is deliberately not modified by this task.)

FROM python:3.12-slim

WORKDIR /srv

COPY dal ./dal
COPY auth_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir ./dal -r requirements.txt

COPY auth_service/app ./app
COPY auth_service/scripts ./scripts

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
