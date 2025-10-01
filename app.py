import streamlit as st
import google.generativeai as genai
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from PIL import Image
import io

# --- Configuración de la Página ---
st.set_page_config(layout="wide", page_title="VibeBoard AI")

# --- Carga de Claves Secretas desde Streamlit Cloud ---
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
STABILITY_API_KEY = st.secrets.get("STABILITY_API_KEY")

# --- Configuración de los Clientes de IA ---
gemini_model = None
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Error al configurar Google Gemini. Revisa tu clave secreta. Error: {e}")

stability_api = None
if STABILITY_API_KEY:
    try:
        stability_api = client.StabilityInference(key=STABILITY_API_KEY, verbose=True, engine="stable-diffusion-xl-1024-v1-0")
    except Exception as e:
        st.error(f"Error al configurar Stability AI. Revisa tu clave secreta. Error: {e}")

# --- Funciones de la IA ---
def generate_storyboard_text(prompt_usuario):
    if not gemini_model:
        return "Error: El cliente de Gemini no está configurado."
    system_prompt = "Eres VibeBoard AI, un director creativo experto en videos virales..." # (Aquí va el resto de tu prompt detallado)
    try:
        response = gemini_model.generate_content(system_prompt + " Idea: " + prompt_usuario)
        return response.text
    except Exception as e:
        return f"Error al contactar a Gemini: {e}"

def generate_image(prompt_imagen):
    if not stability_api:
        return None
    try:
        answers = stability_api.generate(prompt=prompt_imagen)
        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.type == generation.ARTIFACT_IMAGE:
                    return Image.open(io.BytesIO(artifact.binary))
        return None
    except Exception as e:
        st.error(f"Error al contactar a Stability AI: {e}")
        return None

# --- Interfaz de Usuario ---
st.title("VibeBoard AI ✨")
st.subheader("Tu Director Creativo con Inteligencia Artificial")
user_idea = st.text_area("Escribe aquí tu idea para un video corto...", height=100)

if st.button("Crear Mi Video Viral", type="primary"):
    if not GOOGLE_API_KEY or not STABILITY_API_KEY:
        st.error("ERROR: No se encontraron las claves de API. Ve a 'Manage app' -> 'Secrets' y configúralas.")
    elif user_idea:
        storyboard_text = generate_storyboard_text(user_idea)
        if storyboard_text and "Error:" not in storyboard_text:
            st.divider()
            st.subheader("🎬 ¡Tu Storyboard está listo!")
            scenes = storyboard_text.split("---")
            for i, scene_text in enumerate(scenes):
                st.markdown(scene_text.strip())
                if "PROMPT DE IMAGEN:" in scene_text:
                    try:
                        image_prompt = scene_text.split("PROMPT DE IMAGEN:")[1].strip()
                        with st.spinner(f"🎨 Generando imagen para la escena {i+1}..."):
                            image = generate_image(image_prompt)
                        if image:
                            st.image(image, caption=f"Visualización para la escena {i+1}", use_column_width=True)
                    except IndexError:
                        st.warning("No se pudo extraer el prompt de la imagen para esta escena.")
        elif storyboard_text:
            st.error(storyboard_text)
    else:
        st.warning("Por favor, introduce una idea.")
