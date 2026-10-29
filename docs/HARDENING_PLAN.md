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
