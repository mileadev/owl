# OWL audit and hardening plan

Baseline: mileadev/owl main, commit 4e5e6e2c427eca82ce1f4db2c77dee1fa546e1fc.

| Priority | Finding | Resolution |
| --- | --- | --- |
| Critical | Web UI showed environment variables and logged sensitive values | Replaced UI with credential-free task interface |
| High | Agent code execution toolkit used host subprocesses | Removed all tool access from default CLI/UI |
| High | Docker referenced third-party mutable image and China-hosted mirrors | Local image build using default repositories |
| High | README referenced missing examples and conflicting Gradio requirements | Concise correct CLI/docs and aligned requirements |
| High | Default inference hardcoded OpenAI | Added fail-closed Ollama, Ollama Cloud, Bedrock selection |
| Medium | Many Chinese/Japanese variants and translated community samples | Remove non-English-only copies and add a language gate |
| Medium | Docker publishing CI hardcoded to upstream | Replace with non-publishing validation |

## Acceptance gates

1. All tracked text files pass the English-only check.
2. Provider tests verify no fallback, credential checks, safe endpoint validation and CAMEL factory calls.
3. Python compilation, tests, and Docker build pass.
4. Manual tests complete for local Ollama, Ollama Cloud and Bedrock with real accounts.
5. Document and code execution tools remain disabled by default; review all legacy examples separately.

## Residual risk

Cloud prompts leave the machine and may incur usage charges. The CAMEL Bedrock model uses API-key auth, not IAM/SigV4. Legacy examples are not certified; enabling tool execution requires a separate container sandbox and command approvals. This pass does not constitute a complete vulnerability audit of transitive dependencies or all third-party community examples. Perform SBOM, pip-audit, container scanning and live end-to-end tests before production.

## Repository-wide language and legacy checks

The cleanup removes obsolete bilingual Docker helper scripts, translated web apps, Chinese-only investment workflows and Chinese-language fixture data. Translation-only or orphaned example artifacts are deleted rather than advertised as runnable.

Default installation does not load community examples. Legacy runners that expose tool-based code execution now require explicit opt-in using `OWL_ENABLE_UNSAFE_LEGACY_TOOLS=I_ACCEPT_THE_RISK`. This flag is **not** a sandbox: run only in an isolated disposable VM without production credentials.

## MCP SDK compatibility

CAMEL 0.2.84 imports `FastMCP` from `mcp.server`. MCP Python SDK 2.x removed the symbol. Until CAMEL is migrated, constrain `mcp>=1.28,<2` and keep security updates on the maintained v1 line. Re-enable SDK 2 only after full integration tests pass.

## Release checklist and rollback

1. Run Python unit tests, the real CAMEL HTTP-mock test, English-only and secrets gates.
2. Require the Docker build, headless UI smoke test, Bandit, dependency audit, image scan and CodeQL results.
3. Manually test a local Ollama endpoint with no internet and both cloud providers with least-privilege, disposable test credentials; verify model IDs, costs, errors and audit logs.
4. Check container hostname/interface and confirm UI is reachable only at host loopback; confirm missing cloud credentials fail closed.
5. Merge to `main` only with green checks; tag a release after acceptance and record the image digest.

Rollback: redeploy the prior Git SHA or `docker compose down`, then check out the previous release. No schema migrations or persistent storage changes are required.

Dependency remediation: Gradio 6.x prevents the Pillow 13 security update. The local UI has been replaced with standard-library HTTP/HTML/JS; Pillow 13 is explicitly required and audited.
