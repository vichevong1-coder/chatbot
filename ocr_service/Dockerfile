# ocr_service — port 9010
#
# Follows standard Python 3.12 slim pattern with dal install from repo root.

FROM python:3.12-slim

WORKDIR /srv

COPY dal ./dal
COPY ocr_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir ./dal -r requirements.txt

COPY ocr_service/app ./app

EXPOSE 9010

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9010"]
