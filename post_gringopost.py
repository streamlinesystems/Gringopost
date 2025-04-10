from playwright.sync_api import sync_playwright
import os
import time

EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

TITLE = "Dra Priscila Matovelle, geriatrics–palliative care"
CITY = "Cuenca"
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

geriatricaresalud@gmail.com
"""

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://gringopost.com/login")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PASSWORD)
        page.click('input[value="Login"]')
        page.wait_for_timeout(3000)

        page.goto("https://gringopost.com/posting-page/services/")
        page.fill('input[name="postTitle"]', TITLE)
        page.fill('textarea[name="postBody"]', DESCRIPTION)
        page.fill('input[name="postCity"]', CITY)

        page.click('input[value="none"]')  # Boost option: none
        page.click('button:has-text("NEXT")')

        print("✅ Post submitted successfully!")
        browser.close()

if __name__ == "__main__":
    run_bot()
