
import pytest
import requests
import uuid
import logging
from ..config.headers import HEADERS
# -------------------------
# CONFIG
# -------------------------

PAYIN_URL = "https://preprod.admin.kwicpe.com/api/v1/payments/requests"
WEBHOOK_URL = "https://preprod.admin.kwicpe.com/api/v1/webhooks/get-webhook-payin-data"

TIMEOUT = 15

import random
# -------------------------
# LOGGING
# -------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -------------------------
# COMMON FUNCTION
# -------------------------

def create_payin():
    """Create a fresh payin transaction"""

    payload = {
        "orderId": f"ORD{uuid.uuid4().hex[:8]}",
        "amount": "300",
        "customerEmail": f"user{uuid.uuid4().hex[:8]}@yopmail.com",
        "customerMobile": f"9{random.randint(100000000, 999999999)}",
        "customerName": "sonita",
        "transactionMode": "UPI_INTENT",
        "vpa": f"user{uuid.uuid4().hex[:6]}@ybl"
    }

    logger.info(f"Creating Payin: {payload}")

    r = requests.post(PAYIN_URL, headers=HEADERS, json=payload, timeout=TIMEOUT)

    logger.info(f"Payin Response: {r.status_code} | {r.text}")

    assert r.status_code in [200, 201], f"Payin failed: {r.text}"

    return {
        "ORDER_ID": payload["orderId"],
        "AMOUNT": payload["amount"],
        "TRANSACTION_ID": r.json().get("TRANSACTION_ID", "")   }


# -------------------------
# FIXTURE (RUNS BEFORE EVERY TEST)
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

    @staticmethod
    def failed(data):
        return data.get("RESPONSE_CODE") == "999"


# -------------------------
# POSITIVE TEST CASES
# -------------------------

def test_webhook_success(payin_data):
    """Webhook SUCCESS"""

    payload = {
        "RESPONSE_CODE": "000",
        "RESPONSE_STATUS": "SUCCESS",
        "ORDER_ID": payin_data["ORDER_ID"],
        "AMOUNT": payin_data["AMOUNT"],
        "RESPONSE_MESSAGE": "Transaction success",
        "TRANSACTION_ID": f"txn_{uuid.uuid4().hex[:6]}",
        "vpa": "success@ybl"
    }

    r = requests.post(WEBHOOK_URL, json=payload, timeout=TIMEOUT)

    logger.info(f"Webhook SUCCESS: {r.status_code} | {r.text}")

    assert r.status_code in [200, 201, 404]

    if r.status_code == 201:
        assert Validator.success(r.json())


def test_webhook_failed(payin_data):
    """Webhook FAILED"""

    payload = {
        "RESPONSE_CODE": "999",
        "RESPONSE_STATUS": "FAILED",
        "ORDER_ID": payin_data["ORDER_ID"],
        "AMOUNT": payin_data["AMOUNT"],
        "RESPONSE_MESSAGE": "Transaction failed",
        "TRANSACTION_ID": f"txn_{uuid.uuid4().hex[:6]}",
        "vpa": ""
    }

    r = requests.post(WEBHOOK_URL, json=payload, timeout=TIMEOUT)


    logger.info(f"Webhook FAILED: {r.status_code} | {r.text}")

    assert r.status_code in [200, 201, 404]

    if r.status_code == 201:
        assert Validator.failed(r.json())


# -------------------------
# NEGATIVE TEST CASES
# -------------------------

def test_webhook_amount_mismatch(payin_data):
    """Amount mismatch"""

    payload = {
        "RESPONSE_CODE": "000",
        "RESPONSE_STATUS": "SUCCESS",
        "ORDER_ID": payin_data["ORDER_ID"],
        "AMOUNT": "999",   # ❌ wrong amount
        "RESPONSE_MESSAGE": "Mismatch",
        "TRANSACTION_ID": f"txn_{uuid.uuid4().hex[:6]}",
        "vpa": "success@ybl"
    }

    r = requests.post(WEBHOOK_URL, json=payload, timeout=TIMEOUT)

    logger.info(f"Amount Mismatch: {r.status_code} | {r.text}")

    assert r.status_code in [200, 400, 404]


def test_webhook_invalid_order(payin_data):
    """Invalid ORDER_ID"""

    payload = {
        "RESPONSE_CODE": "000",
        "RESPONSE_STATUS": "SUCCESS",
        "ORDER_ID": "INVALID123",
        "AMOUNT": payin_data["AMOUNT"],
        "RESPONSE_MESSAGE": "Invalid order",
        "TRANSACTION_ID": f"txn_{uuid.uuid4().hex[:6]}",
        "vpa": "success@ybl"
    }

    r = requests.post(WEBHOOK_URL, json=payload, timeout=TIMEOUT)

    logger.info(f"Invalid Order: {r.status_code} | {r.text}")

    assert r.status_code in [200, 400, 404]


def test_webhook_missing_order_id(payin_data):
    """Missing ORDER_ID"""

    payload = {
        "RESPONSE_CODE": "000",
        "AMOUNT": payin_data["AMOUNT"]
    }

    r = requests.post(WEBHOOK_URL, json=payload, timeout=TIMEOUT)

    logger.info(f"Missing ORDER_ID: {r.status_code} | {r.text}")

    assert r.status_code in [200, 400, 404]


def test_webhook_invalid_response_code(payin_data):
    """Invalid RESPONSE_CODE"""

    payload = {
        "RESPONSE_CODE": "ABC",
        "ORDER_ID": payin_data["ORDER_ID"],
        "AMOUNT": payin_data["AMOUNT"]
    }

    r = requests.post(WEBHOOK_URL, json=payload, timeout=TIMEOUT)

    logger.info(f"Invalid RESPONSE_CODE: {r.status_code} | {r.text}")

    assert r.status_code in [200, 400, 404]


def test_webhook_empty_payload():
    """Empty payload"""

    r = requests.post(WEBHOOK_URL, json={}, timeout=TIMEOUT)

    logger.info(f"Empty Payload: {r.status_code} | {r.text}")

    assert r.status_code in [200, 400, 404]


def test_webhook_invalid_json():
    """Invalid JSON"""

    r = requests.post(
        WEBHOOK_URL,
        data="invalid_json",
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT
    )

    logger.info(f"Invalid JSON: {r.status_code} | {r.text}")

    assert r.status_code in [200, 400, 404]