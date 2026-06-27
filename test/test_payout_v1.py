 
import requests
import pytest
from ..utils.payload_factory import get_valid_payout_payload
from ..config.headers import HEADERS
from ..config.base_url import BASE_URL
# =========================
# CONFIG
# =========================

URL = f"{BASE_URL}/api/v1/payout/initiate"



# =========================
# COMMON FUNCTION
# =========================

def send_payout(payload):
    response = requests.post(URL, headers=HEADERS, json=payload)
    print("Response:", response.text)
    return response.json()

# =========================
# POSITIVE TEST
# =========================

def test_payout_initiated():
    payload = get_valid_payout_payload()
    response = send_payout(payload)

    if response["RESPONSE_CODE"] == "500":
        assert response["RESPONSE_STATUS"] == "SETTLEMENT_PROCESS"
        assert response["ORDER_ID"] is not None

    elif response["RESPONSE_CODE"] == "999":
        assert "Insufficient wallet balance" in response["RESPONSE_MESSAGE"]

    else:
        assert False, f"Unexpected response: {response}"

# =========================
# NEGATIVE TESTS
# =========================

def test_invalid_account_number():
    payload = get_valid_payout_payload()
    payload["accountNo"] = ""

    response = send_payout(payload)

    assert response["RESPONSE_CODE"] == "999"


def test_invalid_account_number():
    payload = get_valid_payout_payload()
    payload["accountNo"] = "7647343433543854387387287288363886768"

    response = send_payout(payload)

    assert response["RESPONSE_CODE"] == "999"

def test_invalid_ifsc():
    payload = get_valid_payout_payload()
    payload["ifscCode"] = "INVALID123"

    response = send_payout(payload)

    assert response["RESPONSE_CODE"] == "999"


def test_negative_amount():
    payload = get_valid_payout_payload()
    payload["amount"] = "-100"

    response = send_payout(payload)
    print(response)
    assert response["RESPONSE_CODE"] == "999"



def test_zero_amount():
    payload = get_valid_payout_payload()
    payload["amount"] = "0"

    response = send_payout(payload)

    assert response["RESPONSE_CODE"] == "999"


def test_invalid_mobile():
    payload = get_valid_payout_payload()
    payload["beneMobile"] = "123"

    response = send_payout(payload)

    assert response["RESPONSE_CODE"] == "999"


def test_invalid_email():
    payload = get_valid_payout_payload()
    payload["beneEmail"] = "invalidemail"

    response = send_payout(payload)

    assert response["RESPONSE_CODE"] == "999"

# =========================
# DUPLICATE TEST
# =========================

def test_duplicate_payout():
    payload = get_valid_payout_payload()

    response1 = send_payout(payload)

    response2 = send_payout(payload)

    assert response2["RESPONSE_CODE"] == "999"
    assert response2["RESPONSE_STATUS"] == "SETTLEMENT_FAILED"

    assert (
        "Duplicate" in response2["RESPONSE_MESSAGE"]
        or "Insufficient wallet balance" in response2["RESPONSE_MESSAGE"]
    )

# =========================
# EMPTY PAYLOAD
# =========================

def test_empty_payload():
    response = send_payout({})

    assert response["statusCode"] == 401
    assert "accountNo" in response["message"]



def test_min_amount_error():
    payload = get_valid_payout_payload()
    payload["amount"] = "5"

    response = send_payout(payload)

    assert response["RESPONSE_CODE"] == "999"
    assert response["RESPONSE_STATUS"] == "SETTLEMENT_FAILED"
    assert "minimum" in response["RESPONSE_MESSAGE"].lower()

def test_max_amount_error():
    payload = get_valid_payout_payload()
    payload["amount"] = "11000"

    response = send_payout(payload)

    assert response["RESPONSE_CODE"] == "999"
    assert response["RESPONSE_STATUS"] == "SETTLEMENT_FAILED"
    assert "maximum" in response["RESPONSE_MESSAGE"].lower()