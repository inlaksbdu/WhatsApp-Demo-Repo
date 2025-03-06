
FROM python:3.12-slim-bullseye AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 

FROM python:3.12-slim-bullseye

WORKDIR /app

# Install WeasyPrint dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    mime-support \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/



RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p logs \
    && chown -R appuser:appuser logs \
    && chmod 755 logs

# RUN apt-get update \
#     && apt-get install -y ffmpeg \
#     && rm -rf /var/lib/apt/lists/*
# Copy application code
COPY . /app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

ENV PATH="/usr/local/bin:${PATH}"
USER appuser

EXPOSE ${PORT}

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
