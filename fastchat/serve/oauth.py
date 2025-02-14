import os
from datetime import datetime, timezone, timedelta
from authlib.integrations.starlette_client import OAuth, OAuthError
from google.cloud import firestore
from fastapi import FastAPI, Depends, Request, HTTPException
from starlette.config import Config
from starlette.responses import RedirectResponse, Response
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import anyio
import uuid
import gradio as gr

app = FastAPI()
db = firestore.AsyncClient()

# OAuth settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY")
SESSION_LIFETIME_SECONDS = 60 * 60 * 12  # 12 horas

# Set up OAuth
config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)
def sync_get_user(request):
    return anyio.from_thread.run(get_user, request)

async def get_user(request: Request):
    session_id = request.cookies.get('chat_arena_session_id')
    
    if not session_id:
        raise HTTPException(status_code=307, detail="Redirect", headers={"Location": "/login-demo"})

    # Verificar si la sesión aún está activa en Firestore
    session_ref = db.collection("chat-arena-users").document(session_id)
    session_doc = await session_ref.get()

    if not session_doc.exists:
        response = RedirectResponse(url="/login-demo")
        response.delete_cookie("chat_arena_session_id")
        raise HTTPException(status_code=307, detail="Redirect", headers={"Location": "/login-demo"})

    session_data = session_doc.to_dict()
    
    # Verificar si la sesión ha expirado
    expires_at = session_data.get("expires_at")
    if expires_at and expires_at < datetime.now(timezone.utc):
        await session_ref.delete()
        response = RedirectResponse(url="/login-demo")
        response.delete_cookie("chat_arena_session_id")
        raise HTTPException(status_code=307, detail="Redirect", headers={"Location": "/login-demo"})

    return session_id

@app.get('/')
async def public(user: str = Depends(get_user)):
    return RedirectResponse(url='/gradio')

@app.route('/logout')
async def logout(request: Request):
    session_id = request.cookies.get("chat_arena_session_id")
    if session_id:
        await db.collection("chat-arena-users").document(session_id).delete()
    response = RedirectResponse(url='/login-demo')
    response.delete_cookie("chat_arena_session_id")
    return response

@app.route('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.route('/auth')
async def auth(request: Request):
    try:
        # Autoriza el token de acceso
        access_token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(url='/')

    # Extrae información del usuario
    user_info = access_token.get("userinfo")
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")

    chat_arena_session_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=SESSION_LIFETIME_SECONDS)

    # Guardamos la sesión en Firestore
    await db.collection("chat-arena-users").document(chat_arena_session_id).set(
        {"name": name, "email": email, "picture": picture, "expires_at": expires_at}
    )

    # Crea una respuesta y establece la cookie de sesión
    response = RedirectResponse(url='/')
    response.set_cookie(
        key="chat_arena_session_id", 
        value=chat_arena_session_id, 
        max_age=SESSION_LIFETIME_SECONDS, 
        httponly=True, 
        secure=True
    )
    
    return response

@app.get("/check-session")
async def check_session(request: Request):
    session_id = request.cookies.get("chat_arena_session_id")

    if not session_id:
        return {"authenticated": False}

    session_ref = db.collection("chat-arena-users").document(session_id)
    session_doc = session_ref.get()

    if not session_doc.exists or session_doc.to_dict().get("expires_at") < datetime.now(timezone.utc):
        return {"authenticated": False}

    return {"authenticated": True}




GPTLAS_LOGO = "https://storage.googleapis.com/public-gptlas-assets/logo-gptlas-2.png"
CENIA_LOGO = "https://www.cenia.cl/wp-content/themes/urantiacoscenia/assets/images/logo_cenia.png"

def build_login():
    with gr.Blocks(title="Chatea en Español con distintos LLM's", fill_height= True,
        theme=gr.themes.Default(text_size = gr.themes.sizes.text_lg, primary_hue=gr.themes.colors.pink, secondary_hue=gr.themes.colors.blue),
        css="""
        body {
            display: flex;
            justify-content: center;
        }
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: auto;
            padding: 20px;
            border-radius: 10px;
        }
        .logo-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 500px;
        }
        .logo {
            margin: 0 auto;
            display: block;
            background: none;
            box-shadow: none;
            border: none;
            outline: none;
        }
    """) as login_demo:
        
        with gr.Column(elem_classes="login-container"):
            with gr.Row(elem_classes="logo-container"):
                gr.Image(GPTLAS_LOGO, elem_classes="logo", width=250, height=80, show_label=False,
                        show_download_button=False, show_fullscreen_button=False, container=False)
                gr.Image(CENIA_LOGO, elem_classes="logo", width=250, height=80, show_label=False, 
                        show_download_button=False, show_fullscreen_button=False, container=False)

            gr.Markdown("## Bienvenido a **GPTLAS Chat Arena** 🏆")
            gr.Markdown("**Autentícate con tu cuenta de Google para acceder a la plataforma.**")

            gr.Button("🔑 Iniciar sesión con Google", link="/login", variant="primary")

            gr.Markdown("_Tu información está protegida y solo se usará para autenticación._")

    return login_demo

# Iniciar la interfaz del login
login_demo = build_login()

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="session_data",
    max_age=SESSION_LIFETIME_SECONDS,  # Expira después de 10 minutos
    same_site="lax",
    https_only=True  # Cambia a True si usas HTTPS en producción
)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app = gr.mount_gradio_app(app, login_demo, path="/login-demo")