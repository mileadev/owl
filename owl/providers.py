"""Explicit fail-closed routing to local Ollama, Ollama Cloud and Bedrock."""

from __future__ import annotations
import ipaddress
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
PROVIDERS = ("ollama", "ollama-cloud", "bedrock")
_PRIVATE_SHARED = ipaddress.ip_network("100.64.0.0/10")


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    model: str
    url: str
    api_key: str = field(default="", repr=False)


def _local_endpoint(value: str) -> str:
    url = value.strip().rstrip("/")
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("OLLAMA_BASE_URL must be an HTTP(S) URL.")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("OLLAMA_BASE_URL cannot contain credentials or query parameters.")
    if parts.path != "/v1":
        raise ValueError("OLLAMA_BASE_URL must end in /v1.")
    if parts.scheme == "http":
        try:
            ip = ipaddress.ip_address(parts.hostname)
            safe = (
                ip.is_loopback
                or ip in ipaddress.ip_network("10.0.0.0/8")
                or ip in ipaddress.ip_network("172.16.0.0/12")
                or ip in ipaddress.ip_network("192.168.0.0/16")
                or ip in ipaddress.ip_network("fc00::/7")
                or ip in _PRIVATE_SHARED
            )
        except ValueError:
            safe = parts.hostname.lower() in ("localhost", "host.docker.internal")
        if not safe:
            raise ValueError("Plaintext HTTP is restricted to local/private endpoints.")
    return url


def resolve_provider(provider: str | None = None, model: str | None = None) -> ProviderConfig:
    selected = (provider or os.getenv("OWL_PROVIDER", "ollama")).strip().lower()
    if selected not in PROVIDERS:
        raise ValueError("OWL_PROVIDER must be ollama, ollama-cloud or bedrock.")
    defaults = {
        "ollama": os.getenv("OLLAMA_MODEL", "qwen3:8b"),
        "ollama-cloud": os.getenv("OLLAMA_CLOUD_MODEL", "gemma4:31b"),
        "bedrock": os.getenv("BEDROCK_MODEL_ID", ""),
    }
    selected_model = (model or defaults[selected]).strip()
    if not selected_model or len(selected_model) > 200 or any(c.isspace() for c in selected_model):
        raise ValueError("Set a valid model identifier for the selected provider.")

    if selected == "ollama":
        return ProviderConfig(
            selected,
            selected_model,
            _local_endpoint(os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")),
            "ollama",
        )
    if selected == "ollama-cloud":
        key = os.getenv("OLLAMA_API_KEY", "").strip()
        if not key:
            raise ValueError("OLLAMA_API_KEY is required for Ollama Cloud.")
        return ProviderConfig(selected, selected_model, "https://ollama.com/v1", key)

    key = os.getenv("BEDROCK_API_KEY", "").strip()
    if not key:
        raise ValueError("BEDROCK_API_KEY is required for Bedrock API-key authentication.")
    region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "")).strip()
    if not re.fullmatch(r"[a-z]{2}(?:-gov)?-[a-z]+-\d", region):
        raise ValueError("Set AWS_REGION to a valid Bedrock runtime region.")
    return ProviderConfig(
        selected,
        selected_model,
        f"https://bedrock-runtime.{region}.amazonaws.com/openai/v1",
        key,
    )


def create_model(provider: str | None = None, model: str | None = None):
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType

    config = resolve_provider(provider, model)
    platform = (ModelPlatformType.AWS_BEDROCK if config.provider == "bedrock"
                else ModelPlatformType.OPENAI_COMPATIBLE_MODEL)
    return ModelFactory.create(
        model_platform=platform,
        model_type=config.model,
        url=config.url,
        api_key=config.api_key,
        model_config_dict={"temperature": 0.1},
    )
