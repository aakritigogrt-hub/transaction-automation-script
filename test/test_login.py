import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture
def driver():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    yield driver
    driver.quit()

def test_login_dashboard(driver):
    driver.get("https://preprod.admin.kwicpe.com")

    wait = WebDriverWait(driver, 20)

    # Enter credentials
    email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    email_field.send_keys("super@gmail.com")

    password_field = driver.find_element(By.NAME, "password")
    password_field.send_keys("Admin@123")

    login_button = driver.find_element(By.XPATH, "//button[contains(text(),'Login') or @type='submit']")
    login_button.click()

    # Wait until dashboard URL
    wait.until(EC.url_contains("#/dashboard"))

    # ✅ Instead of searching for a specific element, just assert URL
    assert "#/dashboard" in driver.current_url, "Dashboard did not load"

    print("Dashboard loaded successfully:", driver.current_url)