import os
import json
import uuid
import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from botocore.exceptions import ClientError

# Load env variables
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET = os.getenv("S3_BUCKET", "contact-form-submissions")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize boto3 client
s3 = boto3.client("s3", region_name=AWS_REGION)


def ensure_bucket(bucket_name: str) -> bool:
    """Ensure the S3 bucket exists, create if missing (idempotent)."""
    try:
        s3.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        # If bucket doesn't exist → create
        if error_code in ("404", "NoSuchBucket", "403"):
            try:
                if AWS_REGION == "us-east-1":  # special case
                    s3.create_bucket(Bucket=bucket_name)
                else:
                    s3.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
                    )
                app.logger.info(f"✅ Created bucket: {bucket_name}")
                return True
            except Exception as create_err:
                app.logger.error(f"❌ Could not create bucket: {create_err}")
                return False
        else:
            app.logger.error(f"❌ Bucket check failed: {e}")
            return False


@app.post("/api/contact")
def contact():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not message:
        return jsonify({"ok": False, "error": "All fields are required"}), 400

    ts = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    key = (
        f"contact-form-submissions/"
        f"{datetime.datetime.utcnow().strftime('%Y/%m/%d')}/"
        f"{ts}_{uuid.uuid4().hex}.json"
    )

    payload = {
        "name": name,
        "email": email,
        "message": message,
        "submitted_at": ts,
        "ip": request.remote_addr,
    }

    # Ensure bucket exists before writing
    if not ensure_bucket(S3_BUCKET):
        return jsonify({"ok": False, "error": "Could not prepare storage"}), 500

    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(payload, ensure_ascii=False),
            ContentType="application/json",
            ServerSideEncryption="AES256",
        )
        return jsonify({"ok": True, "id": key})
    except Exception as e:
        app.logger.exception("❌ S3 upload failed")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
