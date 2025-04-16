import os
import sys
import argparse
import logging
from playwright.sync_api import sync_playwright, TimeoutError, Page

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Constants ---
LOGIN_URL = "https://gringopost.com/wp-login.php"
DASHBOARD_URL_PATTERN = "**/users/bookmark*"
NEW_POST_URL = "https://gringopost.com/posting-page/services/"
DEFAULT_TIMEOUT = 60_000  # 60,000 ms = 60 seconds

# --- Environment Credentials ---
EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")

def login(page: Page, email: str, password: str, attempts: int = 3):
    """
    Logs into GringoPost with robust handling, supporting alternate selectors.
    """
    logging.info("🌐 Opening login page: %s", LOGIN_URL)
    page.goto(LOGIN_URL)
    for attempt in range(1, attempts + 1):
        try:
            # Username: fallback between "#username" and "#user_login"
            username_locator = page.locator("#username, #user_login")
            username_locator.wait_for()
            username_locator.fill(email)

            # Password
            password_locator = page.locator("input#password")
            password_locator.wait_for()
            password_locator.fill(password)

            # Remember Me checkbox: fallback between input[name='rememberme'] and input#remember_me
            remember_me_locator = page.locator("input[name='rememberme'], input#remember_me")
            remember_me_locator.wait_for(state="visible")
            remember_me_locator.check()

            # Login button: fallback between input[name='wp-submit'] and button with text "Log In"
            submit_locator = page.locator("input[name='wp-submit'], button:has-text('Log In')")
            submit_locator.wait_for(state="visible")
            if not submit_locator.is_enabled():
                raise TimeoutError("Login button found but is not enabled!")

            if not submit_locator.is_visible():
                submit_locator.scroll_into_view_if_needed()
            logging.info("➡️ Clicking the login button...")
            submit_locator.click()

            # Wait for dashboard redirection (or check an element characteristic)
            logging.info("🔄 Waiting for dashboard redirection...")
            page.wait_for_url(DASHBOARD_URL_PATTERN)
            logging.info("✅ Login successful on attempt %d", attempt)
            # Optionally, take a screenshot:
            # page.screenshot(path="screenshot_login_success.png")
            return

        except TimeoutError as e:
            logging.error("❌ Timeout during login attempt %d: %s", attempt, e)
            page.screenshot(path=f"screenshot_login_failed_attempt_{attempt}.png")
            if attempt == attempts:
                raise

def create_service_post(page: Page, title: str, description: str, public_contact: str, city: str):
    """
    Fills and submits the 'service post' form.
    """
    logging.info("📝 Navigating to new post page: %s", NEW_POST_URL)
    page.goto(NEW_POST_URL)
    try:
        # Title
        title_locator = page.locator("input[name='post_title']")
        title_locator.wait_for()
        title_locator.fill(title)

        # Description
        desc_locator = page.locator("textarea[name='post_description']")
        desc_locator.wait_for()
        desc_locator.fill(description)

        # Public Contact info
        contact_locator = page.locator("input[name='public_contact']")
        contact_locator.wait_for()
        contact_locator.fill(public_contact)

        # City
        city_locator = page.locator("input[name='city']")
        city_locator.wait_for()
        city_locator.fill(city)

        # Boost/Newsletter: select "None"
        boost_locator = page.locator("input[name='post_boost'][value='None']")
        boost_locator.wait_for(state="visible")
        boost_locator.check()

        # Next Button
        next_btn = page.locator("button[name='next']")
        next_btn.wait_for(state="visible")
        if not next_btn.is_enabled():
            raise TimeoutError("Next button not enabled!")
        next_btn.click()

        # Review page (verify that the review container is correct)
        review_locator = page.locator("#gf_1067")
        review_locator.wait_for()

        # Send Button
        send_btn = page.locator("button[name='send']")
        send_btn.wait_for(state="visible")
        if not send_btn.is_enabled():
            raise TimeoutError("Send button not enabled!")
        send_btn.click()

        # Confirmation element
        confirmation_locator = page.locator("div.post-success")
        confirmation_locator.wait_for()
        logging.info("✅ Service post created successfully.")

    except TimeoutError as e:
        logging.error("❌ Timeout during post creation: %s", e)
        page.screenshot(path="screenshot_post_failed.png")
        raise
    except Exception as e:
        logging.error("❌ Error during post creation: %s", e)
        page.screenshot(path="screenshot_post_error.png")
        raise

def run_bot(headless_mode: bool, title: str, description: str, public_contact: str, city: str):
    """
    Orchestrates browser automation.
    """
    if not EMAIL or not PASSWORD:
        logging.error("❌ GRINGO_EMAIL or GRINGO_PASSWORD environment variables not set.")
        sys.exit(1)
    with sync_playwright() as p:
        browser = None
        context = None
        try:
            logging.info("🚀 Starting Playwright (headless=%s)…", headless_mode)
            browser = p.chromium.launch(headless=headless_mode)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            page.set_default_timeout(DEFAULT_TIMEOUT)

            login(page, EMAIL, PASSWORD)
            create_service_post(page, title, description, public_contact, city)

            logging.info("✅ Bot finished successfully.")
        except Exception as e:
            logging.error("❌ Bot run failure: %s", e, exc_info=True)
            sys.exit(1)
        finally:
            if context:
                context.close()
                logging.info("🧹 Context closed.")
            if browser:
                browser.close()
                logging.info("🧹 Browser closed.")

def main():
    parser = argparse.ArgumentParser(description="GringoPost Bot")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True, help="Run in headless mode")
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
