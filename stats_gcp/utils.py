from google.cloud import storage
import json
import pandas as pd

# Configura el bucket y archivo
BUCKET_NAME = "chat-arena-data"
USER_FILE_PATH = "UserData.json"
COUNTRY_FILE_PATH = "CountryData.json"

def load_json_from_gcp(bucket_name, file_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    if not blob.exists():  # Verifica si el archivo existe antes de descargar
        raise FileNotFoundError(f"El archivo {file_path} no existe en el bucket {bucket_name}.")

    json_content = blob.download_as_text()
    data = json.loads(json_content)
    return data

def count_user_votes():
    data = load_json_from_gcp(BUCKET_NAME, USER_FILE_PATH)
    users = [entry["username"] for entry in data]
    votes = [entry["count"] for entry in data]

    df = pd.DataFrame({"Usuarios": users, "Votos": votes})
    df = df.sort_values(by="Votos", ascending=False).head(10)

    # Resetear el índice para mayor claridad
    df.reset_index(drop=True, inplace=True)
    return df

def count_country_votes():
    data = load_json_from_gcp(BUCKET_NAME, COUNTRY_FILE_PATH)
    users = [entry["country"] for entry in data]
    votes = [entry["count"] for entry in data]

    df = pd.DataFrame({"Pais": users, "Votos": votes})
    df = df.sort_values(by="Votos", ascending=False).head(10)

    # Resetear el índice para mayor claridad
    df.reset_index(drop=True, inplace=True)
    return df