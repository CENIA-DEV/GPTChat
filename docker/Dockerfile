# Usar la imagen base con soporte para CUDA
FROM nvidia/cuda:12.2.0-runtime-ubuntu20.04

# Actualizar los paquetes del sistema y agregar el repositorio para Python 3.10
RUN apt-get update -y && apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update -y && \
    apt-get install -y \
    python3.10 python3.10-distutils python3.10-venv curl git && \
    apt-get clean

# Descargar e instalar pip para Python 3.10
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

# Crear alias para Python y Pip (obligatorio para asegurar Python 3.10 por defecto)
RUN ln -sf /usr/bin/python3.10 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Verificar la versión de Python y Pip (debugging)
RUN python3 --version && python3 --version && pip --version

# Instalar FastChat y sus dependencias
RUN pip3 install --no-cache-dir fschat fschat[model_worker,webui]

# Instalar librerías adicionales
RUN pip3 install --no-cache-dir \
    vertexai \
    openai \
    plotly \
    google-cloud-aiplatform \
    mistralai \
    anthropic \
    fastapi \
    uvicorn \
    flask \
    google-cloud-storage \
    python-dotenv \
    gunicorn

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el contenido desde la raíz del repositorio al contenedor
COPY . /app

# Exponer los puertos necesarios
EXPOSE 7860 5000 8000 21001 8080

# CMD flexible basado en el servicio que ejecuta este contenedor
CMD ["sh", "-c", "$FASTCHAT_CMD"]
