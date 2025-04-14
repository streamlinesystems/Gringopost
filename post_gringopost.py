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

        # Esperar y marcar el checkbox "Remember Me"
        logging.info("⏳ Esperando checkbox 'Remember Me'...")
        page.wait_for_selector("input#remember_me", state="visible", timeout=DEFAULT_TIMEOUT)
        page.check("input#remember_me")

        # Esperar y hacer clic en el botón de login (selector actualizado)
        logging.info("⏳ Esperando botón de submit...")
        submit_button = page.locator("button[name='uwp_login_submit']")
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
