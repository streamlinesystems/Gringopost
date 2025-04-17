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
LOGIN_URL            = "https://gringopost.com/wp-login.php"
DASHBOARD_URL_PATTERN= "**/users/bookmark*"
NEW_POST_URL         = "https://gringopost.com/posting-page/services/"
DEFAULT_TIMEOUT      = 60_000  # 60 seconds

# --- Environment Credentials ---
EMAIL    = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")


def login(page: Page, email: str, password: str, attempts: int = 3):
    """
    Logs into GringoPost by:
     1. Navigating to the login form
     2. Dismissing any banners (if present)
     3. Filling in username/password via multiple fallback selectors
     4. Clicking the red LOGIN button
    """
    logging.info("🌐 Opening login page: %s", LOGIN_URL)
    page.goto(LOGIN_URL)
    page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)

    # (Optional) click the top‑nav grey Login button if your theme hides the form by default
    try:
        nav_login = page.locator("a:has-text('Log in'), a.login-link")
        nav_login.first.click(timeout=5_000)
        logging.info("🔑 Clicked top‑nav Log in")
    except PlaywrightTimeoutError:
        pass

    for attempt in range(1, attempts + 1):
        try:
            # 1) Username / Email field
            username_locator = page.locator(
                "input[placeholder*='Username or Email'], "
                "#user_login, "
                "input[name='log']"
            )
            username_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
            username_locator.fill(email)

            # 2) Password field
            password_locator = page.locator(
                "input[placeholder*='Password'], "
                "#user_pass, "
                "input[name='pwd']"
            )
            password_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
            password_locator.fill(password)

            # 3) Remember Me (if shown)
            try:
                remember = page.locator("input[type='checkbox']")
                if remember.is_visible():
                    remember.check()
                    logging.info("✔️ Checked Remember Me")
            except PlaywrightTimeoutError:
                pass

            # 4) The red LOGIN button
            submit_locator = page.locator(
                "button[type='submit'], "
                "button:has-text('LOGIN'), "
                "input#wp-submit"
            )
            submit_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
            logging.info("➡️ Clicking the LOGIN button…")
            submit_locator.click()

            # 5) Wait for dashboard
            logging.info("🔄 Waiting for dashboard redirect…")
            page.wait_for_url(DASHBOARD_URL_PATTERN, timeout=DEFAULT_TIMEOUT)
            logging.info("✅ Login successful on attempt %d", attempt)
            return

        except PlaywrightTimeoutError as e:
            logging.error("❌ Timeout on login attempt %d: %s", attempt, e)
            page.screenshot(path=f"screenshot_login_failed_attempt_{attempt}.png")
            if attempt == attempts:
                raise
            logging.info("🔄 Retrying (attempt %d)…", attempt + 1)


def create_service_post(page: Page, title: str, description: str, public_contact: str, city: str):
    """
    Fills and submits the 'service post' form.
    (unchanged from before)
    """
    logging.info("📝 Navigating to new post page: %s", NEW_POST_URL)
    page.goto(NEW_POST_URL)
    page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)

    try:
        title_locator = page.locator("input[name='post_title']")
        title_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        title_locator.fill(title)

        desc_locator = page.locator("textarea[name='post_description']")
        desc_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        desc_locator.fill(description)

        contact_locator = page.locator("input[name='public_contact']")
        contact_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        contact_locator.fill(public_contact)

        city_locator = page.locator("input[name='city']")
        city_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        city_locator.fill(city)

        boost_locator = page.locator("input[name='post_boost'][value='None']")
        boost_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        boost_locator.check()

        next_btn = page.locator("button[name='next']")
        next_btn.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        next_btn.click()

        review_locator = page.locator("#gf_1067")
        review_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)

        send_btn = page.locator("button[name='send']")
        send_btn.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        send_btn.click()

        confirmation_locator = page.locator("div.post-success")
        confirmation_locator.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        logging.info("✅ Service post created successfully.")

    except Exception as e:
        logging.error("❌ Error during post creation: %s", e)
        page.screenshot(path="screenshot_post_error.png")
        raise


def run_bot(headless_mode: bool, title: str, description: str, public_contact: str, city: str):
    """
    Orchestrates the full browser automation.
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
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction,
                        default=True, help="Run in headless mode")
    parser.add_argument("--title",       required=True, help="Post title")
    parser.add_argument("--description", required=True, help="Post description")
    parser.add_argument("--contact",     required=True, help="Public contact info")
    parser.add_argument("--city",        required=True, help="City for the post")
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
