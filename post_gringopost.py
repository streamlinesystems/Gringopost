from playwright.sync_api import sync_playwright, Playwright, expect, TimeoutError as PlaywrightTimeoutError
import os
import sys

# --- Configuración ---
EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

TITLE = "Dra Priscila Matovelle, geriatrics–palliative care"
CITY = "Cuenca"
CONTACT = "geriatricaresalud@gmail.com"
DESCRIPTION = """Hello, dear expats!

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

# --- Selectores robustos y URLS ---
LOGIN_URL = "https://gringopost.com/login"
POSTING_URL = "https://gringopost.com/posting-page/services/"

def run_bot(playwright: Playwright):
    if not EMAIL or not PASSWORD:
        print("❌ GRINGO_EMAIL o GRINGO_PASSWORD no configurados como secretos.")
        sys.exit(1)

    browser = None
    try:
        print("🚀 Lanzando navegador...")
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print(f"🔐 Abriendo página de login: {LOGIN_URL}")
        page.goto(LOGIN_URL, wait_until="networkidle", timeout=60000)

        print("✏️ Llenando formulario de login...")
        page.fill('input[name="log"]', EMAIL)
        page.fill('input[name="pwd"]', PASSWORD)
        page.check('input[name="rememberme"]')
        page.click('input[name="wp-submit"]')

        print("✅ Login enviado. Abriendo formulario de publicación...")
        page.goto(POSTING_URL, wait_until="networkidle", timeout=60000)

        print("📝 Completando campos del formulario...")
        page.fill('input[name="postTitle"]', TITLE)
        page.fill('textarea[name="postBody"]', DESCRIPTION)
        page.fill('input[name="postEmail"]', CONTACT)
        page.fill('input[name="postCity"]', CITY)
        page.click('input[value="none"]')  # Boost none

        print("➡️ Clic en NEXT")
        page.click('button:has-text("NEXT")')

        print("⏳ Esperando botón 'Send'...")
        send_button = page.locator('button:has-text("Send")')
        send_button.wait_for(state="visible", timeout=20000)

        print("📤 Enviando publicación...")
        send_button.click()

        print("✅ Publicación enviada con éxito (esperado). Revisa manualmente si se publicó.")
        page.screenshot(path="screenshot_done.png")

    except PlaywrightTimeoutError as e:
        print(f"❌ Timeout: {e}")
        page.screenshot(path="timeout_error.png")

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        page.screenshot(path="unexpected_error.png")

    finally:
        if browser:
            print("🧹 Cerrando navegador...")
            browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_bot(playwright)
