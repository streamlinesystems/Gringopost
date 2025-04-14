import os
import sys
import logging
import argparse
from playwright.sync_api import sync_playwright, TimeoutError, Page

# --- Configuración de logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes ---
LOGIN_URL = "https://gringopost.com/wp-login.php"
DASHBOARD_URL_PATTERN = "https://gringopost.com/users/bookmark/"
NEW_POST_URL = "https://gringopost.com/posting-page/services/"
DEFAULT_TIMEOUT = 30000  # 30 segundos

# --- Credenciales desde entorno ---
EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

# --- Funciones ---
def login(page: Page, email: str, password: str):
    logging.info("🌐 Abriendo página de login...")
    page.goto(LOGIN_URL, wait_until="domcontentloaded")

    try:
        # Esperar y llenar campo de usuario
        logging.info("⏳ Esperando campo de usuario...")
        page.wait_for_selector("input#username", timeout=DEFAULT_TIMEOUT)
        page.fill("input#username", email)

        # Esperar y llenar campo de contraseña
        logging.info("⏳ Esperando campo de contraseña...")
        page.wait_for_selector("input#password", timeout=DEFAULT_TIMEOUT)
        page.fill("input#password", password)

        # Esperar y marcar checkbox "Remember Me"
        logging.info("⏳ Esperando checkbox 'Remember Me'...")
        page.wait_for_selector("input#remember_me", state="visible", timeout=DEFAULT_TIMEOUT)
        page.check("input#remember_me")

        # Hacer clic en el botón de login
        logging.info("⏳ Esperando botón de login...")
        # Selector actualizado (conforme al HTML entregado anteriormente)
        submit_button = page.locator("button[name='uwp_login_submit']")
        submit_button.wait_for(timeout=DEFAULT_TIMEOUT, state="attached")
        if not submit_button.is_visible():
            logging.warning("El botón 'Login' no es visible; se intenta hacer scroll a la vista.")
            submit_button.scroll_into_view_if_needed()
        logging.info("➡️ Haciendo clic en el botón 'Login'...")
        submit_button.click()

        # Verificar redirección (si el login es exitoso)
        logging.info("🔄 Esperando redirección al dashboard...")
        page.wait_for_url(DASHBOARD_URL_PATTERN, timeout=DEFAULT_TIMEOUT)
        logging.info("✅ Login exitoso")
        page.screenshot(path="screenshot_login_success.png")

    except TimeoutError as e:
        logging.error(f"❌ Timeout durante el login: {e}")
        page.screenshot(path="screenshot_login_failed.png")
        raise

def create_service_post(page: Page, title: str, description: str,
                        public_contact: str, city: str):
    """
    Crea un post de servicio siguiendo los pasos de la guía.
    Ajusta los selectores según el HTML de tu sitio.
    """
    logging.info("📝 Navegando a la página de creación de post de servicios...")
    page.goto(NEW_POST_URL, wait_until="networkidle")
    
    try:
        # Llenar el campo de título
        logging.info("⏳ Esperando campo de título...")
        # Se asume que el campo de título es un input con el nombre 'post_title'
        page.wait_for_selector("input[name='post_title']", timeout=DEFAULT_TIMEOUT)
        page.fill("input[name='post_title']", title)
        
        # Llenar el campo de descripción
        logging.info("⏳ Esperando campo de descripción...")
        # Se asume que la descripción se ingresa en un textarea con el nombre 'post_description'
        page.wait_for_selector("textarea[name='post_description']", timeout=DEFAULT_TIMEOUT)
        page.fill("textarea[name='post_description']", description)
        
        # Llenar el campo de Public Contact info (opcional)
        logging.info("⏳ Esperando campo de Public Contact info...")
        page.wait_for_selector("input[name='public_contact']", timeout=DEFAULT_TIMEOUT)
        page.fill("input[name='public_contact']", public_contact)
        
        # Llenar el campo de Ciudad
        logging.info("⏳ Esperando campo de Ciudad...")
        page.wait_for_selector("input[name='city']", timeout=DEFAULT_TIMEOUT)
        page.fill("input[name='city']", city)
        
        # Seleccionar la opción "None" en Boost in Newsletter/Post on Facebook
        logging.info("⏳ Seleccionando opción 'None' para Boost/Post en Facebook...")
        # Se asume que es un radio button con el valor "None" y el nombre 'post_boost'
        page.wait_for_selector("input[name='post_boost'][value='None']", timeout=DEFAULT_TIMEOUT)
        page.check("input[name='post_boost'][value='None']")
        
        # Hacer clic en "Next"
        logging.info("➡️ Haciendo clic en 'Next'...")
        page.wait_for_selector("button[name='next']", timeout=DEFAULT_TIMEOUT)
        page.click("button[name='next']")
        
        # Revisar el post (la revisión se muestra en una sección con un ID específico, por ejemplo #gf_1067)
        logging.info("⏳ Esperando página de revisión...")
        page.wait_for_selector("#gf_1067", timeout=DEFAULT_TIMEOUT)
        
        # Hacer clic en "Send"
        logging.info("➡️ Haciendo clic en 'Send'...")
        page.wait_for_selector("button[name='send']", timeout=DEFAULT_TIMEOUT)
        page.click("button[name='send']")
        
        # Esperar que la publicación final se complete (puede aparecer un mensaje o redirección)
        logging.info("⏳ Esperando finalización del post...")
        page.wait_for_selector("#gf_1067", timeout=DEFAULT_TIMEOUT)
        logging.info("✅ Post creado exitosamente")
        page.screenshot(path="screenshot_post_created.png")
        
    except TimeoutError as e:
        logging.error(f"❌ Timeout durante la creación del post: {e}")
        page.screenshot(path="screenshot_post_failed.png")
        raise

def run_bot(headless_mode: bool):
    if not EMAIL or not PASSWORD:
        logging.error("❌ Las variables de entorno GRINGO_EMAIL o GRINGO_PASSWORD no están definidas.")
        sys.exit(1)

    browser = None
    page = None

    with sync_playwright() as p:
        try:
            logging.info(f"🚀 Iniciando Playwright... (headless={headless_mode})")
            browser = p.chromium.launch(headless=headless_mode)
            context = browser.new_context()
            page = context.new_page()

            logging.info("🏁 Iniciando secuencia de login y creación del post...")
            login(page, EMAIL, PASSWORD)
            
            # Definir datos para el post de servicio a crear.
            post_title = "Dra Priscila Matovelle; geriatrics-palliative care"
            post_description = (
                "Hello, dear expats!\n\n"
                "My name is Dr. Priscila Matovelle, and I specialize in geriatrics and palliative care. "
                "I’m originally from Cuenca, where I studied medicine before continuing my training in Spain, where I also earned my Ph.D. in elderly care.\n\n"
                "After years of international experience, I recently returned to Cuenca, and I’m excited to offer high-quality, compassionate medical care to the expat community.\n\n"
                "I understand how challenging it can be to navigate healthcare in a foreign country—I lived in Virginia Beach for a year, so I truly empathize with those challenges.\n\n"
                "Medical Services:\n"
                "– Comprehensive specialized care for adults over 65 years of age.\n"
                "– Pre-surgical frailty assessment and post-surgical follow-up.\n"
                "– Diagnosis and management of acute and chronic diseases such as hypertension, diabetes, thyroid disorders, among others.\n"
                "– Geriatric syndromes: Malnutrition, Dysmobility, Loss of muscle mass, Falls, Incontinence, Polypharmacy, Chronic pain.\n"
                "– Cognitive disorders: Memory loss, dementia/Alzheimer’s disease.\n"
                "– Depression, anxiety, emotional disturbance, Insomnia.\n"
                "– Geriatric and oncological palliative care\n\n"
                "I offer home visits, online or consultations at my office in Hospital Monte Sinaí, Tower I, office 403.\n\n"
                "If you or a loved one need expert care, I’m here to help.\n\n"
                "Contact me at: 098 063 4974\n\n"
                "Looking forward to meeting you and supporting your health and wellness here in Cuenca or anywhere in the world!"
            )
            public_contact = "geriatricaresalud@gmail.com"
            city = "Cuenca"
            
            create_service_post(page, post_title, post_description, public_contact, city)

        except Exception as e:
            logging.exception("❌ Error inesperado durante la ejecución:")
            if page:
                try:
                    page.screenshot(path="screenshot_error.png")
                    logging.info("📸 Screenshot de error tomada.")
                except Exception as ss_error:
                    logging.warning(f"⚠️ No se pudo tomar screenshot del error: {ss_error}")
            raise
        finally:
            if browser:
                browser.close()
                logging.info("🚪 Navegador cerrado.")
            else:
                logging.warning("⚠️ No se cerró el navegador.")

# --- Entrada principal ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bot de GringoPost - Creación de Post de Servicios")
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ejecutar en modo headless (por defecto)"
    )
    args = parser.parse_args()
    run_bot(headless_mode=args.headless)
