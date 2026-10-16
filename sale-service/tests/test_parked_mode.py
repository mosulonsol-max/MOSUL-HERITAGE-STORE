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

    def test_parked_service_exposes_health_and_readiness_but_rejects_sales(self):
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

            with patch.object(server, "readiness_snapshot", return_value={
                "auction_ready": False, "payment_enabled": False,
                "blockers": ["delivery_package"],
            }):
                status, readiness = request("/readiness")
            self.assertEqual(status, 200)
            self.assertFalse(readiness["auction_ready"])
            self.assertFalse(readiness["payment_enabled"])
            self.assertEqual(readiness["blockers"], ["delivery_package"])

            status, _ = request("/auction")
            self.assertEqual(status, 503)

            status, _ = request("/bids", "POST")
            self.assertEqual(status, 503)


if __name__ == "__main__":
    unittest.main()
