import os
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, Depends, Request, HTTPException
from starlette.config import Config
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import gradio as gr

app = FastAPI()

# OAuth settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY")
SESSION_LIFETIME_SECONDS = 60*5

# Set up OAuth
config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

def get_user(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=307, detail="Redirect", headers={"Location": "/login-demo"})
    return user

@app.get('/')
def public(user: dict = Depends(get_user)):
    if user:
        return RedirectResponse(url='/gradio')
    else:
        return RedirectResponse(url='/login-demo')

@app.route('/logout')
async def logout(request: Request):
    request.session.clear()  # Elimina toda la sesión
    return RedirectResponse(url='/login-demo')

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
    
    # Imprime la información relevante
    print(f"Usuario autenticado:")
    print(f"- Nombre: {name}")
    print(f"- Email: {email}")
    print(f"- Foto de perfil: {picture}")
    
    # Guarda el usuario en la sesión
    request.session['user'] = {"name": name, "email": email, "picture": picture}
    return RedirectResponse(url='/')

@app.get("/check-session")
async def check_session(request: Request):
    user = request.session.get("user")
    return {"authenticated": bool(user)}

GPTLAS_LOGO = "https://storage.googleapis.com/public-gptlas-assets/logo-gptlas-2.png"
CENIA_LOGO = "https://www.cenia.cl/wp-content/themes/urantiacoscenia/assets/images/logo_cenia.png"

def build_login():
    with gr.Blocks(css="""
    body {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh; /* Ocupa toda la altura de la ventana */
        margin: 0;
    }
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: auto;
        padding: 20px;
        border-radius: 10px;
        background-color: #1e1e1e; /* Fondo gris oscuro para toda la página */
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
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

            gr.Button("🔑 Iniciar sesión con Google", link="/login", elem_classes="login-button")

            gr.Markdown("_Tu información está protegida y solo se usará para autenticación._")

    return login_demo


# Iniciar la interfaz del login
login_demo = build_login()

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="session_id",
    max_age=SESSION_LIFETIME_SECONDS,  # Expira después de 10 minutos
    same_site="lax",
    https_only=True  # Cambia a True si usas HTTPS en producción
)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app = gr.mount_gradio_app(app, login_demo, path="/login-demo")