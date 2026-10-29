# OWL security audit — 2026-10-29

## Scope and methodology

Inspected the fork's 153-file baseline and 98 text/code artifacts on the hardening branch, including entrypoints, CAMEL model wiring, Gradio, local containers, GitHub Actions and community examples. Reviewed language usage, subprocess and browser execution, credential handling, arbitrary downloads, archive extraction, dependency constraints and cloud routing. Added unit tests, a real CAMEL HTTP-mock test, Docker smoke tests, Bandit, pip-audit, CodeQL, Trivy, and tracked-content language/secret checks.

**Assessment:** no assertion of malware-free status. Static analysis cannot certify absence of malicious behaviour; dependencies, container images and legacy examples require continuous review. No cloud credential or external provider was used during this audit.

## Findings and remediations

| ID | Severity | Original evidence | Remediation |
| --- | --- | --- | --- |
| OWL-001 | Critical | Gradio environment table returned unredacted keys and logged edited values | Replaced UI; no secrets editor or logging of values |
| OWL-002 | High | Default agents exposed CodeExecutionToolkit(sandbox="subprocess") and browser/filesystem tools | Replaced default CLI/UI with tool-free assistant/workforce; legacy tool access needs explicit opt-in |
| OWL-003 | High | Document processing accepted arbitrary remote URLs and made unconstrained HEAD/GET requests | Local-document-only policy, root path authorization and denied remote retrieval |
| OWL-004 | High | ZIP archives extracted using system unzip with no entry or decompressed-size checks | Path/symlink validation, 64 MiB/200-entry limits, staged extraction, unit tests |
| OWL-005 | High | Compose ran mugglejinx/owl:latest, exposing mutable third-party supply chain | Build exclusively from local Dockerfile, nonroot user, read-only root, capability drop |
| OWL-006 | High | Dockerfile sourced PyPI and Playwright through third-party mirrors and embedded unnecessary toolchains | Use standard PyPI, minimal core dependencies, no mirror variables |
| OWL-007 | High | CAMEL 0.2.84 imports FastMCP incompatible with MCP SDK 2 | Constrain MCP SDK v1 while migrating upstream |
| OWL-008 | Medium | Role-play module logged raw prompts/responses to general log | Keep raw messages out of default logs, preserve token metadata |
| OWL-009 | Medium | Unused upstream-specific Docker publishing workflow | Removed, replaced with build/test/scan workflows |
| OWL-010 | Medium | Chinese/Japanese UI variants, scripts, assets and translated samples | Removed; automated English-language gate |
| OWL-011 | Medium | README linked missing examples and duplicate out-of-date installation flows | Replaced with local quick-start and independent deployment doc |
| OWL-013 | Medium | GAIA benchmark downloaded an unpinned Hugging Face dataset revision | Require an explicit 40-character `OWL_GAIA_REVISION` SHA before downloading |
| OWL-012 | Medium | Runtime dependencies included unnecessary crawling/media/experimental SDKs | Keep core runtime small; legacy extras are opt-in |

## Residual risks and constraints

- Old community examples can still access external services, browsers, model APIs, and arbitrary local data when explicitly launched. The opt-in flag is **not** isolation. Run in a disposable VM with minimal networking, no production credentials, and reviewed prompts.
- Third-party dependencies and native model runtimes are outside this repository's trust boundary. Monitor advisories, digest-pin deployable images at release, and preserve SBOMs for each build.
- Bedrock OpenAI-compatible CAMEL 0.2.84 uses Bedrock API-key authentication. IAM/SigV4 provider support would require another adapter and separate validation.
- Cloud provider prompts are processed remotely and can be billable. The no-fallback policy protects only OWL's own router. A local Ollama installation configured to proxy cloud models is a distinct risk.
- Local URL model endpoints are operator-supplied; allow only trusted private network endpoints. Never expose the UI without authentication or Ollama's plaintext API on a public interface.
- PDF/image/XLSX samples are not executable source but remain third-party data and must not be treated as benign instructions.
- Real three-provider inference tests, pricing and account-level IAM review cannot be completed without the operator's endpoints/keys; automated tests use mock responses, not paid services.

## Validation policy

All checks must pass before merging. The Python suite uses a live local HTTP mock to exercise the actual CAMEL/OpenAI request path; model-factory routing for the two cloud providers is mocked. The Docker suite starts the UI in a restricted container and probes its HTTP listener. CodeQL/Trivy/pip-audit/Secret/Linguistic checks execute in CI. The latest results are visible in GitHub Actions for PR #1.
