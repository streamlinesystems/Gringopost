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
DEFAULT_TIMEOUT = 60000  # 60,000 ms = 60 segundos

# --- Credenciales desde entorno ---
EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

def login(page: Page, email: str, password: str, attempts: int = 3):
    logging.info("🌐 Abriendo página de login...")
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    
    for attempt in range(1, attempts + 1):
        try:
            logging.info("🖊️ Intento %d/%d de login", attempt, attempts)
            # Campo de usuario: prueba primero con input#username, luego con input#user_login
            try:
                page.wait_for_selector("input#username", timeout=DEFAULT_TIMEOUT)
                page.fill("input#username", email)
            except TimeoutError:
                logging.warning("No se encontró 'input#username'; intentando 'input#user_login'...")
                page.wait_for_selector("input#user_login", timeout=DEFAULT_TIMEOUT)
                page.fill("input#user_login", email)

            # Campo de contraseña
            logging.info("⏳ Esperando campo de contraseña...")
            page.wait_for_selector("input#password", timeout=DEFAULT_TIMEOUT)
            page.fill("input#password", password)

            # Checkbox "Remember Me"
            logging.info("⏳ Esperando checkbox 'Remember Me'...")
            # Ajusta este selector según lo que veas en la página (input#remember_me o input[name='rememberme'])
            try:
                page.wait_for_selector("input#remember_me", state="visible", timeout=DEFAULT_TIMEOUT)
                page.check("input#remember_me")
            except TimeoutError:
                logging.warning("No se encontró 'input#remember_me'; intentando 'input[name=\"rememberme\"]'...")
                page.wait_for_selector("input[name='rememberme']", timeout=DEFAULT_TIMEOUT)
                page.check("input[name='rememberme']")

            # Botón de login
            logging.info("⏳ Esperando botón de login...")
            # Verifica con las DevTools el selector real; aquí se usa input[name='wp-submit'] como estándar
            try:
                submit_button = page.locator("input[name='wp-submit']")
                submit_button.wait_for(timeout=DEFAULT_TIMEOUT, state="enabled")
            except TimeoutError:
                logging.warning("No se encontró el botón con 'input[name=\"wp-submit\"]'; intentando otro selector...")
                submit_button = page.locator("button:has-text('Login')")
                submit_button.wait_for(timeout=DEFAULT_TIMEOUT, state="enabled")
            
            if not submit_button.is_visible():
                logging.warning("El botón 'Login' no es visible; se intenta hacer scroll a la vista.")
                submit_button.scroll_into_view_if_needed()
            logging.info("➡️ Haciendo clic en el botón 'Login'...")
            submit_button.click()

            # Espera redirección o confirmación de login
            logging.info("🔄 Esperando redirección al dashboard o aparición de un elemento característico...")
            page.wait_for_url(DASHBOARD_URL_PATTERN, timeout=DEFAULT_TIMEOUT)
            logging.info("✅ Login exitoso en el intento %d", attempt)
            page.screenshot(path="screenshot_login_success.png")
            return

        except TimeoutError as e:
            logging.error("❌ Timeout durante el login en intento %d: %s", attempt, e)
            page.screenshot(path=f"screenshot_login_failed_attempt_{attempt}.png")
            if attempt == attempts:
                raise

def create_service_post(page: Page, title: str, description: str, public_contact: str, city: str):
    logging.info("📝 Navegando a la página de creación de post...")
    page.goto(NEW_POST_URL, wait_until="domcontentloaded")
    
    try:
        # Campo de título
        logging.info("⏳ Esperando campo de título...")
        page.wait_for_selector("input[name='post_title']", timeout=DEFAULT_TIMEOUT)
        page.fill("input[name='post_title']", title)
        
        # Campo de descripción
        logging.info("⏳ Esperando campo de descripción...")
        page.wait_for_selector("textarea[name='post_description']", timeout=DEFAULT_TIMEOUT)
        page.fill("textarea[name='post_description']", description)
        
        # Campo de Public Contact info
        logging.info("⏳ Esperando campo de Public Contact info...")
        page.wait_for_selector("input[name='public_contact']", timeout=DEFAULT_TIMEOUT)
        page.fill("input[name='public_contact']", public_contact)
        
        # Campo de Ciudad
        logging.info("⏳ Esperando campo de Ciudad...")
        page.wait_for_selector("input[name='city']", timeout=DEFAULT_TIMEOUT)
        page.fill("input[name='city']", city)
        
        # Opción Boost/Newsletter - seleccionar "None"
        logging.info("⏳ Seleccionando opción 'None' para Boost/Post en Facebook...")
        page.wait_for_selector("input[name='post_boost'][value='None']", timeout=DEFAULT_TIMEOUT)
        page.check("input[name='post_boost'][value='None']")
        
        # Botón "Next"
        logging.info("➡️ Haciendo clic en 'Next'...")
        # Puedes optar por button:has-text("Next") si es más confiable
        page.wait_for_selector("button[name='next']", timeout=DEFAULT_TIMEOUT)
        page.click("button[name='next']")
        
        # Página de revisión
        logging.info("⏳ Esperando página de revisión...")
        page.wait_for_selector("#gf_1067", timeout=DEFAULT_TIMEOUT)
        
        # Botón "Send"
        logging.info("➡️ Haciendo clic en 'Send'...")
        page.wait_for_selector("button[name='send']", timeout=DEFAULT_TIMEOUT)
        page.click("button[name='send']")
        
        # Esperar confirmación de publicación; ajustar el selector según la interfaz de éxito
        logging.info("⏳ Esperando confirmación de post publicado...")
        # Puedes buscar por texto o un mensaje de éxito en lugar de "#gf_1067" si es más fiable
        page.wait_for_selector("div.post-success", timeout=DEFAULT_TIMEOUT)
        logging.info("✅ Post creado exitosamente")
        page.screenshot(path="screenshot_post_created.png")
        
    except TimeoutError as e:
        logging.error("❌ Timeout durante la creación del post: %s", e)
        page.screenshot(path="screenshot_post_failed.png")
        raise

def run_bot(headless_mode: bool):
    if not EMAIL or not PASSWORD:
        logging.error("❌ Las variables de entorno GRINGO_EMAIL o GRINGO_PASSWORD no están definidas.")
        sys.exit(1)

    with sync_playwright() as p:
        try:
            logging.info("🚀 Iniciando Playwright... (headless=%s)", headless_mode)
            browser = p.chromium.launch(headless=headless_mode)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()

            logging.info("🏁 Iniciando secuencia de login y creación del post...")
            login(page, EMAIL, PASSWORD)
            
            post_title = "Dra Priscila Matovelle; geriatrics-palliative care"
            post_description = (
                "Hello, dear expats!\n\n"
                "My name is Dr. Priscila Matovelle, and I specialize in geriatrics and palliative care. "
                "I’m originally from Cuenca, where I studied medicine before continuing my training in Spain, "
                "where I also earned my Ph.D. in elderly care.\n\n"
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
                    logging.warning("⚠️ No se pudo tomar screenshot del error: %s", ss_error)
            raise
        finally:
            try:
                browser.close()
                logging.info("🚪 Navegador cerrado.")
            except Exception:
                logging.warning("⚠️ No se cerró el navegador.")

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
