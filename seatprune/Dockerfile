FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY . /app/

RUN uv pip install --system .

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "seatprune.server"]
