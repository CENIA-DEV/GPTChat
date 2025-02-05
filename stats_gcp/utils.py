from google.cloud import storage
import json
import pandas as pd

# Configura el bucket y archivo
BUCKET_NAME = "chat-arena-data"
FILE_PATH = "UserDataTest.json"

def load_json_from_gcp(bucket_name, file_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    if not blob.exists():  # Verifica si el archivo existe antes de descargar
        raise FileNotFoundError(f"El archivo {file_path} no existe en el bucket {bucket_name}.")

    json_content = blob.download_as_text()
    data = json.loads(json_content)
    return data

def count_country_votes():
    print("actualizar")
    data = load_json_from_gcp(BUCKET_NAME, FILE_PATH)
    users = [list(user.keys())[0] for user in data]
    votes = [list(user.values())[0] for user in data]
    
    df = pd.DataFrame({"Usuarios": users, "Votos": votes})
    df = df.sort_values(by="Votos", ascending=False).head(10)
    return df
