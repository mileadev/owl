import os
import unittest
from unittest.mock import patch
from owl.providers import _local_endpoint, resolve_provider


class ProviderTests(unittest.TestCase):
    def test_local_default(self):
        with patch.dict(os.environ, {"OWL_PROVIDER": "ollama"}, clear=True):
            result = resolve_provider()
        self.assertEqual(result.url, "http://127.0.0.1:11434/v1")
        self.assertNotIn("ollama", repr(result))

    def test_private_cluster(self):
        self.assertEqual(_local_endpoint("http://100.108.101.105:11434/v1"),
                         "http://100.108.101.105:11434/v1")

    def test_public_http_rejected(self):
        with self.assertRaises(ValueError):
            _local_endpoint("http://example.com/v1")

    def test_cloud_key_required(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "OLLAMA_API_KEY"):
                resolve_provider("ollama-cloud")

    def test_cloud_url_and_redaction(self):
        with patch.dict(os.environ, {"OLLAMA_API_KEY": "secret"}, clear=True):
            result = resolve_provider("ollama-cloud")
        self.assertEqual(result.url, "https://ollama.com/v1")
        self.assertNotIn("secret", repr(result))

    def test_bedrock_region(self):
        env = {"BEDROCK_API_KEY": "token", "AWS_REGION": "eu-west-1",
               "BEDROCK_MODEL_ID": "example-model"}
        with patch.dict(os.environ, env, clear=True):
            result = resolve_provider("bedrock")
        self.assertEqual(result.url,
                         "https://bedrock-runtime.eu-west-1.amazonaws.com/openai/v1")

    def test_no_fallback(self):
        with self.assertRaises(ValueError):
            resolve_provider("unknown")
