FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN pip install --no-cache-dir uv==0.9.7
COPY pyproject.toml README.md ./
COPY owl ./owl
COPY examples ./examples
RUN uv pip install --system --no-cache -e . && useradd --uid 10001 --create-home owl
USER 10001:10001
EXPOSE 7860
CMD ["python", "-m", "owl.webapp"]
