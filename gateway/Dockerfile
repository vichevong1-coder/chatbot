# gateway — port 9000, the only public surface.
#
# Unlike auth_service/orchestrator, the gateway has NO dal dependency
# (requirements.txt explains why), so a plain `build: ./gateway` context is
# fine — no repo-root context needed.

FROM python:3.12-slim

WORKDIR /srv

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 9000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
