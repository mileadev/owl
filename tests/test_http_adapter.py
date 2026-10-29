"""Exercise the installed CAMEL model backend against a fake local Ollama server."""

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from owl.providers import create_model, resolve_provider
from owl.runtime import run_task


class FakeOllama(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        message = {
            "id": "chatcmpl-mock",
            "object": "chat.completion",
            "created": 1,
            "model": payload["model"],
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": "MOCK_OK"},
                 "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
        }
        body = json.dumps(message).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class HttpAdapterTests(unittest.TestCase):
    def test_local_ollama_real_model_factory(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllama)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/v1"
            with patch.dict(os.environ, {"OLLAMA_BASE_URL": url, "OLLAMA_MODEL": "qwen3:8b"}):
                self.assertEqual(run_task("Test connectivity", mode="assistant"), "MOCK_OK")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_cloud_and_bedrock_factory_selection(self):
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType
        with patch.object(ModelFactory, "create", return_value=object()) as factory:
            with patch.dict(os.environ, {"OLLAMA_API_KEY": "test-only", "OLLAMA_CLOUD_MODEL": "gemma4:31b"}):
                create_model("ollama-cloud")
            self.assertEqual(factory.call_args.kwargs["model_platform"],
                             ModelPlatformType.OPENAI_COMPATIBLE_MODEL)
            self.assertEqual(factory.call_args.kwargs["url"], "https://ollama.com/v1")
        with patch.object(ModelFactory, "create", return_value=object()) as factory:
            env = {"BEDROCK_API_KEY": "test-only", "AWS_REGION": "eu-west-1",
                   "BEDROCK_MODEL_ID": "openai.gpt-oss-20b-1:0"}
            with patch.dict(os.environ, env):
                create_model("bedrock")
            self.assertEqual(factory.call_args.kwargs["model_platform"],
                             ModelPlatformType.AWS_BEDROCK)
            self.assertEqual(factory.call_args.kwargs["url"],
                             "https://bedrock-runtime.eu-west-1.amazonaws.com/openai/v1")


if __name__ == "__main__":
    unittest.main()
