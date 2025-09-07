FROM python:3.11-slim


LABEL maintainer="Dat Huynh <datthuynh30102002@gmail.com>"
LABEL app="Crud-Fastapi"


WORKDIR /app


COPY ./requirements.txt ./requirements.txt


RUN pip install --no-cache-dir --upgrade -r ./requirements.txt


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
