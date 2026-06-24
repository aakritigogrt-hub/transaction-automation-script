
import requests
import pytest
from ..utils.login_payload import *
from ..config.base_url import BASE_URL

BASE_URLS = f"{BASE_URL}/api/v1/admin/auth/login"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "x-skip":"true"
}


def test_valid_login():
    response = requests.post(BASE_URLS, headers=HEADERS, json=get_valid_payload())
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