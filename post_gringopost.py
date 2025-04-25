import os
import sys
import argparse
import logging
from playwright.sync_api import sync_playwright, TimeoutError, Page

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
LOGIN_URL               = "https://gringopost.com/wp-login.php"
DASHBOARD_URL_PATTERN   = "**/users/bookmark*"
NEW_POST_URL            = "https://gringopost.com/posting-page/services/"
DEFAULT_TIMEOUT         = 60_000  # ms

EMAIL    = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

def login(page: Page, email: str, password: str, attempts: int = 3):
    logging.info("🌐 Opening login page…")
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    for attempt in range(1, attempts + 1):
        try:
            logging.info("🖊️  Login attempt %d/%d", attempt, attempts)

            # fill username
            page.locator("#username, #user_login").wait_for(timeout=DEFAULT_TIMEOUT)
            page.fill("#username, #user_login", email)

            # fill password
            page.locator("input#password").wait_for(timeout=DEFAULT_TIMEOUT)
            page.fill("input#password", password)

            # remember-me checkbox
            page.locator("input[name='rememberme'], input#remember_me")\
                .wait_for(state="visible", timeout=DEFAULT_TIMEOUT)\
                .check()

            # **updated** login button selector:
            submit = page.locator(
                "input[name='wp-submit'], button[name='uwp_login_submit'], button:has-text('Login')"
            )
            submit.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
            if not submit.is_enabled():
                raise TimeoutError("Login button found but not enabled")
            submit.click()

            # wait for dashboard
            page.wait_for_url(DASHBOARD_URL_PATTERN, timeout=DEFAULT_TIMEOUT)
            logging.info("✅ Login successful on attempt %d", attempt)
            return

        except TimeoutError as e:
            logging.error("❌ Timeout on login attempt %d: %s", attempt, e)
            if attempt == attempts:
                raise

def create_service_post(page: Page, title: str, description: str, public_contact: str, city: str):
    logging.info("📝 Navigating to new post page…")
    page.goto(NEW_POST_URL, wait_until="domcontentloaded")

    # title
    page.locator("input[name='post_title']").wait_for(timeout=DEFAULT_TIMEOUT)
    page.fill("input[name='post_title']", title)

    # description
    page.locator("textarea[name='post_description']").wait_for(timeout=DEFAULT_TIMEOUT)
    page.fill("textarea[name='post_description']", description)

    # contact
    page.locator("input[name='public_contact']").wait_for(timeout=DEFAULT_TIMEOUT)
    page.fill("input[name='public_contact']", public_contact)

    # city
    page.locator("input[name='city']").wait_for(timeout=DEFAULT_TIMEOUT)
    page.fill("input[name='city']", city)

    # boost = None
    page.locator("input[name='post_boost'][value='None']")\
        .wait_for(state="visible", timeout=DEFAULT_TIMEOUT)\
        .check()

    # next
    next_btn = page.locator("button[name='next']")
    next_btn.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
    if not next_btn.is_enabled():
        raise TimeoutError("Next button not enabled")
    next_btn.click()

    # review
    page.locator("#gf_1067").wait_for(timeout=DEFAULT_TIMEOUT)

    # send
    send_btn = page.locator("button[name='send']")
    send_btn.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
    if not send_btn.is_enabled():
        raise TimeoutError("Send button not enabled")
    send_btn.click()

    # confirmation
    page.locator("div.post-success").wait_for(timeout=DEFAULT_TIMEOUT)
    logging.info("✅ Service post created successfully.")

def run_bot(headless: bool, title: str, description: str, contact: str, city: str):
    if not EMAIL or not PASSWORD:
        logging.error("❌ Missing GRINGO_EMAIL or GRINGO_PASSWORD in env")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx     = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width":1280, "height":720}
        )
        page = ctx.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)

        try:
            login(page, EMAIL, PASSWORD)
            create_service_post(page, title, description, contact, city)
            logging.info("🚀 Bot finished successfully.")
        except Exception:
            logging.exception("❌ Bot encountered an error")
            sys.exit(1)
        finally:
            ctx.close()
            browser.close()

def main():
    parser = argparse.ArgumentParser(description="GringoPost Auto-Publisher")
    parser.add_argument("--headless",    action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--title",       required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--contact",     required=True)
    parser.add_argument("--city",        required=True)
    args = parser.parse_args()

    run_bot(args.headless, args.title, args.description, args.contact, args.city)

if __name__ == "__main__":
    main()
