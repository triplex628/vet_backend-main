FROM python:3.11-slim


WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

#RUN pip install --no-cache-dir uvloop==0.16.0 greenlet==1.1.2 httptools==0.2.0

RUN pip install -r requirements.txt

RUN pip install redis>=4.2.0

COPY src .

