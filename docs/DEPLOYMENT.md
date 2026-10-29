# Local deployment

Install Python 3.12, uv and Ollama; start Ollama, then run:

```bash
cp .env.example .env
uv venv --python 3.12
uv pip install -e .
ollama pull qwen3:8b
.venv/bin/python -m examples.run "Hello"
.venv/bin/python -m owl.webapp
```

Default host and port: `127.0.0.1:7860`. Change `OLLAMA_BASE_URL` to a **private, firewall-restricted** Ollama endpoint for GPU cluster nodes. Never expose unauthenticated Ollama HTTP publicly.

To use Ollama Cloud, configure `OLLAMA_API_KEY`, `OLLAMA_CLOUD_MODEL` and `OWL_PROVIDER=ollama-cloud`. To use Bedrock, configure `BEDROCK_API_KEY`, `BEDROCK_MODEL_ID`, `AWS_REGION` and `OWL_PROVIDER=bedrock`. The pinned CAMEL adapter requires an API key and does not use AWS IAM profiles. Both cloud providers can incur charges.

Docker Desktop:

```bash
docker compose -f .container/docker-compose.yml config
docker compose -f .container/docker-compose.yml up --build -d
docker compose -f .container/docker-compose.yml logs --tail=100 owl
docker compose -f .container/docker-compose.yml down
```

The container listens on port 7860 internally, published to host loopback only. Docker's Ollama endpoint defaults to `host.docker.internal`; use `OLLAMA_DOCKER_BASE_URL` for other private endpoints. Docker bridge networking on Linux requires a reachable, restricted Ollama listener.

Optional (untrusted) legacy toolkits: install with `uv pip install -e '.[legacy]'`. Keep these outside production and never expose host command execution to untrusted input.\n\nValidation: `python -m unittest discover -s tests -v`, `python -m compileall -q owl examples`, and `python scripts/check_english.py`. Live inference tests require an accessible model and credentials.

The previous `.container/build_docker*.{sh,bat}` and `run_in_docker*.{sh,bat}` helpers are retired. Use standard Docker Compose commands instead.

CAMEL 0.2.84 currently requires MCP SDK v1 for its `FastMCP` imports. Do not separately upgrade `mcp` to v2 in this environment.
