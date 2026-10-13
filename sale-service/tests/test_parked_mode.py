import json
import os
import tempfile
import io
import unittest
from unittest.mock import patch

import server


class ParkedModeTests(unittest.TestCase):
    def test_startup_allows_health_checked_parked_service(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = os.path.join(directory, "sales.sqlite3")
            with patch.object(server, "DB_PATH", server.Path(db_path)), \
                 patch.dict(os.environ, {"SALES_ENABLED": "0"}):
                server.validate_startup()
            self.assertTrue(os.path.isfile(db_path))

    def test_parked_service_has_health_only_and_rejects_writes(self):
        with patch.object(server, "SALES_ENABLED", False):
            def request(path, method="GET"):
                handler = object.__new__(server.Handler)
                handler.path = path
                handler.command = method
                handler.wfile = io.BytesIO()
                status = []
                handler.send_response = lambda code, *_: status.append(code)
                handler.send_header = lambda *_: None
                handler.end_headers = lambda: None
                if method == "POST":
                    handler.do_POST()
                else:
                    handler.do_GET()
                return status[0], json.loads(handler.wfile.getvalue())

            status, health = request("/health")
            self.assertEqual(status, 200)
            self.assertEqual(health["status"], "sales_disabled")
            self.assertFalse(health["sales_enabled"])
            self.assertIsNone(health["seller"])

            status, _ = request("/auction")
            self.assertEqual(status, 503)

            status, _ = request("/bids", "POST")
            self.assertEqual(status, 503)


if __name__ == "__main__":
    unittest.main()
