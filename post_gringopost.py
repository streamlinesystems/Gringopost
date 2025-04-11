from playwright.sync_api import sync_playwright, TimeoutError
import os
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

TITLE = "Dra Priscila Matovelle, geriatrics–palliative care"
CITY = "Cuenca"
CONTACT = "geriatricaresalud@gmail.com"

DESCRIPTION = """..."""  # Aquí sigue tu descripción completa

def run_bot(headless_mode: bool):
    if not EMAIL or not PASSWORD:
        logger.error("❌ GRINGO_EMAIL y GRINGO_PASSWORD no están definidos.")
        sys.exit(1)

    browser = None
    page = None

    try:
        with sync_playwright() as p:
            logger.info(f"🚀 Iniciando navegador... (headless: {headless_mode})")
            browser = p.chromium.launch(headless=headless_mode)
            context = browser.new_context()
            page = context.new_page()

            logger.info("🌐 Navegando a la página de inicio de sesión...")
            page.goto("https://gringopost.com/login", timeout=30000)

            logger.info("⏳ Esperando campo de email...")
            page.wait_for_selector('input[name="email"]', timeout=10000)

            logger.info("✍️ Completando formulario de login...")
            page.fill('input[name="email"]', EMAIL)
            page.fill('input[name="password"]', PASSWORD)
            page.click('button[type="submit"]')

            page.wait_for_selector("a[href='/post-service']", timeout=10000)
            logger.info("✅ Login exitoso.")

            # Aquí seguiría tu código para el post...

            page.screenshot(path="screenshot_success.png")

    except TimeoutError as e:
        logger.error(f"⏱️ TimeoutError: {e}")
        if page:
            try:
                page.screenshot(path="screenshot_timeout.png")
            except Exception as inner_e:
                logger.warning(f"No se pudo capturar screenshot de timeout: {inner_e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Error inesperado: {str(e)}")
        if page:
            try:
                page.screenshot(path="screenshot_error.png")
            except Exception as inner_e:
                logger.warning(f"No se pudo capturar screenshot de error: {inner_e}")
        sys.exit(1)
    finally:
        if browser:
            try:
                logger.info("🚪 Cerrando navegador...")
                browser.close()
            except Exception as e:
                logger.warning(f"No se pudo cerrar el navegador: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True
    )
    args = parser.parse_args()
    run_bot(headless_mode=args.headless)
