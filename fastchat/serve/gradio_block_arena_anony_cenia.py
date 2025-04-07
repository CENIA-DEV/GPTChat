"""
Chatbot Arena (battle) tab.
Users chat with two anonymous models.
"""

import json
import time
import yaml
import gradio as gr
import numpy as np
import asyncio
import anyio
from starlette.responses import RedirectResponse
from fastchat.serve.oauth import db
from fastchat.constants import (
    MODERATION_MSG,
    CONVERSATION_LIMIT_MSG,
    SLOW_MODEL_MSG,
    BLIND_MODE_INPUT_CHAR_LEN_LIMIT,
    CONVERSATION_TURN_LIMIT,
    CONFIG_MODELS_FILE,
    SYSTEM_MSG
)
from fastchat.serve.gradio_block_arena_named import flash_buttons
from fastchat.serve.gradio_web_server import (
    State,
    bot_response,
    get_conv_log_filename,
    no_change_btn,
    enable_btn,
    disable_btn,
    invisible_btn,
    enable_text,
    disable_text,
    acknowledgment_md,
    get_ip,
    get_model_description_md,
    send_to_remote_server,
)

from fastchat.serve.remote_logger import get_remote_logger
from fastchat.utils import (
    build_logger,
    moderation_filter,
)
# from stats.utils import count_country_votes
from stats_gcp.utils import count_country_votes, count_user_votes
import gradio as gr

with open("model_order.txt", "r") as file:
    ORDER_MODELS = file.read().splitlines()


logger = build_logger("gradio_web_server_multi", "gradio_web_server_multi.log")

num_sides = 2
enable_moderation = False
anony_names = ["", ""]
models = []


def set_global_vars_anony(enable_moderation_):
    global enable_moderation
    enable_moderation = enable_moderation_

def change_vote_backdown(request: gr.Request):
    return change_vote(True, request)

def change_vote_no_backdown(request: gr.Request):
    return change_vote(False, request)

def change_vote(backdown: bool, request: gr.Request):
    session_id = request.cookies.get("chat_arena_session_id")  # Obtener el ID de sesión
    # Traer la data de la sesión
    data = sync_load_from_db(session_id)
    states = [json.loads(data["state0"]), json.loads(data["state1"])]

    username = data["email"] if "email" in data.keys() else None
    country = data["country"] if "country" in data.keys() else None
    education = data["education"] if "education" in data.keys() else None
    profession = data["profession"] if "profession" in data.keys() else None
    data = {
        "tstamp": round(time.time(), 4),
        "states": [x for x in states],
        "ip": get_ip(request),
        "username": username,
        "country": country,
        "education": education,
        "profession": profession,
        "backdown": backdown,
    }

    send_to_remote_server(data, folder_name="hackaton-changes")

    return (gr.update(visible=False))

def load_demo_side_by_side_anony(models_, url_params):
    global models
    models = models_

    states = (None,) * num_sides
    selector_updates = (
        gr.Markdown(visible=True),
        gr.Markdown(visible=True),
        gr.update(visible=True),
    )

    return states + selector_updates
def sync_save_to_db(session_id, state0, state1):
    return anyio.from_thread.run(save_to_db, session_id, state0, state1)

async def save_to_db(session_id, state0, state1):
    """Guarda los estados en Firestore de manera asíncrona"""
    if not session_id:
        logger.error("No session ID found. Cannot save to DB.")
        return
    
    data = {
        "state0": json.dumps(state0.dict()),  # Asegúrate de que tenga un método serializable
        "state1": json.dumps(state1.dict()),
    }

    logger.info(f"Saving states for session: {session_id}")
    
    await db.collection("chat-arena-users").document(session_id).set(data, merge=True)

def sync_load_from_db(session_id):
    return anyio.from_thread.run(load_from_db, session_id)

async def load_from_db(session_id):
    """Carga los estados desde Firestore de manera asíncrona"""
    if not session_id:
        logger.error("No session ID found. Cannot load from DB.")
        return None

    doc = await db.collection("chat-arena-users").document(session_id).get()
    if not doc.exists:
        logger.error(f"Session ID {session_id} not found in DB.")
        return None

    data = doc.to_dict()

    return data

def vote_last_response(states, vote_type, model_selectors, request: gr.Request):
    # Registro de la votación en archivo y en el logger remoto.
    session_id = request.cookies.get("chat_arena_session_id")  # Obtener el ID de sesión
    # Traer la data de la sesión
    data = sync_load_from_db(session_id)
    states = [json.loads(data["state0"]), json.loads(data["state1"])]

    username = data["email"] if "email" in data.keys() else None
    country = data["country"] if "country" in data.keys() else None
    education = data["education"] if "education" in data.keys() else None
    profession = data["profession"] if "profession" in data.keys() else None

    with open(get_conv_log_filename(), "a") as fout:
        data = {
            "tstamp": round(time.time(), 4),
            "type": vote_type,
            "states": [x for x in states],
            "ip": get_ip(request),
            "username": username,
            "country": country,
            "education": education,
            "profession": profession,
        }
        fout.write(json.dumps(data) + "\n")

    send_to_remote_server(data)
    get_remote_logger().log(data)

    # Determinar el valor de `change_bool`
    index_0 = ORDER_MODELS.index(states[0]["template_name"])
    index_1 = ORDER_MODELS.index(states[1]["template_name"])
    
    if index_0 > index_1 and vote_type == "leftvote":
        change_bool = True
    elif index_0 < index_1 and vote_type == "rightvote":
        change_bool = False
    else:
        change_bool = False

    # Flujo alternativo basado en `change_bool`
    if change_bool:
        # Habilitar/deshabilitar botones en un orden diferente
        names = (
            "### Model A: " + states[0]["template_name"][:-6], # [:-6] para quitar el "-cenia"
            "### Model B: " + states[1]["template_name"][:-6], # [:-6] para quitar el "-cenia"
        )
        yield names + (disable_text,) + (disable_btn,) * 5 + tuple([gr.update(visible=True)])  # Mostrar el backdown_row # Ejemplo de habilitación
    else:
        # Flujo actual
        if ":" not in model_selectors[0]:
            for i in range(5):
                names = (
                    "### Model A: " + states[0]["template_name"][:-6], # [:-6] para quitar el "-cenia"
                    "### Model B: " + states[1]["template_name"][:-6], # [:-6] para quitar el "-cenia"
                )
                yield names + (disable_text,) + (disable_btn,) * 5 + tuple([gr.update(visible=False)])  # Mostrar el backdown_row
                time.sleep(0.1)
        else:
            names = (
                "### Model A: " + states[0]["template_name"],
                "### Model B: " + states[1]["template_name"],
            )
            yield names + (disable_text,) + (disable_btn,) * 5 + tuple([gr.update(visible=False)])  # Mostrar el backdown_row

def leftvote_last_response(
    state0, state1, model_selector0, model_selector1, request: gr.Request
):
    logger.info(f"leftvote (anony). ip: {get_ip(request)}")
    for x in vote_last_response(
        [state0, state1], "leftvote", [model_selector0, model_selector1], request
    ):
        yield x


def rightvote_last_response(
    state0, state1, model_selector0, model_selector1, request: gr.Request
):
    logger.info(f"rightvote (anony). ip: {get_ip(request)}")
    for x in vote_last_response(
        [state0, state1], "rightvote", [model_selector0, model_selector1], request
    ):
        yield x


def tievote_last_response(
    state0, state1, model_selector0, model_selector1, request: gr.Request
):
    logger.info(f"tievote (anony). ip: {get_ip(request)}")
    for x in vote_last_response(
        [state0, state1], "tievote", [model_selector0, model_selector1], request
    ):
        yield x


def bothbad_vote_last_response(
    state0, state1, model_selector0, model_selector1, request: gr.Request
):
    logger.info(f"bothbad_vote (anony). ip: {get_ip(request)}")
    for x in vote_last_response(
        [state0, state1], "bothbad_vote", [model_selector0, model_selector1], request
    ):
        yield x


def regenerate(state0, state1, request: gr.Request):
    logger.info(f"regenerate (anony). ip: {get_ip(request)}")
    states = [state0, state1]
    if state0.regen_support and state1.regen_support:
        for i in range(num_sides):
            states[i].conv.update_last_message(None)
        return (
            states + [x.to_gradio_chatbot() for x in states] + [""] + [disable_btn] * 6
        )
    states[0].skip_next = True
    states[1].skip_next = True
    return states + [x.to_gradio_chatbot() for x in states] + [""] + [no_change_btn] * 6


def clear_history(request: gr.Request):
    logger.info(f"clear_history (anony). ip: {get_ip(request)}")
    return (
        [None] * num_sides
        + [None] * num_sides
        + anony_names
        + [enable_text]
        + [invisible_btn] * 4
        + [disable_btn] * 2
        + [""]
        + [enable_btn]
    )


def share_click(state0, state1, model_selector0, model_selector1, request: gr.Request):
    logger.info(f"share (anony). ip: {get_ip(request)}")
    if state0 is not None and state1 is not None:
        vote_last_response(
            [state0, state1], "share", [model_selector0, model_selector1], request
        )


with open(CONFIG_MODELS_FILE, "r") as file:
    config = yaml.safe_load(file)

SAMPLING_WEIGHTS = config.get("SAMPLING_WEIGHTS", {})
BATTLE_TARGETS = config.get("BATTLE_TARGETS", {})
ANON_MODELS = config.get("ANON_MODELS", [])
SAMPLING_BOOST_MODELS = config.get("SAMPLING_BOOST_MODELS", [])
OUTAGE_MODELS = config.get("OUTAGE_MODELS", [])


def get_sample_weight(model, outage_models, sampling_weights, sampling_boost_models=[]):
    if model in outage_models:
        return 0
    weight = sampling_weights.get(model, 0)
    if model in sampling_boost_models:
        weight *= 5
    return weight


def get_battle_pair(
    models, battle_targets, outage_models, sampling_weights, sampling_boost_models
):
    if len(models) == 1:
        return models[0], models[0]

    model_weights = []
    for model in models:
        weight = get_sample_weight(
            model, outage_models, sampling_weights, sampling_boost_models
        )
        model_weights.append(weight)
    total_weight = np.sum(model_weights)
    model_weights = model_weights / total_weight
    chosen_idx = np.random.choice(len(models), p=model_weights)
    chosen_model = models[chosen_idx]
    # for p, w in zip(models, model_weights):
    #     print(p, w)

    rival_models = []
    rival_weights = []
    for model in models:
        if model == chosen_model:
            continue
        if model in ANON_MODELS and chosen_model in ANON_MODELS:
            continue
        weight = get_sample_weight(model, outage_models, sampling_weights)
        if (
            weight != 0
            and chosen_model in battle_targets
            and model in battle_targets[chosen_model]
        ):
            # boost to 20% chance
            weight = 0.5 * total_weight / len(battle_targets[chosen_model])
        rival_models.append(model)
        rival_weights.append(weight)
    # for p, w in zip(rival_models, rival_weights):
    #     print(p, w)
    rival_weights = rival_weights / np.sum(rival_weights)
    rival_idx = np.random.choice(len(rival_models), p=rival_weights)
    rival_model = rival_models[rival_idx]

    swap = np.random.randint(2)
    if swap == 0:
        return chosen_model, rival_model
    else:
        return rival_model, chosen_model


def add_text(
    state0, state1, model_selector0, model_selector1, text, request: gr.Request
):  
    ip = get_ip(request)
    logger.info(f"add_text (anony). ip: {ip}. len: {len(text)}")
    states = [state0, state1]
    model_selectors = [model_selector0, model_selector1]
    # Init states if necessary
    if states[0] is None:
        assert states[1] is None

        model_left, model_right = get_battle_pair(
            models,
            BATTLE_TARGETS,
            OUTAGE_MODELS,
            SAMPLING_WEIGHTS,
            SAMPLING_BOOST_MODELS,
        )
        model_selectors[0] = model_left
        model_selectors[1] = model_right
        states = [
            State(model_left),
            State(model_right),
        ]

    if len(text) <= 0:
        for i in range(num_sides):
            states[i].skip_next = True
        return (
            states
            + [x.to_gradio_chatbot() for x in states]
            + ["", None]
            + [
                no_change_btn,
            ]
            * 6
            + [""]
        )

    model_list = [states[i].model_name for i in range(num_sides)]
    # turn on moderation in battle mode
    all_conv_text_left = states[0].conv.get_prompt()
    all_conv_text_right = states[0].conv.get_prompt()
    all_conv_text = (
        all_conv_text_left[-1000:] + all_conv_text_right[-1000:] + "\nuser: " + text
    )
    flagged = moderation_filter(all_conv_text, model_list, do_moderation=True) ###############################################################################
    if flagged:
        logger.info(f"violate moderation (anony). ip: {ip}. text: {text}")
        # overwrite the original text
        text = MODERATION_MSG

    conv = states[0].conv
    if (len(conv.messages) - conv.offset) // 2 >= CONVERSATION_TURN_LIMIT:
        logger.info(f"conversation turn limit. ip: {get_ip(request)}. text: {text}")
        for i in range(num_sides):
            states[i].skip_next = True
        return (
            states
            + [x.to_gradio_chatbot() for x in states]
            + [CONVERSATION_LIMIT_MSG]
            + [
                no_change_btn,
            ]
            * 6
            + [""]
        )

    text = text[:BLIND_MODE_INPUT_CHAR_LEN_LIMIT]  # Hard cut-off
    for i in range(num_sides):
        states[i].conv.append_message(states[i].conv.roles[0], text)
        states[i].conv.append_message(states[i].conv.roles[1], None)
        states[i].skip_next = False

    hint_msg = ""
    for i in range(num_sides):
        if "deluxe" in states[i].model_name:
            hint_msg = SLOW_MODEL_MSG
    return (
        states
        + [x.to_gradio_chatbot() for x in states]
        + [""]
        + [
            disable_btn,
        ]
        * 6
        + [hint_msg]
    )


def bot_response_multi(
    state0,
    state1,
    temperature,
    top_p,
    max_new_tokens,
    request: gr.Request,
):
    session_id = request.cookies.get("chat_arena_session_id")  # Obtener el ID de sesión
    data_session = sync_load_from_db(session_id)
    if not data_session:
        gr.Info("⚠️ Debes reiniciar sesión para interactuar.")
        return RedirectResponse(url='/')
    logger.info(f"bot_response_multi (anony). ip: {get_ip(request)}")
    state0.conv.set_system_message(data_session.get("system_msg", SYSTEM_MSG))
    state1.conv.set_system_message(data_session.get("system_msg", SYSTEM_MSG))

    if state0 is None or state0.skip_next:
        # This generate call is skipped due to invalid inputs
        yield (
            state0,
            state1,
            state0.to_gradio_chatbot(),
            state1.to_gradio_chatbot(),
        ) + (no_change_btn,) * 6
        return

    states = [state0, state1]
    gen = []
    for i in range(num_sides):
        gen.append(
            bot_response(
                states[i],
                temperature,
                top_p,
                max_new_tokens,
                request,
                apply_rate_limit=False,
                use_recommended_config=True,
            )
        )

    model_tpy = []
    for i in range(num_sides):
        token_per_yield = 1
        if states[i].model_name in [
            "gemini-pro",
            "gemma-1.1-2b-it",
            "gemma-1.1-7b-it",
            "phi-3-mini-4k-instruct",
            "phi-3-mini-128k-instruct",
            "snowflake-arctic-instruct",
        ]:
            token_per_yield = 30
        elif states[i].model_name in [
            "qwen-max-0428",
            "qwen1.5-110b-chat",
            "llava-v1.6-34b",
        ]:
            token_per_yield = 7
        elif states[i].model_name in [
            "qwen2-72b-instruct",
        ]:
            token_per_yield = 4
        model_tpy.append(token_per_yield)

    chatbots = [None] * num_sides
    iters = 0
    while True:
        stop = True
        iters += 1
        for i in range(num_sides):
            try:
                # yield fewer times if chunk size is larger
                if model_tpy[i] == 1 or (iters % model_tpy[i] == 1 or iters < 3):
                    ret = next(gen[i])
                    states[i], chatbots[i] = ret[0], ret[1]
                stop = False
            except StopIteration:
                pass
        yield states + chatbots + [disable_btn] * 6
        if stop:
            break
    # Enviar a la base de datos
    # print(state0)
    sync_save_to_db(session_id, state0, state1)

async def update_system_msg(system_msg, request: gr.Request):
    session_id = request.cookies.get("chat_arena_session_id")
    await db.collection("chat-arena-users").document(session_id).set({
        "system_msg": system_msg}, merge=True)
    return system_msg
            

def build_side_by_side_ui_anony(models, demo):
    notice_markdown = f"""
# ⚔️  CENIA Chatbot Arena.



## 📜 Reglas
- Haz cualquier pregunta a dos modelos anónimos (por ejemplo, ChatGPT, Gemini, Claude, Llama) y ¡vota por el mejor!
- Puedes chatear durante varios turnos hasta identificar un ganador.
- Los votos no se contabilizarán si se revela la identidad de los modelos durante la conversación.

## 👇 Chatea Ahora!
"""

    states = [gr.State() for _ in range(num_sides)]
    model_selectors = [None] * num_sides
    chatbots = [None] * num_sides

    gr.Markdown(notice_markdown, elem_id="notice_markdown")

    with gr.Group(elem_id="share-region-anony"):
        with gr.Accordion("📊 Gráfico de participación por pais"):
            gr.BarPlot(
                value=count_country_votes,
                x="Pais",
                y="Votos",
                every=60.0*10,
                x_label_angle=45,
                key="grafico-votos-pais",
                sort='y'
            )
        with gr.Accordion("📜​ Actualiza el prompt", open=False):
            new_prompt_input = gr.Textbox(
                label="Prompt", placeholder=SYSTEM_MSG
            )
            change_prompt_btn = gr.Button("Actualizar Prompt", elem_id="change_prompt_btn", variant="primary")
            actual_promt = gr.Textbox(label="Prompt Actual", value=SYSTEM_MSG, interactive=False)

            change_prompt_btn.click(
                update_system_msg,  
                inputs=[new_prompt_input],  
                outputs=[actual_promt]  
            )
            demo.load(fn = update_system_msg, 
                    inputs=[actual_promt], 
                    outputs=[actual_promt])
        # Cambio de datos nacionalidad
        with gr.Accordion(
            f"🔍 Expanda para ver los modelos disponibles",
            open=False,
        ):
            model_description_md = get_model_description_md(models)
            gr.Markdown(model_description_md, elem_id="model_description_markdown")
        with gr.Row():
            for i in range(num_sides):
                label = "Model A" if i == 0 else "Model B"
                with gr.Column():
                    chatbots[i] = gr.Chatbot(
                        label=label,
                        elem_id="chatbot",
                        height=600,
                        show_copy_button=True,
                    )

        with gr.Row():
            for i in range(num_sides):
                with gr.Column():
                    model_selectors[i] = gr.Markdown(
                        anony_names[i], elem_id="model_selector_md"
                    )
        with gr.Row():
            slow_warning = gr.Markdown("")

    with gr.Column(visible=False) as backdown_row:
        backdown_txt = gr.HTML("""<h2> ¿Sabiendo que la respuesta que no has elegido consume menos energía cambiarías tu elección o la mantendrías?</h2>""")
        with gr.Row():
            no_backdown_btn = gr.Button(value="Mantengo la respuesta", visible=True, interactive=True)
            backdown_btn = gr.Button(value="Cambiaría de respuesta", visible=True, interactive=True)
    with gr.Row():
        leftvote_btn = gr.Button(
            value="👈  A es mejor", visible=False, interactive=False
        )
        rightvote_btn = gr.Button(
            value="👉  B es mejor", visible=False, interactive=False
        )
        tie_btn = gr.Button(value="🤝  Ambas son buenas", visible=False, interactive=False)
        bothbad_btn = gr.Button(
            value="👎 Ambas son malas", visible=False, interactive=False
        )

    with gr.Row():
        textbox = gr.Textbox(
            show_label=False,
            placeholder="👉 Ingresa tu prompt y presiona Enviar",
            elem_id="input_box",
        )
        send_btn = gr.Button(value="Enviar", variant="primary", scale=0)

    with gr.Row() as button_row:
        clear_btn = gr.Button(value="🎲 Nueva Ronda", interactive=False)
        regenerate_btn = gr.Button(value="🔄  Regenerar", interactive=False, visible=True)
        share_btn = gr.Button(value="📷  Compartir")
        

    with gr.Accordion("Parameters", open=False, visible=False) as parameter_row:
        temperature = gr.Slider(
            minimum=0.0,
            maximum=1.0,
            value=0.7,
            step=0.1,
            interactive=True,
            label="Temperature",
        )
        top_p = gr.Slider(
            minimum=0.0,
            maximum=1.0,
            value=1.0,
            step=0.1,
            interactive=True,
            label="Top P",
        )
        max_output_tokens = gr.Slider(
            minimum=16,
            maximum=2048,
            value=1600,
            step=64,
            interactive=True,
            label="Max output tokens",
        )

    gr.Markdown(acknowledgment_md, elem_id="ack_markdown")

    # Register listeners
    btn_list = [
        leftvote_btn,
        rightvote_btn,
        tie_btn,
        bothbad_btn,
        regenerate_btn,
        clear_btn,
    ]
    leftvote_btn.click(
        leftvote_last_response,
        states + model_selectors,
        model_selectors
        + [textbox, leftvote_btn, rightvote_btn, tie_btn, bothbad_btn, send_btn, backdown_row],
    )
    rightvote_btn.click(
        rightvote_last_response,
        states + model_selectors,
        model_selectors
        + [textbox, leftvote_btn, rightvote_btn, tie_btn, bothbad_btn, send_btn, backdown_row],
    )
    tie_btn.click(
        tievote_last_response,
        states + model_selectors,
        model_selectors
        + [textbox, leftvote_btn, rightvote_btn, tie_btn, bothbad_btn, send_btn, backdown_row],
    )
    bothbad_btn.click(
        bothbad_vote_last_response,
        states + model_selectors,
        model_selectors
        + [textbox, leftvote_btn, rightvote_btn, tie_btn, bothbad_btn, send_btn, backdown_row],
    )
    regenerate_btn.click(
        regenerate, states, states + chatbots + [textbox] + btn_list
    ).then(
        bot_response_multi,
        states + [temperature, top_p, max_output_tokens],
        states + chatbots + btn_list,
    ).then(
        flash_buttons, [], btn_list
    )
    clear_btn.click(
        clear_history,
        None,
        states
        + chatbots
        + model_selectors
        + [textbox]
        + btn_list
        + [slow_warning]
        + [send_btn],
    )
    backdown_btn.click(
        change_vote_backdown,
        inputs=[],
        outputs=[backdown_row]
    )
    no_backdown_btn.click(
        change_vote_no_backdown,
        inputs=[],
        outputs=[backdown_row]
    )

    share_js = """
function (a, b, c, d) {
    const captureElement = document.querySelector('#share-region-anony');
    html2canvas(captureElement)
        .then(canvas => {
            canvas.style.display = 'none'
            document.body.appendChild(canvas)
            return canvas
        })
        .then(canvas => {
            const image = canvas.toDataURL('image/png')
            const a = document.createElement('a')
            a.setAttribute('download', 'chatbot-arena.png')
            a.setAttribute('href', image)
            a.click()
            canvas.remove()
        });
    return [a, b, c, d];
}
"""
    share_btn.click(share_click, states + model_selectors, [], js=share_js)

    textbox.submit(
        add_text,
        states + model_selectors + [textbox],
        states + chatbots + [textbox] + btn_list + [slow_warning],
    ).then(
        bot_response_multi,
        states + [temperature, top_p, max_output_tokens],
        states + chatbots + btn_list,
    ).then(
        flash_buttons,
        [],
        btn_list,
    )

    send_btn.click(
        add_text,
        states + model_selectors + [textbox],
        states + chatbots + [textbox] + btn_list,
    ).then(
        bot_response_multi,
        states + [temperature, top_p, max_output_tokens],
        states + chatbots + btn_list,
    ).then(
        flash_buttons, [], btn_list
    )

    return states + model_selectors