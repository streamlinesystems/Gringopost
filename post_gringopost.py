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
DEFAULT_TIMEOUT = 30000  # 30 segundos

# --- Credenciales desde entorno ---
EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

# --- Funciones ---
def login(page: Page, email: str, password: str):
    logging.info("🌐 Abriendo página de login...")
    page.goto(LOGIN_URL, wait_until="domcontentloaded")

    try:
        # Esperar campo de usuario
        logging.info("⏳ Esperando campo de usuario...")
        page.wait_for_selector("input#username", timeout=DEFAULT_TIMEOUT)

        # Esperar campo de contraseña
        logging.info("⏳ Esperando campo de contraseña...")
        page.wait_for_selector("input#password", timeout=DEFAULT_TIMEOUT)

        # Esperar checkbox Remember Me
        logging.info("⏳ Esperando checkbox 'Remember Me'...")
        page.wait_for_selector("input[name='rememberme']", timeout=DEFAULT_TIMEOUT)

        # Esperar botón de submit (visible)
        logging.info("⏳ Esperando botón de submit...")
        submit_button = page.locator("input[name='wp-submit']")
        submit_button.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)

        # Llenar formulario
        logging.info("✏️ Rellenando formulario de login...")
        page.fill("input#username", email)
        page.fill("input#password", password)
        page.check("input[name='rememberme']")

        # Verificar si el botón está habilitado y hacer clic
        if submit_button.is_enabled():
            logging.info("➡️ Enviando login...")
            submit_button.click()
        else:
            logging.error("⚠️ Botón de login visible pero no habilitado")
            page.screenshot(path="screenshot_submit_disabled.png")
            raise Exception("Botón de login no habilitado")

        # Esperar redirección al dashboard
        page.wait_for_url(DASHBOARD_URL_PATTERN, timeout=DEFAULT_TIMEOUT)
        logging.info("✅ Login exitoso")
        page.screenshot(path="screenshot_login_success.png")

    except TimeoutError as e:
        logging.error(f"❌ Timeout durante el login: {e}")
        page.screenshot(path="screenshot_login_failed.png")
        raise

def post_service(page: Page):
    logging.info("📤 Simulación de post (a implementar)...")
    page.screenshot(path="screenshot_post_done.png")

def run_bot(headless_mode: bool):
    if not EMAIL or not PASSWORD:
        logging.error("❌ Variables de entorno GRINGO_EMAIL o GRINGO_PASSWORD no están definidas.")
        sys.exit(1)

    browser = None
    page = None

    with sync_playwright() as p:
        try:
            logging.info(f"🚀 Iniciando Playwright... (headless={headless_mode})")
            browser = p.chromium.launch(headless=headless_mode)
            context = browser.new_context()
            page = context.new_page()

            logging.info("🏁 Iniciando secuencia de login y post...")
            login(page, EMAIL, PASSWORD)
            post_service(page)

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
    parser = argparse.ArgumentParser(description="Bot de GringoPost")
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ejecutar en modo headless (por defecto)"
    )
    args = parser.parse_args()
    run_bot(headless_mode=args.headless)
