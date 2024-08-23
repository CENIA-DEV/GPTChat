"""
Global constants.
"""

from enum import IntEnum
import os

REPO_PATH = os.path.dirname(os.path.dirname(__file__))

# Survey Link URL (to be removed)
SURVEY_LINK = """<div style='text-align: center; margin: 20px 0;'>
    <div style='display: inline-block; border: 2px solid #DE3163; padding: 10px; border-radius: 5px;'>
        <span style='color: #DE3163; font-weight: bold;'>We would love your feedback! Fill out <a href='https://docs.google.com/forms/d/e/1FAIpQLSfKSxwFOW6qD05phh4fwYjk8q0YV1VQe_bmK0_qOVTbC66_MA/viewform?usp=sf_link' style='color: #DE3163; text-decoration: underline;'>this short survey</a> to tell us what you like about the arena, what you don't like, and what you want to see in the future.</span>
    </div>
</div>"""

##### For the gradio web server
SERVER_ERROR_MSG = "**ERROR DE RED DEBIDO AL ALTO TRÁFICO. POR FAVOR REGENERE O ACTUALICE ESTA PÁGINA.**"
TEXT_MODERATION_MSG = (
    "$MODERATION$ SU TEXTO VIOLA NUESTRAS DIRECTRICES DE MODERACIÓN DE CONTENIDOS."
)
IMAGE_MODERATION_MSG = (
    "$MODERATION$ YOUR IMAGE VIOLATES OUR CONTENT MODERATION GUIDELINES."
)
MODERATION_MSG = "$MODERATION$ YOUR INPUT VIOLATES OUR CONTENT MODERATION GUIDELINES."
CONVERSATION_LIMIT_MSG = "HAS ALCANZADO EL LÍMITE DE DURACIÓN DE LA CONVERSACIÓN. POR FAVOR, BORRA EL HISTORIAL E INICIA UNA NUEVA CONVERSACIÓN."
INACTIVE_MSG = "ESTA SESIÓN HA ESTADO INACTIVA DURANTE DEMASIADO TIEMPO. POR FAVOR, ACTUALICE ESTA PÁGINA."
SLOW_MODEL_MSG = "⚠️  Ambos modelos mostrarán las respuestas a la vez. Ten paciencia, ya que puede tardar más de 30 segundos."
RATE_LIMIT_MSG = "**SE HA ALCANZADO EL LÍMITE DE VELOCIDAD DE ESTE MODELO. VUELVA MÁS TARDE O UTILICE  <span style='color: red; font-weight: bold;'>[BATTLE MODE](https://chat.lmsys.org)</span> (the 1st tab).**"
# Maximum input length
INPUT_CHAR_LEN_LIMIT = int(os.getenv("FASTCHAT_INPUT_CHAR_LEN_LIMIT", 12000))
BLIND_MODE_INPUT_CHAR_LEN_LIMIT = int(
    os.getenv("FASTCHAT_BLIND_MODE_INPUT_CHAR_LEN_LIMIT", 30000)
)
# Maximum conversation turns
CONVERSATION_TURN_LIMIT = 50
# Session expiration time
SESSION_EXPIRATION_TIME = 3600
# The output dir of log files
LOGDIR = os.getenv("LOGDIR", ".")
# CPU Instruction Set Architecture
CPU_ISA = os.getenv("CPU_ISA")
# models to use config file path
CONFIG_MODELS_FILE = os.getenv("FASTCHAT_CONFIG", "fastchat/configs/models.yaml")
# System Spanish message
SYSTEM_MSG = "Una conversación entre un usuario curioso y un modelo de lenguaje.El modelo de lenguaje debe responder siempre en español y proporcionar información verificada sin inventar datos."

##### For the controller and workers (could be overwritten through ENV variables.)
CONTROLLER_HEART_BEAT_EXPIRATION = int(
    os.getenv("FASTCHAT_CONTROLLER_HEART_BEAT_EXPIRATION", 90)
)
WORKER_HEART_BEAT_INTERVAL = int(os.getenv("FASTCHAT_WORKER_HEART_BEAT_INTERVAL", 45))
WORKER_API_TIMEOUT = int(os.getenv("FASTCHAT_WORKER_API_TIMEOUT", 100))
WORKER_API_EMBEDDING_BATCH_SIZE = int(
    os.getenv("FASTCHAT_WORKER_API_EMBEDDING_BATCH_SIZE", 4)
)


class ErrorCode(IntEnum):
    """
    https://platform.openai.com/docs/guides/error-codes/api-errors
    """

    VALIDATION_TYPE_ERROR = 40001

    INVALID_AUTH_KEY = 40101
    INCORRECT_AUTH_KEY = 40102
    NO_PERMISSION = 40103

    INVALID_MODEL = 40301
    PARAM_OUT_OF_RANGE = 40302
    CONTEXT_OVERFLOW = 40303

    RATE_LIMIT = 42901
    QUOTA_EXCEEDED = 42902
    ENGINE_OVERLOADED = 42903

    INTERNAL_ERROR = 50001
    CUDA_OUT_OF_MEMORY = 50002
    GRADIO_REQUEST_ERROR = 50003
    GRADIO_STREAM_UNKNOWN_ERROR = 50004
    CONTROLLER_NO_WORKER = 50005
    CONTROLLER_WORKER_TIMEOUT = 50006
