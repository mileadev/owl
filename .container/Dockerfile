FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY owl ./owl
COPY examples ./examples
RUN python -m pip install --no-cache-dir . \
    && useradd --uid 10001 --create-home --shell /usr/sbin/nologin owl
USER 10001:10001
EXPOSE 7860
CMD ["python", "-m", "owl.webapp"]
