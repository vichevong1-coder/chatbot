FROM python:3.12-slim

WORKDIR /app

COPY dal /srv/dal
RUN pip install --no-cache-dir /srv/dal

COPY stt_service/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY stt_service/app app

EXPOSE 9009
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9009"]
