FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY openswarm_builder ./openswarm_builder
COPY templates ./templates
COPY vendor ./vendor

RUN pip install --no-cache-dir .

EXPOSE 8090
CMD ["uvicorn", "openswarm_builder.adapters.http_server:app", "--host", "0.0.0.0", "--port", "8090"]
