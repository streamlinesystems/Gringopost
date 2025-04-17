import os
import sys
import argparse
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Page

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Constants ---
LOGIN_URL = "https://gringopost.com/wp-login.php"
DASHBOARD_URL_PATTERN = "**/users/bookmark*"
NEW_POST_URL = "https://gringopost.com/posting-page/services/"
DEFAULT_TIMEOUT = 60_000  # 60 seconds

# --- Environment Credentials ---
EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")


def login(page: Page, email: str, password: str, attempts: int = 3):
    """
    Logs into GringoPost with robust handling, using correct WordPress selectors.
    """
    logging.info("🌐 Opening login page: %s", LOGIN_URL)
    page.goto(LOGIN_URL)
    page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)

    for attempt in range(1, attempts + 1):
        try:
            # Username
            username_locator = page.locator("#user_login")
            username_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
            username_locator.fill(email)

            # Password
            password_locator = page.locator("#user_pass")
            password_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
            password_locator.fill(password)

            # Remember Me (optional)
            remember_locator = page.locator("input[name='rememberme']")
            if remember_locator.is_visible():
                remember_locator.check()

            # Submit button
            submit_locator = page.locator("input#wp-submit")
            submit_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
            logging.info("➡️ Clicking the login button...")
            submit_locator.click()

            # Wait for dashboard
            logging.info("🔄 Waiting for dashboard redirection...")
            page.wait_for_url(DASHBOARD_URL_PATTERN, timeout=DEFAULT_TIMEOUT)
            logging.info("✅ Login successful on attempt %d", attempt)
            return

        except PlaywrightTimeoutError as e:
            logging.error("❌ Timeout during login attempt %d: %s", attempt, e)
            page.screenshot(path=f"screenshot_login_failed_{attempt}.png")
            if attempt == attempts:
                raise
            logging.info("🔄 Retrying login (attempt %d)", attempt + 1)


def create_service_post(page: Page, title: str, description: str, public_contact: str, city: str):
    """
    Fills and submits the 'service post' form.
    """
    logging.info("📝 Navigating to new post page: %s", NEW_POST_URL)
    page.goto(NEW_POST_URL)
    page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)

    try:
        # Title
        title_locator = page.locator("input[name='post_title']")
        title_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        title_locator.fill(title)

        # Description
        desc_locator = page.locator("textarea[name='post_description']")
        desc_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        desc_locator.fill(description)

        # Public Contact
        contact_locator = page.locator("input[name='public_contact']")
        contact_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        contact_locator.fill(public_contact)

        # City
        city_locator = page.locator("input[name='city']")
        city_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        city_locator.fill(city)

        # Boost/Newsletter
        boost_locator = page.locator("input[name='post_boost'][value='None']")
        boost_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        boost_locator.check()

        # Next
        next_btn = page.locator("button[name='next']")
        next_btn.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        next_btn.click()

        # Review
        review_locator = page.locator("#gf_1067")
        review_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)

        # Send
        send_btn = page.locator("button[name='send']")
        send_btn.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        send_btn.click()

        # Confirmation
        confirm_locator = page.locator("div.post-success")
        confirm_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        logging.info("✅ Service post created successfully.")

    except PlaywrightTimeoutError as e:
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
        logging.error("❌ Missing GRINGO_EMAIL or GRINGO_PASSWORD environment variables.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless_mode)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)

        try:
            logging.info("🚀 Starting Playwright (headless=%s)…", headless_mode)
            login(page, EMAIL, PASSWORD)
            create_service_post(page, title, description, public_contact, city)
            logging.info("✅ Bot finished successfully.")
        except Exception:
            logging.exception("❌ Bot run failure")
            sys.exit(1)
        finally:
            context.close()
            browser.close()
            logging.info("🧹 Browser and context closed.")


def main():
    parser = argparse.ArgumentParser(description="GringoPost Bot")
    parser.add_argument(
        "--headless", action=argparse.BooleanOptionalAction,
        default=True,
        help="Run in headless mode (set to False to see browser)"
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
