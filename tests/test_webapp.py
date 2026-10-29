"""HTTP UI security and mocked execution integration tests."""

import http.client
import json
import threading
import unittest
from unittest.mock import patch

from owl.webapp import make_server


class BrowserSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server("127.0.0.1", 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        data = response.read()
        result = response.status, data, dict(response.getheaders())
        connection.close()
        return result

    def post(self, origin=True, task="test"):
        port = self.server.server_port
        headers = {"Content-Type": "application/json"}
        if origin:
            headers["Origin"] = f"http://127.0.0.1:{port}"
        return self.request("POST", "/api/run", json.dumps({
            "task": task, "provider": "ollama", "model": "", "mode": "assistant"
        }), headers)

    def test_frontend_is_served_with_csp(self):
        status, html, headers = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Local Ollama", html)
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertIn("no-store", headers["Cache-Control"])

    def test_config_does_not_expose_keys(self):
        with patch.dict("os.environ", {"OLLAMA_API_KEY": "never-echo-this", "OWL_PROVIDER": "ollama-cloud"}):
            code, body, _ = self.request("GET", "/api/config")
        self.assertEqual(code, 200)
        self.assertNotIn(b"never-echo-this", body)
        self.assertEqual(json.loads(body)["provider"], "ollama-cloud")

    def test_cross_origin_rejected(self):
        status, _, _ = self.post(origin=False)
        self.assertEqual(status, 403)
        port = self.server.server_port
        status, _, _ = self.request("POST", "/api/run", b"{}", {
            "Origin": "https://evil.test",
            "Content-Type": "application/json",
            "Host": f"127.0.0.1:{port}",
        })
        self.assertEqual(status, 403)

    def test_task_routes_without_echoed_prompt(self):
        with patch("owl.webapp.run_task", return_value="<script>not-executed</script>") as run:
            status, body, _ = self.post()
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["answer"], "<script>not-executed</script>")
        run.assert_called_once_with("test", "ollama", None, "assistant")
        js = self.request("GET", "/app.js")[1]
        self.assertIn(b".textContent", js)
        self.assertNotIn(b"innerHTML", js)

    def test_reject_unknown_content_type(self):
        port = self.server.server_port
        status, _, _ = self.request("POST", "/api/run", b"{}", {
            "Content-Type": "text/plain",
            "Origin": f"http://127.0.0.1:{port}",
        })
        self.assertEqual(status, 415)

    def test_reject_non_loopback_without_explicit_override(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                make_server("0.0.0.0", 0)


if __name__ == "__main__":
    unittest.main()
