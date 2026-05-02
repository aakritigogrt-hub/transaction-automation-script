# import pytest
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# @pytest.fixture
# def driver():
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
#     driver.maximize_window()
#     yield driver
#     driver.quit()

# def test_login_dashboard(driver):
#     driver.get("https://preprod.admin.kwicpe.com")

#     wait = WebDriverWait(driver, 20)

#     # Enter credentials
#     email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
#     email_field.send_keys("super@gmail.com")

#     password_field = driver.find_element(By.NAME, "password")
#     password_field.send_keys("Admin@123")

#     login_button = driver.find_element(By.XPATH, "//button[contains(text(),'Login') or @type='submit']")
#     login_button.click()

#     # Wait until dashboard URL
#     wait.until(EC.url_contains("#/dashboard"))

#     # ✅ Instead of searching for a specific element, just assert URL
#     assert "#/dashboard" in driver.current_url, "Dashboard did not load"

#     print("Dashboard loaded successfully:", driver.current_url)


import requests
import pytest
from ..utils.login_payload import *

BASE_URL = "https://preprod.admin.kwicpe.com/api/v1/admin/auth/login"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def test_valid_login():
    response = requests.post(BASE_URL, headers=HEADERS, json=get_valid_payload())
    assert response.status_code == 201


def test_invalid_email():
    response = requests.post(BASE_URL, headers=HEADERS, json=get_invalid_email_payload())
    assert response.status_code in [400, 401,422]


def test_invalid_password():
    response = requests.post(BASE_URL, headers=HEADERS, json=get_invalid_password_payload())
    assert response.status_code in [400, 401,422]


def test_empty_email():
    response = requests.post(BASE_URL, headers=HEADERS, json=get_empty_email_payload())
    assert response.status_code == 422


def test_empty_password():
    response = requests.post(BASE_URL, headers=HEADERS, json=get_empty_password_payload())
    assert response.status_code == 422


def test_missing_email():
    response = requests.post(BASE_URL, headers=HEADERS, json=get_missing_email_payload())
    assert response.status_code == 422


def test_missing_password():
    response = requests.post(BASE_URL, headers=HEADERS, json=get_missing_password_payload())
    assert response.status_code == 422


def test_invalid_recaptcha():
    response = requests.post(BASE_URL, headers=HEADERS, json=get_invalid_recaptcha_payload())
    assert response.status_code in [400, 401]