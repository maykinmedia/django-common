"""
Test the behaviour of the API landing page.

Tests aimed at accessibility and correct functioning of the tabs javascript and block
overrides for downstream projects.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="function", autouse=True)
def before_each_after_each(live_server, page: Page):
    test_page_url = f"{live_server.url}/api/index/"
    page.goto(test_page_url)
    marker = page.get_by_role("heading", name="Testapp API")
    expect(marker).to_be_visible()
    yield


def test_content_tabs_initial_load(page: Page):
    # Initially, the Dutch tab should be focused and the English one visible
    dutch_tab = page.get_by_role("tab", name="Nederlands", selected=True)
    expect(dutch_tab).to_be_visible()
    english_tab = page.get_by_role("tab", name="English", selected=False)
    expect(english_tab).to_be_visible()

    dutch_tab_panel = page.get_by_role("tabpanel", name="Nederlands")
    expect(dutch_tab_panel).to_be_visible()
    expect(dutch_tab_panel).to_have_text("Dutch Content")

    english_tab_panel = page.get_by_role("tabpanel", name="English")
    expect(english_tab_panel).not_to_be_visible()


def test_activate_english_content(page: Page):
    english_tab = page.get_by_role("tab", name="English", selected=False)
    expect(english_tab).to_be_visible()

    english_tab.click()

    english_tab_panel = page.get_by_role("tabpanel", name="English")
    expect(english_tab_panel).to_be_visible()
    expect(english_tab_panel).to_have_text("English Content")


def test_keyboard_navigation_tabs(page: Page):
    # Focus the first tab
    page.keyboard.press("Tab")
    dutch_tab = page.get_by_role("tab", name="Nederlands")
    expect(dutch_tab).to_be_focused()

    # Navigate to the second and activate it
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Enter")

    english_tab = page.get_by_role("tab", name="English", selected=True)
    expect(english_tab).to_be_focused()
    english_tab_panel = page.get_by_role("tabpanel", name="English")
    expect(english_tab_panel).to_be_visible()
    expect(english_tab_panel).to_have_text("English Content")
