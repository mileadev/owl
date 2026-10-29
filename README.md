# OWL — Local-first Multi-Agent Assistant

English-only fork of [CAMEL-AI OWL](https://github.com/camel-ai/owl). Inference providers: **local Ollama**, **Ollama Cloud**, and **Amazon Bedrock**. Python 3.10–3.12.

## Quick start

```bash
git clone https://github.com/mileadev/owl.git
cd owl
cp .env.example .env
uv venv --python 3.12
uv pip install -e .
ollama pull qwen3:8b
.venv/bin/python -m examples.run "Explain OWL architecture"
.venv/bin/python -m owl.webapp
```

The UI listens on http://127.0.0.1:7860. Ollama must be running on port 11434.

## Provider configuration

Set `OWL_PROVIDER` in `.env`, or pass `--provider` to CLI. The UI also selects providers. Missing keys or failed requests **never trigger fallback**.

| Provider | Required configuration |
| --- | --- |
| `ollama` (default, free/local) | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |
| `ollama-cloud` | `OLLAMA_API_KEY`, `OLLAMA_CLOUD_MODEL` |
| `bedrock` | `BEDROCK_API_KEY`, `AWS_REGION`, `BEDROCK_MODEL_ID` |

Ollama Cloud uses `https://ollama.com/v1`. Bedrock uses the regional OpenAI-compatible endpoint with **API-key authentication** supported by CAMEL 0.2.84; IAM/SigV4 role credentials are not supported by this implementation. Cloud usage may incur charges.

Use `--mode workforce` for a reasoning/verification workforce; it makes multiple model requests. Optional search requires `OWL_ENABLE_WEB_SEARCH=1` and workforce mode.

## Docker

```bash
cp .env.example .env
docker compose -f .container/docker-compose.yml up --build
```

Docker Desktop uses `host.docker.internal` for native Ollama. Consult [deployment instructions](docs/DEPLOYMENT.md).

## Security

Default CLI/UI does not expose shell, filesystem or browser execution. Credentials remain in an ignored local `.env` and are never rendered by the UI. The default deployment must not be exposed publicly without authentication. The core runtime has no autonomous command, browser, or filesystem access. Legacy examples and community integrations require the optional `legacy` dependencies and are **not** safe for untrusted tasks; do not use them with sensitive host credentials.

See [audit and hardening plan](docs/HARDENING_PLAN.md) for findings, tests and remaining work. [Apache-2.0](licenses/LICENSE); original attribution in [CITATION.cff](CITATION.cff).
