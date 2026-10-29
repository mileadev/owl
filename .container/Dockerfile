FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY owl ./owl
COPY examples ./examples
RUN python -m pip install --no-cache-dir . \
    && useradd --uid 10001 --create-home --shell /usr/sbin/nologin owl
USER 10001:10001
ENV HOME=/tmp XDG_CACHE_HOME=/tmp/cache
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/', timeout=3).read()" || exit 1
CMD ["python", "-m", "owl.webapp"]
