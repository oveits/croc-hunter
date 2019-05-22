import os
import time

import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException)

hostname = os.getenv('INGRESS_HOSTNAME')
release_name = os.getenv('RELEASE_NAME')
commit_sha = os.getenv('CF_SHORT_REVISION')
selenium_hub_url = os.getenv('SELENIUM_HUB_URL')

# Give Selenium Hub time to start
time.sleep(15)  # TODO: figure how to do this better

@pytest.fixture(scope='module')
def browser():
    browser_name = ip = os.getenv('BROWSER')
    browser = webdriver.Remote(
        command_executor=selenium_hub_url,
        desired_capabilities={'browserName': browser_name},
    )
    yield browser
    browser.quit()


def test_confirm_title(browser):
    browser.get("http://{}".format(hostname))
    assert "Croc Hunter" in browser.title


def test_confirm_canvas_bg(browser):
    browser.get("http://{}".format(hostname))
    element = browser.find_element(By.ID, 'canvasBg')
    assert element.get_attribute('id') == 'canvasBg'


def test_confirm_canvas_enemy(browser):
    browser.get("http://{}".format(hostname))
    element = browser.find_element(By.ID, 'canvasEnemy')
    assert element.get_attribute('id') == 'canvasEnemy'


def test_confirm_canvas_jet(browser):
    browser.get("http://{}".format(hostname))
    element = browser.find_element(By.ID, 'canvasJet')
    assert element.get_attribute('id') == 'canvasJet'


def test_confirm_canvas_hud(browser):
    browser.get("http://{}".format(hostname))
    element = browser.find_element(By.ID, 'canvasHud')
    assert element.get_attribute('id') == 'canvasHud'


# TODO: uncomment:
def test_confirm_release_name(browser):
    browser.get("http://{}".format(hostname))
    element = browser.find_element(By.XPATH, '//div[@class="details"]')
    assert release_name in element.text


# def test_confirm_commit_sha(browser):
#     browser.get("http://{}".format(hostname))
#     element = browser.find_element(By.XPATH, '//div[@class="details"]')
#     assert commit_sha in element.text
