import os
import sys
import argparse
import logging
from playwright.sync_api import sync_playwright, TimeoutError, Page

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
LOGIN_URL = "https://gringopost.com/wp-login.php"
DASHBOARD_URL_PATTERN = "**/users/bookmark*"
NEW_POST_URL = "https://gringopost.com/posting-page/services/"
DEFAULT_TIMEOUT = 60_000

EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

def login(page: Page, email: str, password: str, attempts: int = 3):
    logging.info("🌐 Opening login page…")
    page.goto(LOGIN_URL)

    for attempt in range(1, attempts + 1):
        try:
            # Username (fallback on #username or #user_login)
            username_locator = page.locator("#username, #user_login")
            username_locator.wait_for(timeout=DEFAULT_TIMEOUT)
            username_locator.fill(email)

            # Password
            password_locator = page.locator("input#password")
            password_locator.wait_for(timeout=DEFAULT_TIMEOUT)
            password_locator.fill(password)

            # —— FIXED: target only the actual Remember Me checkbox by its ID
            remember = page.locator("input#remember_me")
            if remember.is_visible():
                remember.check()

            # Login button (fallback on input or a button with text)
            submit_locator = page.locator(
                "input[name='wp-submit'], button:has-text('Log In')"
            )
            submit_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
            if not submit_locator.is_enabled():
                raise TimeoutError("Login button not enabled!")
            submit_locator.click()

            # Wait for dashboard
            page.wait_for_url(DASHBOARD_URL_PATTERN, timeout=DEFAULT_TIMEOUT)
            logging.info("✅ Login successful on attempt %d", attempt)
            return

        except TimeoutError as e:
            logging.error("❌ Timeout during login attempt %d: %s", attempt, e)
            if attempt == attempts:
                raise

def create_service_post(page: Page, title: str, description: str, public_contact: str, city: str):
    logging.info("📝 Navigating to new post page…")
    page.goto(NEW_POST_URL)

    # Title
    title_loc = page.locator("input[name='post_title']")
    title_loc.wait_for(timeout=DEFAULT_TIMEOUT)
    title_loc.fill(title)

    # Description
    desc_loc = page.locator("textarea[name='post_description']")
    desc_loc.wait_for(timeout=DEFAULT_TIMEOUT)
    desc_loc.fill(description)

    # Public Contact
    contact_loc = page.locator("input[name='public_contact']")
    contact_loc.wait_for(timeout=DEFAULT_TIMEOUT)
    contact_loc.fill(public_contact)

    # City
    city_loc = page.locator("input[name='city']")
    city_loc.wait_for(timeout=DEFAULT_TIMEOUT)
    city_loc.fill(city)

    # Boost/Newsletter = None
    boost_loc = page.locator("input[name='post_boost'][value='None']")
    boost_loc.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
    boost_loc.check()

    # Next
    next_btn = page.locator("button[name='next']")
    next_btn.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
    if not next_btn.is_enabled():
        raise TimeoutError("Next button not enabled!")
    next_btn.click()

    # Review
    review_loc = page.locator("#gf_1067")
    review_loc.wait_for(timeout=DEFAULT_TIMEOUT)

    # Send
    send_btn = page.locator("button[name='send']")
    send_btn.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
    if not send_btn.is_enabled():
        raise TimeoutError("Send button not enabled!")
    send_btn.click()

    # Confirmation
    confirm_loc = page.locator("div.post-success")
    confirm_loc.wait_for(timeout=DEFAULT_TIMEOUT)
    logging.info("✅ Service post created successfully.")

def run_bot(headless_mode: bool, title: str, description: str, public_contact: str, city: str):
    if not EMAIL or not PASSWORD:
        logging.error("❌ GRINGO_EMAIL or GRINGO_PASSWORD not set.")
        sys.exit(1)

    with sync_playwright() as p:
        logging.info("🚀 Starting Playwright (headless=%s)…", headless_mode)
        browser = p.chromium.launch(headless=headless_mode)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)

        try:
            login(page, EMAIL, PASSWORD)
            create_service_post(page, title, description, public_contact, city)
            logging.info("✅ Bot finished successfully.")
        except Exception as e:
            logging.error("❌ Bot run failure: %s", e, exc_info=True)
            sys.exit(1)
        finally:
            context.close()
            browser.close()

def main():
    parser = argparse.ArgumentParser(description="GringoPost Bot")
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run in headless mode"
    )
    parser.add_argument("--title", required=True, help="Post title")
    parser.add_argument("--description", required=True, help="Post description")
    parser.add_argument("--contact", required=True, help="Public contact info")
    parser.add_argument("--city", required=True, help="City for the post")
    args = parser.parse_args()

    run_bot(
        headless_mode=args.headless,
        title=args.title,
        description=args.description,
        public_contact=args.contact,
        city=args.city
    )

if __name__ == "__main__":
    main()
