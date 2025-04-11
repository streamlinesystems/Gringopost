from playwright.sync_api import sync_playwright, TimeoutError
import os
import sys

EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

TITLE = "Dra Priscila Matovelle, geriatrics–palliative care"
CITY = "Cuenca"
CONTACT = "geriatricaresalud@gmail.com"

DESCRIPTION = """
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

def run_bot(playwright):
    if not EMAIL or not PASSWORD:
        print("❌ ERROR: GRINGO_EMAIL y GRINGO_PASSWORD no están definidos.")
        sys.exit(1)

    print("🚀 Iniciando navegador...")
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Aquí puedes agregar la lógica para login y post
    page.goto("https://gringopost.com/login")

    # Cierra el navegador al final
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_bot(playwright)
