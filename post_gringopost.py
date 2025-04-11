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
        # Esperar y llenar campo de usuario
        logging.info("⏳ Esperando campo de usuario...")
        page.wait_for_selector("input#username", timeout=DEFAULT_TIMEOUT)
        page.fill("input#username", email)

        # Esperar y llenar campo de contraseña
        logging.info("⏳ Esperando campo de contraseña...")
        page.wait_for_selector("input#password", timeout=DEFAULT_TIMEOUT)
        page.fill("input#password", password)

        # Esperar y marcar "Remember Me"
        logging.info("⏳ Esperando checkbox 'Remember Me'...")
        page.wait_for_selector("input#remember_me", state="visible", timeout=DEFAULT_TIMEOUT)
        page.check("input#remember_me")

        # Esperar y hacer clic en el botón de submit
        logging.info("⏳ Esperando botón de submit...")
        submit_button = page.locator("input[name='wp-submit']")
        # Esperamos que el botón esté en el DOM
        submit_button.wait_for(timeout=DEFAULT_TIMEOUT, state="attached")
        # Si no es visible, se intenta hacer scroll para que aparezca en la vista
        if not submit_button.is_visible():
            logging.warning("El botón de submit no es visible, se intenta hacer scroll a la vista.")
            submit_button.scroll_into_view_if_needed()
        logging.info("➡️ Enviando login...")
        submit_button.click()

        # Verificar redirección al dashboard
        logging.info("🔄 Esperando redirección al dashboard...")
        page.wait_for_url(DASHBOARD_URL_PATTERN, timeout=DEFAULT_TIMEOUT)
        logging.info("✅ Login exitoso")
        page.screenshot(path="screenshot_login_success.png")

    except TimeoutError as e:
        logging.error(f"❌ Timeout durante el login: {e}")
        page.screenshot(path="screenshot_login_failed.png")
        raise

def post_service(page: Page):
    logging.info("📤 Simulación de post (implementa lo que necesites aquí)...")
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
