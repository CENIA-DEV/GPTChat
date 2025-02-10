"""
The gradio demo server with multiple tabs.
It supports chatting with a single model or chatting with two models side-by-side.
"""

import argparse
import uvicorn
import os
import gradio as gr
from fastchat.serve.gradio_block_arena_anony_cenia import (
    build_side_by_side_ui_anony,
    load_demo_side_by_side_anony,
    set_global_vars_anony,
)
from fastchat.serve.gradio_block_arena_named import (
    set_global_vars_named,
)
from fastchat.serve.gradio_web_server import (
    set_global_vars,
    block_css,
    get_model_list,
    get_ip,
)
from fastchat.utils import (
    build_logger,
    get_window_url_params_js,
    get_window_url_params_with_tos_js,
    parse_gradio_auth_creds,
)
from fastchat.serve.oauth import app as oauth_app, get_user

# Configuración del logger
logger = build_logger("gradio_web_server_multi", "gradio_web_server_multi.log")

# Valores por defecto
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 7860
DEFAULT_CONTROLLER_URL = os.getenv("CONTROLLER_URL", "http://localhost:21001")
DEFAULT_CONCURRENCY_COUNT = 200
DEFAULT_MODEL_LIST_MODE = "once"
DEFAULT_MODERATE = False
DEFAULT_SHOW_TERMS_OF_USE = False
DEFAULT_VISION_ARENA = False
DEFAULT_RANDOM_QUESTIONS = None
DEFAULT_REGISTER_API_ENDPOINT_FILE = "register_gcp"
DEFAULT_GRADIO_AUTH_PATH = None
DEFAULT_ELO_RESULTS_FILE = None
DEFAULT_LEADERBOARD_TABLE_FILE = None
DEFAULT_GRADIO_ROOT_PATH = None
DEFAULT_GA_ID = None
DEFAULT_USE_REMOTE_STORAGE = False
DEFAULT_PASSWORD = None

# Simular los args con valores por defecto
args = {
    "host": DEFAULT_HOST,
    "port": DEFAULT_PORT,
    "share": False,
    "controller_url": DEFAULT_CONTROLLER_URL,
    "concurrency_count": DEFAULT_CONCURRENCY_COUNT,
    "model_list_mode": DEFAULT_MODEL_LIST_MODE,
    "moderate": DEFAULT_MODERATE,
    "show_terms_of_use": DEFAULT_SHOW_TERMS_OF_USE,
    "vision_arena": DEFAULT_VISION_ARENA,
    "random_questions": DEFAULT_RANDOM_QUESTIONS,
    "register_api_endpoint_file": DEFAULT_REGISTER_API_ENDPOINT_FILE,
    "gradio_auth_path": DEFAULT_GRADIO_AUTH_PATH,
    "elo_results_file": DEFAULT_ELO_RESULTS_FILE,
    "leaderboard_table_file": DEFAULT_LEADERBOARD_TABLE_FILE,
    "gradio_root_path": DEFAULT_GRADIO_ROOT_PATH,
    "ga_id": DEFAULT_GA_ID,
    "use_remote_storage": DEFAULT_USE_REMOTE_STORAGE,
    "password": DEFAULT_PASSWORD,
}

# Log de los args
logger.info(f"args: {args}")

# Set global variables
set_global_vars(args["controller_url"], args["moderate"], args["use_remote_storage"])
set_global_vars_named(args["moderate"])
set_global_vars_anony(args["moderate"])

# Obtener la lista de modelos
models, all_models = get_model_list(
    args["controller_url"],
    args["register_api_endpoint_file"],
    vision_arena=False,
)

vl_models, all_vl_models = get_model_list(
    args["controller_url"],
    args["register_api_endpoint_file"],
    vision_arena=True,
)

# Set authorization credentials
auth = None
if args["gradio_auth_path"] is not None:
    auth = parse_gradio_auth_creds(args["gradio_auth_path"])

# Función para cargar la demo
def load_demo(url_params, request: gr.Request):
    global models, all_models, vl_models, all_vl_models

    ip = get_ip(request)
    logger.info(f"load_demo. ip: {ip}. params: {url_params}")

    if args["model_list_mode"] == "reload":
        models, all_models = get_model_list(
            args["controller_url"],
            args["register_api_endpoint_file"],
            vision_arena=False,
        )

        vl_models, all_vl_models = get_model_list(
            args["controller_url"],
            args["register_api_endpoint_file"],
            vision_arena=True,
        )

    side_by_side_anony_updates = load_demo_side_by_side_anony(all_models, url_params)
    return side_by_side_anony_updates

# Función para construir la interfaz de la demo
def build_demo(models, vl_models, elo_results_file, leaderboard_table_file):
    if args["show_terms_of_use"]:
        load_js = get_window_url_params_with_tos_js
    else:
        load_js = get_window_url_params_js

    head_js = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
"""
    if args["ga_id"] is not None:
        head_js += f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={args["ga_id"]}"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());

gtag('config', '{args["ga_id"]}');
window.__gradio_mode__ = "app";
</script>
        """
    text_size = gr.themes.sizes.text_lg
    js_check_session = """
<script>
    setInterval(async function() {
        const response = await fetch("/check-session");
        const data = await response.json();
        if (!data.authenticated) {
            window.location.href = "/login-demo";
        }
    }, 5000); // Verifica cada 5 segundos
</script>
"""

    with gr.Blocks(
        title="Chatea en Español con distintos LLM's",
        theme=gr.themes.Default(text_size=text_size, primary_hue=gr.themes.colors.pink, secondary_hue=gr.themes.colors.blue),
        css=block_css,
        head=head_js,
    ) as demo:

        side_by_side_anony_list = build_side_by_side_ui_anony(models)
        demo_tabs = side_by_side_anony_list
        url_params = gr.JSON(visible=False)

        if args["model_list_mode"] not in ["once", "reload"]:
            raise ValueError(f"Unknown model list mode: {args['model_list_mode']}")

        demo.load(
            load_demo,
            [url_params],
            demo_tabs,
            js=load_js,
        )
        gr.HTML(js_check_session)

        with gr.Row():
            gr.Button("Cerrar sesión", link="/logout")

    return demo

# Construir la demo
if len(models) <= 0:
    # Página de mantenimiento si no hay modelos disponibles
    with gr.Blocks(title="Página en Mantención") as demo:
        gr.Markdown("""
        # 🚧 Página en Mantención
        Estamos realizando algunas mejoras. Por favor, vuelve más tarde.
        """)
else:
    # Construir la interfaz normal
    demo = build_demo(
        models,
        all_vl_models,
        args["elo_results_file"],
        args["leaderboard_table_file"],
    )

# Configurar la cola y montar la aplicación
demo.queue(
    default_concurrency_limit=args["concurrency_count"],
    status_update_rate=10,
    api_open=False,
    max_size=200
)

app = gr.mount_gradio_app(oauth_app, demo, path="/gradio", auth_dependency=get_user)

# Ejecutar el servidor web
if __name__ == "__main__":
    uvicorn.run(app, host=args["host"], port=args["port"])