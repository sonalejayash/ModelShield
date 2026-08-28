FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 modelshield
WORKDIR /app

COPY pyproject.toml README.md ./
COPY api/ api/
COPY controller/ controller/
COPY model/ model/
COPY policy/ policy/
COPY quality/ quality/
COPY security/ security/

RUN pip install --no-cache-dir --disable-pip-version-check . \
    && chown -R modelshield:modelshield /app

USER 10001
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]