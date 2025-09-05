import os
import json
import uuid
import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Load env variables
load_dotenv()

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "portfolio")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI env var is required")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize MongoDB client
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
contacts_col = db.get_collection("contact_submissions")


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
        result = contacts_col.insert_one(payload)
        return jsonify({"ok": True, "id": str(result.inserted_id)})
    except PyMongoError as e:
        app.logger.exception("❌ MongoDB insert failed")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
