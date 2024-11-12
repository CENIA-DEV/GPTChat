import logging
import json
import dotenv
from flask import Flask, request, jsonify
from google.cloud import storage
from datetime import datetime

dotenv.load_dotenv()
app = Flask(__name__)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

storage_client = storage.Client()

BUCKET_NAME = "gpt-las-chat"


@app.route("/upload-json", methods=["POST"])
async def upload_json():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"uploaded_data_{timestamp}.json"

        json_data = json.dumps(data, ensure_ascii=False)

        bucket = storage_client.bucket(BUCKET_NAME)

        blob = bucket.blob("data_chat/" + filename)
        blob.upload_from_string(json_data, content_type="application/json")
        logger.info(f"message: File {filename} uploaded successfully, status: 200")

        return jsonify({"message": f"File {filename} uploaded successfully"}), 200
    except Exception as e:
        logger.info(f"error: {str(e)}, status:500")
        return jsonify({"error": str(e)}), 500
