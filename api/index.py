import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from app import create_app

    app = create_app()
except Exception as exc:
    boot_error = exc

    def app(environ, start_response):
        status = "500 Internal Server Error"
        headers = [("Content-Type", "application/json; charset=utf-8")]
        start_response(status, headers)
        body = {
            "error": "Flask app failed to boot",
            "type": boot_error.__class__.__name__,
            "message": str(boot_error),
            "database_url_configured": bool(os.getenv("DATABASE_URL")),
            "secret_key_configured": bool(os.getenv("SECRET_KEY")),
        }
        return [json.dumps(body, ensure_ascii=False).encode("utf-8")]
