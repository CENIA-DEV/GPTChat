import asyncio
from google.cloud import storage
import json
from datetime import datetime

async def get_gcs_bucket(bucket_name):
    """Obtiene el bucket de Google Cloud Storage con manejo de errores."""
    try:
        client = storage.Client()
        bucket = client.get_bucket(bucket_name)
        print(f"✅ Conectado correctamente al bucket: {bucket_name}")
        return bucket
    except Exception as e:
        print(f"❌ Error al conectar con el bucket {bucket_name}: {e}")
        return None

async def list_json_files(bucket_name, folder):
    """Lista los archivos JSON en una carpeta del bucket de GCS."""
    bucket = await get_gcs_bucket(bucket_name)
    if not bucket:
        return []

    try:
        blobs = bucket.list_blobs(prefix=folder)
        json_files = [blob.name for blob in blobs if blob.name.endswith('.json')]
        print(f"📂 Se encontraron {len(json_files)} archivos JSON en {folder}")
        return json_files
    except Exception as e:
        print(f"❌ Error al listar archivos en {folder}: {e}")
        return []

async def read_json_from_gcs(bucket_name, file_key):
    """Lee un archivo JSON desde GCS."""
    bucket = await get_gcs_bucket(bucket_name)
    if not bucket:
        return {}

    try:
        blob = bucket.blob(file_key)
        content = blob.download_as_text()
        return json.loads(content)
    except Exception as e:
        print(f"❌ Error al leer {file_key} desde GCS: {e}")
        return {}

async def write_json_to_gcs(bucket_name, file_key, data):
    """Escribe un archivo JSON en GCS con manejo de errores."""
    bucket = await get_gcs_bucket(bucket_name)
    if not bucket:
        print("⚠️ No se pudo obtener el bucket, el archivo no se guardará.")
        return False

    try:
        blob = bucket.blob(file_key)
        json_data = json.dumps(data, indent=2)
        blob.upload_from_string(json_data, content_type="application/json")
        
        # Verificar si el archivo realmente se subió
        if blob.exists():
            print(f"✅ Archivo guardado correctamente en GCS: gs://{bucket_name}/{file_key}")
        else:
            print(f"❌ Error: el archivo {file_key} no se encuentra en GCS tras la subida.")

        return True
    except Exception as e:
        print(f"❌ Error al escribir {file_key} en GCS: {e}")
        return False

async def process_files(bucket_name, folder, last_seen_files, user_conversation_counts):
    """Procesa nuevos archivos JSON en la carpeta del bucket y actualiza los conteos de conversaciones."""
    current_files = set(await list_json_files(bucket_name, folder))
    new_files = current_files - last_seen_files

    if not new_files:
        print("📌 No se detectaron nuevos archivos.")
        return last_seen_files

    print(f"🔄 Procesando {len(new_files)} nuevos archivos...")

    for file in new_files:
        json_data = await read_json_from_gcs(bucket_name, file)
        if not json_data:
            continue  # Saltar si el archivo no se pudo leer

        # Manejar el caso en el que json_data sea una lista
        if isinstance(json_data, list):
            for item in json_data:
                username = item.get("username")
                if username:
                    user_conversation_counts[username] = user_conversation_counts.get(username, 0) + 1
        else:
            username = json_data.get("username")
            if username:
                user_conversation_counts[username] = user_conversation_counts.get(username, 0) + 1

    # Convertir el formato del JSON a una lista de objetos
    json_output = [{"username": user, "count": count} for user, count in user_conversation_counts.items()]

    # Guardar resultados en GCS dentro de la carpeta "data_chat/"
    output_file = "UserData.json"
    success = await write_json_to_gcs(bucket_name, output_file, json_output)

    if not success:
        print("❌ No se pudo guardar el archivo en GCS. Revisa permisos y conexión.")

    return current_files

async def monitor_bucket(bucket_name, folder, interval=300):
    """Ejecuta el monitoreo del bucket de forma asíncrona."""
    print("🚀 Iniciando el procesador de JSON...")
    
    # Inicializar last_seen_files como vacío y user_conversation_counts desde cero
    last_seen_files = set()
    user_conversation_counts = {}

    while True:
        print(f"[{datetime.now()}] 🔍 Buscando nuevos archivos...")
        last_seen_files = await process_files(bucket_name, folder, last_seen_files, user_conversation_counts)
        await asyncio.sleep(interval)

# Controlador asíncrono para integrar con el sistema
async def update_votes_controller():
    bucket_name = "chat-arena-data"
    folder = "data_chat/"
    interval = 60*10  # Intervalo en segundos

    # Ejecutar la tarea de monitoreo en segundo plano
    await monitor_bucket(bucket_name, folder, interval)

# if __name__ == "__main__":
#     asyncio.run(update_votes_controller())
