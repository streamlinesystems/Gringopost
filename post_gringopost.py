import os
import sys
import argparse
import logging
from playwright.sync_api import sync_playwright, TimeoutError

# Configurar logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

TITLE = "Dra Priscila Matovelle, geriatrics–palliative care"
CITY = "Cuenca"
CONTACT = "geriatricaresalud@gmail.com"

DESCRIPTION = """
Hello, dear expats!

My name is Dr. Priscila Matovelle, and I specialize in Geriatrics and Palliative Care...
[Acorta aquí para brevedad, mantén tu versión completa en producción]
"""

def login(page, email, password):
    logger.info("Navegando a la página de inicio de sesión...")
    page.goto("https://www.gringopost.com/login", timeout=60000)
    
    logger.info("Completando formulario de login...")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')

    logger.info("Esperando confirmación de login...")
    page.wait_for_selector('text=Welcome', timeout=10000)

def post_service(page, title, city, description, contact):
    logger.info("Navegando a página de publicación...")
    page.goto("https://www.gringopost.com/add-post", timeout=60000)
    
    logger.info("Llenando formulario de servicio...")
    page.fill('input[name="title"]', title)
    page.fill('input[name="city"]', city)
    page.fill('textarea[name="description"]', description)
    page.fill('input[name="contact"]', contact)

    logger.info("Publicando servicio...")
    page.click('button[type="submit"]')
    page.wait_for_selector("text=Post successfully submitted", timeout=10000)

def run_bot(headless_mode: bool):
    if not EMAIL or not PASSWORD:
        logger.error("❌ GRINGO_EMAIL o GRINGO_PASSWORD no están definidos.")
        sys.exit(1)

    browser = None
    try:
        with sync_playwright() as p:
            logger.info(f"🚀 Iniciando navegador... (headless: {headless_mode})")
            browser = p.chromium.launch(headless=headless_mode)
            context = browser.new_context()
            page = context.new_page()

            login(page, EMAIL, PASSWORD)
            logger.info("✅ Sesión iniciada correctamente")

            post_service(page, TITLE, CITY, DESCRIPTION, CONTACT)
            logger.info("✅ Publicación completada con éxito")

            page.screenshot(path="screenshot_success.png")
    except TimeoutError as e:
        logger.error(f"⏱️ TimeoutError: {e}")
        if page:
            page.screenshot(path="screenshot_timeout.png")
    except Exception as e:
        logger.error(f"💥 Error inesperado: {e}")
        if 'page' in locals():
            page.screenshot(path="screenshot_error.png")
    finally:
        if browser:
            logger.info("🚪 Cerrando navegador...")
            browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Gringopost Bot")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True, help="Run browser in headless mode")
    args = parser.parse_args()

    run_bot(headless_mode=args.headless)
