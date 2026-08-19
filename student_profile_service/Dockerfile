# student_profile_service — port 9008.
#
# NOTE: this Dockerfile expects the **repo root** as the build context so it can copy
# the monorepo `dal/` package. The root docker-compose.yml must be adjusted to match.

FROM python:3.12-slim

WORKDIR /srv

COPY dal ./dal
COPY student_profile_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir ./dal -r requirements.txt

COPY student_profile_service/app ./app

EXPOSE 9008

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9008"]
