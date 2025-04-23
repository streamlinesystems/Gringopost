#!/usr/bin/env python3
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

# Increase the default timeout to 2 minutes
DEFAULT_TIMEOUT = 120_000  

EMAIL = os.getenv("GRINGO_EMAIL")
PASSWORD = os.getenv("GRINGO_PASSWORD")


def login(page: Page, email: str, password: str, attempts: int = 3):
    logging.info("🌐 Opening login page…")
    page.goto(LOGIN_URL)
    # wait until all network calls settle
    page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)

    for attempt in range(1, attempts + 1):
        try:
            logging.info("🖊️ Login attempt %d/%d", attempt, attempts)

            # Fill username (either #username or #user_login)
            user_field = page.locator("#username, #user_login")
            user_field.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
            user_field.fill(email)

            # Fill password
            pwd_field = page.locator("input#password")
            pwd_field.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
            pwd_field.fill(password)

            # Check "Remember Me" if present
            remember = page.locator("form#loginform input[name='rememberme'], form#loginform input#remember_me")
            if remember.count() == 1:
                remember.check(timeout=DEFAULT_TIMEOUT)
                logging.info("🔒 Remember Me checked")

            # Locate the submit button inside the WP login form
            submit = page.locator(
                "form#loginform input[type='submit'], form#loginform button[type='submit']"
            )
            submit.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
            submit.click()

            # Wait for dashboard URL pattern
            page.wait_for_url(DASHBOARD_URL_PATTERN, timeout=DEFAULT_TIMEOUT)
            logging.info("✅ Login successful on attempt %d", attempt)
            return

        except TimeoutError as e:
            logging.error("❌ Timeout on login attempt %d: %s", attempt, e)
            page.screenshot(path=f"screenshot_login_failed_{attempt}.png")
            if attempt == attempts:
                raise


def create_service_post(page: Page, title: str, description: str, public_contact: str, city: str):
    logging.info("📝 Navigating to new post page…")
    page.goto(NEW_POST_URL)
    page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)

    # Title
    title_fld = page.locator("input[name='post_title']")
    title_fld.wait_for(timeout=DEFAULT_TIMEOUT)
    title_fld.fill(title)

    # Description
    desc_fld = page.locator("textarea[name='post_description']")
    desc_fld.wait_for(timeout=DEFAULT_TIMEOUT)
    desc_fld.fill(description)

    # Public Contact
    contact_fld = page.locator("input[name='public_contact']")
    contact_fld.wait_for(timeout=DEFAULT_TIMEOUT)
    contact_fld.fill(public_contact)

    # City
    city_fld = page.locator("input[name='city']")
    city_fld.wait_for(timeout=DEFAULT_TIMEOUT)
    city_fld.fill(city)

    # Boost/Newsletter: select "None"
    boost = page.locator("input[name='post_boost'][value='None']")
    boost.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
    boost.check()

    # Next
    next_btn = page.locator("button[name='next'], form#postform button:has-text('Next')")
    next_btn.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
    next_btn.click()

    # Review
    review = page.locator("#gf_1067")
    review.wait_for(timeout=DEFAULT_TIMEOUT)

    # Send
    send_btn = page.locator("button[name='send'], form#postform button:has-text('Send')")
    send_btn.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
    send_btn.click()

    # Confirmation
    success = page.locator("div.post-success, .success-message")
    success.wait_for(timeout=DEFAULT_TIMEOUT)
    logging.info("✅ Service post created successfully.")


def run_bot(headless: bool, title: str, desc: str, contact: str, city: str):
    if not EMAIL or not PASSWORD:
        logging.error("❌ Missing GRINGO_EMAIL or GRINGO_PASSWORD env vars")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
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
            login(page, EMAIL, PASSWORD)
            create_service_post(page, title, desc, contact, city)
            logging.info("✅ Bot finished all steps.")
        except Exception:
            logging.exception("❌ Bot encountered an error:")
            sys.exit(1)
        finally:
            context.close()
            browser.close()


def main():
    parser = argparse.ArgumentParser(description="GringoPost Auto-Publisher")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--title",       required=True, help="The post title")
    parser.add_argument("--description", required=True, help="The post description")
    parser.add_argument("--contact",     required=True, help="Public contact info")
    parser.add_argument("--city",        required=True, help="City for the post")
    args = parser.parse_args()

    run_bot(
        headless=args.headless,
        title=args.title,
        desc=args.description,
        contact=args.contact,
        city=args.city
    )


if __name__ == "__main__":
    main()
