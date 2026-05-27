import pytest
import requests
import uuid
import logging
import random
import time

from ..config.headers import HEADERS

# -------------------------
# CONFIG
# -------------------------
LOGIN_URL = "https://staging.admin.kwicpe.com/api/api/v1/admin/auth/login"
PAYIN_URL = "https://staging.admin.kwicpe.com/api/api/v1/payments/requests"

WEBHOOK_URL = (
    "https://staging.admin.kwicpe.com/api/api/v1/webhooks/get-webhook-payin-data"
)

ROLLING_RESERVE_URL = (
    "https://staging.admin.kwicpe.com/api/api/v1/rolling-reserve/"
    "get-rolling-reserve-data?page=1"
)

TIMEOUT = (30,60)
HEADERS_1 = {
    "accept": "application/json",
    "content-type": "application/json",
    "x-skip": "true"
}
# -------------------------
# LOGGING
# -------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_token():
    payload = {
        "email": "super@gmail.com",
        "password": "Admin@12345",
        "recaptchaToken": "dummy_token"
    }

    r = requests.post(LOGIN_URL, headers=HEADERS_1, json=payload)

    assert r.status_code in [200, 201]

    res = r.json()

    token = res.get("accessToken") or res.get("data", {}).get("accessToken")

    assert token, "Token not found"

    return token
# -------------------------
# COMMON FUNCTION
# -------------------------

def create_payin():
    """Create fresh payin transaction"""

    payload = {
        "orderId": f"ORD{uuid.uuid4().hex[:8]}",
        "amount": "300",
        "customerEmail": f"user{uuid.uuid4().hex[:8]}@yopmail.com",
        "customerMobile": f"9{random.randint(100000000, 999999999)}",
        "customerName": "sonita",
        "transactionMode": "UPI_INTENT",
        "vpa": "stage@ybl"
    }

    logger.info(f"Creating Payin: {payload}")

    r = requests.post(
        PAYIN_URL,
        headers=HEADERS,
        json=payload,
        timeout=TIMEOUT
    )

    logger.info(f"Payin Response: {r.status_code} | {r.text}")

    assert r.status_code in [200, 201], f"Payin Failed: {r.text}"

    return {
        "ORDER_ID": payload["orderId"],
        "AMOUNT": payload["amount"],
        "TRANSACTION_ID": r.json().get("TRANSACTION_ID", "")
    }

# -------------------------
# FIXTURE
# -------------------------

@pytest.fixture(scope="function")
def payin_data():
    return create_payin()

# -------------------------
# VALIDATOR
# -------------------------

class Validator:

    @staticmethod
    def success(data):
        return data.get("RESPONSE_CODE") == "000"

# -------------------------
# TEST CASE
# -------------------------

def test_rolling_reserve_entry_created(
    payin_data
):
    start = time.time()
    webhook_payload = {
        "RESPONSE_CODE": "000",
        "RESPONSE_STATUS": "SUCCESS",
        "ORDER_ID": payin_data["ORDER_ID"],
        "AMOUNT": payin_data["AMOUNT"],
        "RESPONSE_MESSAGE": "Transaction success",
        "TRANSACTION_ID": f"txn_{uuid.uuid4().hex[:6]}",
        "vpa": "stage@ybl"
    }
    print("TIME:", time.time() - start)
    webhook_response = requests.post(
        WEBHOOK_URL,
        json=webhook_payload,
        timeout=TIMEOUT
    )

    assert webhook_response.status_code in [200, 201, 404]

    time.sleep(5)
    token = get_token()

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "x-skip":"true"
    }
    reserve_response = requests.get(
        ROLLING_RESERVE_URL,
        headers=headers,
        timeout=TIMEOUT
    )

    assert reserve_response.status_code == 200

    data = reserve_response.json()

    found = False

    for item in data:

        order_id = (
            item.get("orderId")
            or item.get("ORDER_ID")
        )

        if order_id == payin_data["ORDER_ID"]:

            found = True

            print("Rolling Reserve Entry Found")
            print(item)

            break

    assert found, (
        f"Rolling Reserve Entry Not Found "
        f"for Order ID: {payin_data['ORDER_ID']}"
    )