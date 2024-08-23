from flask import Flask, request, jsonify
from google.cloud import storage
import json
from datetime import datetime
import dotenv

dotenv.load_dotenv()
app = Flask(__name__)

# Initialize Google Cloud Storage client
storage_client = storage.Client()

# Define your bucket name
BUCKET_NAME = "gpt-las-chat"


@app.route("/upload-json", methods=["POST"])
async def upload_json():
    try:
        # Get the JSON data from the request
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        # Create a unique filename using the current timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"uploaded_data_{timestamp}.json"

        # Convert the JSON data to a string
        json_data = json.dumps(data, ensure_ascii=False)

        # Get the bucket
        bucket = storage_client.bucket(BUCKET_NAME)

        # Create a new blob and upload the JSON data
        blob = bucket.blob("test_data_chat/" + filename)
        await blob.upload_from_string(json_data, content_type="application/json")

        return jsonify({"message": f"File {filename} uploaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

