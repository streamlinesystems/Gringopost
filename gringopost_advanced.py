import os
import sys
import logging
import argparse
from playwright.sync_api import sync_playwright, TimeoutError, Page, BrowserContext, Browser

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes ---
# Credenciales (leídas desde el entorno)
EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

# URLs
LOGIN_URL = "https://gringopost.com/login"
POSTING_URL = "https://gringopost.com/posting-page/services/"
DASHBOARD_URL_PATTERN = "**/dashboard" # Usamos patrón glob

# Datos del Post
POST_TITLE = "Dra Priscila Matovelle, geriatrics–palliative care"
POST_CITY = "Cuenca"
POST_CONTACT = "geriatricaresalud@gmail.com"
POST_DESCRIPTION = """
Hello, dear expats!

My name is Dr. Priscila Matovelle, and I specialize in Geriatrics and Palliative Care. I’m originally from Cuenca, where I studied medicine before continuing my training in Spain, where I also earned my Ph.D. in elderly care.

After years of international experience, I recently returned to Cuenca, and I’m excited to offer high-quality, compassionate medical care to the expat community. 

I understand how challenging it can be to navigate healthcare in a foreign country—I lived in Virginia Beach for a year, so I truly empathize with those challenges.

Medical Services:
– Comprehensive specialized care for adults over 65 years of age.
– Pre-surgical frailty assessment and post-surgical follow-up.
– Diagnosis and management of acute and chronic diseases such as hypertension, diabetes, thyroid disorders, among others.
– Geriatric syndromes: Malnutrition, dysmobility, loss of muscle mass, falls, incontinence, polypharmacy, chronic pain.
– Cognitive disorders: Memory loss, dementia/Alzheimer’s disease.
– Depression, anxiety, emotional disturbance, Insomnia.
– Geriatric and oncological palliative care

I offer home visits, online or consultations at my office in Hospital Monte Sinaí, Tower I, office 403. 

If you or a loved one need expert care, I’m here to help. 

Contact me at: 098 063 4974

Looking forward to meeting you and supporting your health and wellness here in Cuenca or anywhere in the world!
"""

# Timeouts (en milisegundos)
DEFAULT_TIMEOUT = 10000
LOGIN_REDIRECT_TIMEOUT = 15000
CONFIRMATION_TIMEOUT = 10000

# --- Funciones Auxiliares ---

def login(page: Page, email: str, password: str):
    """Navega a la página de login, rellena credenciales y envía."""
    logging.info("🌐 Navegando a la página de login: %s", LOGIN_URL)
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    
    logging.info("⏳ Esperando campo de usuario...")
    page.wait_for_selector("input#username", timeout=DEFAULT_TIMEOUT)

    logging.info("✏️ Rellenando formulario de login...")
    page.fill("input#username", email)
    # Usar name='pwd' está bien si no hay ID, pero #id es preferible
    page.fill("input[name='pwd']", password) 
    page.check("input[name='rememberme']")
    
    logging.info("➡️ Enviando formulario de login...")
    page.click("input[name='wp-submit']")

    logging.info("⏳ Esperando redirección post-login a %s...", DASHBOARD_URL_PATTERN)
    page.wait_for_url(DASHBOARD_URL_PATTERN, timeout=LOGIN_REDIRECT_TIMEOUT)
    logging.info("✅ Login exitoso.")

def post_service(page: Page, title: str, description: str, contact: str, city: str):
    """Navega a la página de publicación y rellena los detalles del servicio."""
    logging.info("📄 Navegando al formulario de publicación: %s", POSTING_URL)
    page.goto(POSTING_URL, wait_until="domcontentloaded")

    logging.info("📝 Rellenando campos del post...")
    # Esperar que el primer campo esté visible/editable puede añadir robustez
    page.locator('input[name="postTitle"]').wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
    
    page.fill('input[name="postTitle"]', title)
    page.fill('textarea[name="postBody"]', description)
    page.fill('input[name="postEmail"]', contact)
    page.fill('input[name="postCity"]', city)

    # Selector potencialmente frágil: input[value="none"]
    # Si hay problemas, inspeccionar el HTML para un selector más específico 
    # (ID, name, o asociado a una etiqueta). Por ahora, lo mantenemos.
    logging.info("🔘 Seleccionando opción 'none' (revisar si es necesario)...")
    page.check('input[value="none"]') # Asegúrate que este checkbox/radio es el correcto

    logging.info("➡️ Haciendo clic en 'NEXT'...")
    # Usar page.locator es una alternativa moderna, pero page.click funciona bien
    page.locator('button:has-text("NEXT")').click()

    logging.info("⏳ Esperando botón 'Send'...")
    send_button = page.locator('button:has-text("Send")')
    send_button.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)

    logging.info("📤 Publicando...")
    send_button.click()

    # Verificar mensaje de éxito
    try:
        confirmation_locator = page.locator("text=Thank you for your post")
        confirmation_locator.wait_for(state="visible", timeout=CONFIRMATION_TIMEOUT)
        logging.info("✅ Confirmación: el post fue enviado correctamente.")
        page.screenshot(path="post_success.png")
    except TimeoutError:
        logging.warning("⚠️ No se detectó mensaje de confirmación esperado.")
        page.screenshot(path="post_no_confirmation.png")


def run_bot(headless_mode: bool):
    """Función principal que orquesta el bot."""
    if not EMAIL or not PASSWORD:
        logging.error("❌ ERROR: GRINGO_EMAIL y GRINGO_PASSWORD deben estar definidos en las variables de entorno.")
        sys.exit(1)

    browser: Browser | None = None
    context: BrowserContext | None = None
    page: Page | None = None

    try:
        with sync_playwright() as p:
            logging.info(f"🚀 Iniciando navegador... (Headless: {headless_mode})")
            browser = p.chromium.launch(headless=headless_mode)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" # Ejemplo de User Agent
            )
            page = context.new_page()
            
            # Login
            login(page, EMAIL, PASSWORD)
            
            # Publicar Servicio
            post_service(page, POST_TITLE, POST_DESCRIPTION, POST_CONTACT, POST_CITY)

    except TimeoutError as e:
        logging.error(f"❌ Timeout al esperar un elemento o navegación: {e}")
        if page:
            page.screenshot(path="timeout_error.png")
    except Exception as e:
        logging.exception(f"❌ Error inesperado durante la ejecución del bot:") # logging.exception incluye traceback
        if page:
            page.screenshot(path="unexpected_error.png")
    finally:
        if browser:
            logging.info("🚪 Cerrando navegador...")
            browser.close() # Cierra el navegador y todos sus contextos/páginas

# --- Punto de Entrada ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bot para publicar en GringoPost.")
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction, # Permite --headless o --no-headless
        default=True, # Headless por defecto
        help="Ejecutar en modo headless (sin interfaz gráfica) o no."
    )
    args = parser.parse_args()

    run_bot(headless_mode=args.headless)
