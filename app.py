import os
import json
import uuid
import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# Load env variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Local submissions file (for dev without DB)
SUBMISSIONS_FILE = os.path.join(os.path.dirname(__file__), "submissions.jsonl")


@app.post("/api/contact")
def contact():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not message:
        return jsonify({"ok": False, "error": "All fields are required"}), 400

    ts = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    payload = {
        "_id": uuid.uuid4().hex,
        "name": name,
        "email": email,
        "message": message,
        "submitted_at": ts,
        "ip": request.remote_addr,
    }

    try:
        # append to local JSONL file for development
        with open(SUBMISSIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return jsonify({"ok": True, "id": payload["_id"]})
    except Exception as e:
        app.logger.exception("❌ Local write failed")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
