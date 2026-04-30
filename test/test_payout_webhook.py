



# test_webhook_payout_e2e.py

import pytest
import requests
import uuid
import random
import logging
from ..config.headers import HEADERS

# =========================
# CONFIG
# =========================

PAYOUT_URL = "https://preprod.admin.kwicpe.com/api/v1/payout/initiate"
WEBHOOK_URL = "https://preprod.admin.kwicpe.com/api/v1/webhooks/get-webhook-payout-data"



TIMEOUT = 15

# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# HELPER
# =========================

def generate_order_id():
    return f"ORD{uuid.uuid4().hex[:10]}"


# =========================
# STEP 1: CREATE PAYOUT
# =========================

def create_payout():

    order_id = generate_order_id()
    amount = str(random.randint(100, 500))

    payload = {
        "accountType": "savings",
        "amount": amount,
        "mode": "IMPS",
        "ifscCode": "HDFC0002671",
        "accountNo": str(random.randint(10000000000, 99999999999)),
        "beneName": "Test User",
        "beneAddress": "Testing",
        "beneEmail": "test@gmail.com",
        "beneMobile": "9000000000",
        "orderId": order_id
    }

    logger.info(f"PAYOUT REQUEST: {payload}")

    res = requests.post(PAYOUT_URL, headers=HEADERS, json=payload, timeout=TIMEOUT)

    logger.info(f"PAYOUT RESPONSE: {res.status_code} | {res.text}")

    assert res.status_code == 201

    data = res.json()

    # Business validation
    assert data["RESPONSE_CODE"] == "500"
    assert data["RESPONSE_STATUS"] == "SETTLEMENT_PROCESS"

    return {
        "ORDER_ID": order_id,
        "AMOUNT": amount
    }


# =========================
# FIXTURE (RUNS BEFORE EVERY TEST)
# =========================

@pytest.fixture(scope="function")
def payout_data():
    return create_payout()


# =========================
# STEP 2: SEND WEBHOOK
# =========================

def send_webhook(order_id, amount, status="SETTLED"):

    payload = {
        "RESPONSE_CODE": "000" if status == "SETTLED" else "999",
        "UTR": f"UTR{uuid.uuid4().hex[:8]}",
        "RESPONSE_STATUS": status,
        "ORDER_ID": order_id,
        "AMOUNT": amount,
        "RESPONSE_MESSAGE": f"Webhook {status}",
        "MERCHANT_REF_NO": order_id
    }

    logger.info(f"WEBHOOK PAYLOAD: {payload}")

    res = requests.post(WEBHOOK_URL, headers=HEADERS, json=payload, timeout=TIMEOUT)

    logger.info(f"WEBHOOK RESPONSE: {res.status_code} | {res.text}")

    return res


# =========================
# TEST CASES
# =========================

# ✅ 1. SUCCESS FLOW
def test_payout_webhook_success(payout_data):

    res = send_webhook(
        payout_data["ORDER_ID"],
        payout_data["AMOUNT"],
        status="SETTLED"
    )

    assert res.status_code in [200, 201]


# ✅ 2. FAILED FLOW
def test_payout_webhook_failed(payout_data):

    res = send_webhook(
        payout_data["ORDER_ID"],
        payout_data["AMOUNT"],
        status="FAILED"
    )

    assert res.status_code in [200, 201]


# ❌ 3. INVALID ORDER
def test_webhook_invalid_order():

    res = send_webhook(
        "INVALID123",
        "100",
        status="SETTLED"
    )

    assert res.status_code in [400, 404]


# 🔁 4. DUPLICATE WEBHOOK
def test_webhook_duplicate(payout_data):

    send_webhook(payout_data["ORDER_ID"], payout_data["AMOUNT"], "SETTLED")

    res = send_webhook(payout_data["ORDER_ID"], payout_data["AMOUNT"], "SETTLED")

    assert res.status_code in [200, 400, 409]


# ⚠️ 5. STATUS CHANGE
def test_webhook_status_change(payout_data):

    send_webhook(payout_data["ORDER_ID"], payout_data["AMOUNT"], "SETTLED")

    res = send_webhook(payout_data["ORDER_ID"], payout_data["AMOUNT"], "FAILED")

    assert res.status_code in [200, 400]


