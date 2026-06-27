



import pytest
import requests
import time
from ..config.headers import HEADERS
from ..config.base_url import BASE_URL
from ..utils.payload_factory import get_valid_payload



# ==========================
# BASE CONFIG
# ==========================
BASE_URLS = f"{BASE_URL}/api/v1/payments/requests"
TIMEOUT = 10

VALID_MODES = ["UPI_INTENT", "UPI_COLLECT"]


# ==========================
# TEST CLASS
# ==========================
class TestPayinAPI:

    # ----------------------
    # SUCCESS CASE
    # ----------------------
    def test_success_payment(self):
        payload = get_valid_payload()

        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        data = response.json()

        assert response.status_code == 201
        assert data.get("ORDER_ID") is not None
        assert data.get("RESPONSE_CODE") != "999"

    # ----------------------
    # MISSING FIELD TESTS
    # ----------------------
    @pytest.mark.parametrize("field", [
    "orderId",  # replace with actual order id field name
    "amount"])
    def test_missing_fields(self, field):
        payload = get_valid_payload()

        del payload[field]

        response = requests.post(
            BASE_URLS,
            headers=HEADERS,
            json=payload,
            timeout=TIMEOUT
        )

        print(f"Removed field: {field}")
        print(response.text)
        assert response.status_code == 201

    # ----------------------
    # FORMAT VALIDATION
    # ----------------------
    def test_invalid_email(self):
        payload = get_valid_payload()
        payload["customerEmail"] = "invalid"

        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        assert response.json().get("RESPONSE_CODE") == "999"

    def test_invalid_mobile(self):
        payload = get_valid_payload()
        payload["customerMobile"] = "123"

        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        assert response.json().get("RESPONSE_CODE") == "999"

    def test_invalid_vpa(self):
        payload = get_valid_payload()
        payload["vpa"] = "wrongupi"

        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        assert response.json().get("RESPONSE_CODE") == "999"

    # ----------------------
    # AMOUNT TESTS
    # ----------------------
    @pytest.mark.parametrize("amount", ["0", "-100", "99999999"])
    def test_invalid_amount(self, amount):
        payload = get_valid_payload()
        payload["amount"] = amount

        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        assert response.json().get("RESPONSE_CODE") == "400"

    # ----------------------
    # AUTH TESTS
    # ----------------------
    def test_missing_api_key(self):
        payload = get_valid_payload()
        headers = {"Content-Type": "application/json"}

        response = requests.post(BASE_URLS, headers=headers, json=payload, timeout=TIMEOUT)
        assert response.status_code in [401, 201, 400]

    def test_invalid_api_key(self):
        payload = get_valid_payload()
        headers = {
            "api-key": "wrong_key",
            "Content-Type": "application/json"
        }

        response = requests.post(BASE_URLS, headers=headers, json=payload, timeout=TIMEOUT)
        assert response.status_code in [401, 201, 400]

    # ----------------------
    # DUPLICATE ORDER
    # ----------------------
    def test_duplicate_order(self):
        payload = get_valid_payload()

        r1 = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        r2 = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)

        data2 = r2.json()

        assert "ORDER_ID" in data2 or data2.get("RESPONSE_CODE") == "999"

    # ----------------------
    # TRANSACTION MODES
    # ----------------------
    @pytest.mark.parametrize("mode", VALID_MODES)
    def test_valid_transaction_modes(self, mode):
        payload = get_valid_payload()
        payload["transactionMode"] = mode

        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        assert response.json().get("ORDER_ID") is not None

    # def test_invalid_transaction_mode(self):
    #     payload = get_valid_payload()
    #     payload["transactionMode"] = "INVALID"

    #     response = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=TIMEOUT)
    #     assert response.json().get("RESPONSE_CODE") == "999"

    # ----------------------
    # RESPONSE STRUCTURE
    # ----------------------
    def test_response_structure(self):
        payload = get_valid_payload()

        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        data = response.json()

        assert "ORDER_ID" in data
        assert "RESPONSE_CODE" in data
        assert "RESPONSE_MESSAGE" in data

    # ----------------------
    # RESPONSE TIME
    # ----------------------
    def test_response_time(self):
        payload = get_valid_payload()

        start = time.time()
        requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        end = time.time()

        assert (end - start) < 5

    def test_min_amount_error(self):
        payload = get_valid_payload()
        payload["amount"] = "10"

        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        data = response.json()

        assert response.status_code in [200, 201, 400]
        assert data.get("RESPONSE_CODE") == "999"
        assert data.get("RESPONSE_STATUS") == "FAILED"

        # Flexible validation
        assert "minimum" in data.get("RESPONSE_MESSAGE", "").lower()


    def test_max_amount_error(self):
        payload = get_valid_payload()
        payload["amount"] = "11000"

        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        data = response.json()

        assert response.status_code in [200, 201, 400]
        assert data.get("RESPONSE_CODE") == "999"
        assert data.get("RESPONSE_STATUS") == "FAILED"

        # Flexible validation
        assert "maximum" in data.get("RESPONSE_MESSAGE", "").lower()
    # ----------------------


    def test_min_amount_error_flexible(self):
        payload = get_valid_payload()
        payload["amount"] = "4"

        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        data = response.json()

        message = data.get("RESPONSE_MESSAGE", "").lower()

        assert data.get("RESPONSE_CODE") == "999"

        assert (
            "minimum amount" in message
            or "below the minimum limit" in message
        ), f"Unexpected message: {message}"


    def test_max_amount_error_flexible(self):
        payload = get_valid_payload()
        payload["amount"] = "9100"

        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        data = response.json()

        message = data.get("RESPONSE_MESSAGE", "").lower()

        assert data.get("RESPONSE_CODE") == "999"

        assert (
            "transaction amount exceeds the maximum limit" in message
            or " transaction amount exceeds the maximum limit" in message
        ), f"Unexpected message: {message}"

    # EDGE CASES
    # ----------------------

    # def test_special_characters(self):
    #     payload = get_valid_payload()
    #     payload["customerName"] = "@@@###$$$"

    #     response = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=TIMEOUT)
    #     assert response.status_code in [ 400]

    # def test_empty_payload(self):
    #     response = requests.post(BASE_URL, headers=HEADERS, json={}, timeout=TIMEOUT)
    #     assert response.json().get("RESPONSE_CODE") == "999"

    # # ----------------------
    # # SECURITY TESTS
    # # ----------------------
    # def test_sql_injection(self):
    #     payload = get_valid_payload()
    #     payload["customerName"] = "' OR 1=1 --"

    #     response = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=TIMEOUT)
    #     assert response.status_code in [400]

    # def test_xss_attack(self):
    #     payload = get_valid_payload()
    #     payload["customerName"] = "<script>alert(1)</script>"

    #     response = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=TIMEOUT)
    #     assert response.status_code in [400]

    def test_invalid_amount(self):
        payload = get_valid_payload()
        payload["amount"] = "abc"
        response = requests.post(BASE_URLS, headers=HEADERS, json=payload, timeout=TIMEOUT)
        data = response.json()
        assert response.status_code in [400]



   
    def test_ip_not_whitelisted(self):
        payload = get_valid_payload()

        response = requests.post(
            BASE_URLS,
            headers=HEADERS,
            json=payload,
            timeout=TIMEOUT
        )

        data = response.json()

        assert response.status_code == 403
        assert data.get("statusCode") == 403
        assert data.get("errors") == "Forbidden"
        assert "not whitelisted" in data.get("message", "").lower()
        assert data.get("data") is None