"""
Local Development Server
รัน: python local_server.py
เปิดเบราว์เซอร์: http://localhost:8888
"""
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from unittest.mock import MagicMock

# ── Bootstrap ─────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))

for _m in ['tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
           'matplotlib', 'matplotlib.figure', 'matplotlib.backends',
           'matplotlib.backends.backend_tkagg']:
    sys.modules[_m] = MagicMock()

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import function handlers (lazy — imported once at startup)
from netlify.functions.calculate import handler as _calc_handler
from netlify.functions.export_pdf import handler as _pdf_handler


# ── Request handler ───────────────────────────────────────────────────────────

class Handler(SimpleHTTPRequestHandler):
    """Serves static files from public/ and routes /api/* to Python handlers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(ROOT, "public"), **kwargs)

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} {fmt % args}")

    def do_POST(self):
        path = self.path.split("?")[0]
        if path in ("/api/calculate", "/.netlify/functions/calculate"):
            self._proxy(_calc_handler)
        elif path in ("/api/export-pdf", "/.netlify/functions/export_pdf"):
            self._proxy(_pdf_handler)
        else:
            self.send_error(404, f"Unknown endpoint: {path}")

    def _proxy(self, handler_fn):
        """Read body, call handler, write response."""
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length).decode("utf-8") if length else ""

        event   = {"body": body, "httpMethod": "POST",
                   "headers": dict(self.headers)}
        context = {}

        try:
            result = handler_fn(event, context)
        except Exception as exc:
            result = {"statusCode": 500,
                      "body": json.dumps({"error": str(exc)})}

        status  = result.get("statusCode", 200)
        headers = result.get("headers", {})
        body_out = result.get("body", "")
        is_b64  = result.get("isBase64Encoded", False)

        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header("Access-Control-Allow-Origin", "*")

        if is_b64:
            import base64
            raw = base64.b64decode(body_out)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        else:
            encoded = body_out.encode("utf-8") if isinstance(body_out, str) else body_out
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8888))
    server = HTTPServer(("localhost", PORT), Handler)
    print(f"\n{'='*52}")
    print(f"  Steel Structure Design — Local Server")
    print(f"  http://localhost:{PORT}")
    print(f"  กด Ctrl+C เพื่อหยุด")
    print(f"{'='*52}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
