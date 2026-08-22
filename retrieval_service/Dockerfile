FROM python:3.12-slim

WORKDIR /app

COPY dal /srv/dal
RUN pip install --no-cache-dir /srv/dal

COPY retrieval_service/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY retrieval_service/app app

EXPOSE 9007
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9007"]
