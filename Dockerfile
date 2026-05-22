FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY part1_tree.py .
COPY part2_fetch.py .
COPY part3_verify.py .
COPY main.py .
COPY tests/ ./tests/

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
