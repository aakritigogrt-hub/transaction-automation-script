import requests
import pytest
import uuid
import random
import time
import json
from ..config.headers import HEADERS

# =========================
# CONFIG
# =========================

BASE_URL = "https://staging.admin.kwicpe.com/api/api/v1"

LOGIN_URL = f"{BASE_URL}/admin/auth/login"
BALANCE_URL = f"{BASE_URL}/admin/transactions/get-admin-balance"
TXN_URL = f"{BASE_URL}/admin/transactions/get-transaction-by-id"

COMPLAINT_URL = f"{BASE_URL}/admin/complaint/create-complaint"

PAYIN_URL = f"{BASE_URL}/payments/requests"
WEBHOOK_URL = f"{BASE_URL}/webhooks/get-webhook-payin-data"

TIMEOUT = 10

HEADERS_1 = {
    "accept": "application/json",
    "content-type": "application/json",
    "x-skip": "true"
}

USER_ID = "26ee893c-4531-4905-bf8e-9fdc2b5c07e1"


# =========================
# LOGIN
# =========================

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


# =========================
# BALANCE
# =========================

def get_balance(token):

    headers = HEADERS_1.copy()
    headers["authorization"] = f"Bearer {token}"

    params = {
        "userId": USER_ID
    }

    r = requests.get(
        BALANCE_URL,
        headers=headers,
        params=params
    )

    print("Balance Response:", r.text)

    assert r.status_code == 200

    res = r.json()

    if isinstance(res, float):
        return res

    if "data" in res:
        return float(res["data"].get("availableBalance", 0))

    return float(res.get("availableBalance", 0))


# =========================
# PAYIN
# =========================

def create_payin():

    payload = {
        "orderId": f"ORD{uuid.uuid4().hex[:8]}",
        "amount": "300",
        "customerEmail": f"user{uuid.uuid4().hex[:8]}@yopmail.com",
        "customerMobile": f"9{random.randint(100000000, 999999999)}",
        "customerName": "sonitma",
        "transactionMode": "UPI_INTENT",
        "vpa": f"user{uuid.uuid4().hex[:6]}@ybl"
    }

    r = requests.post(
        PAYIN_URL,
        headers=HEADERS,
        json=payload,
        timeout=TIMEOUT
    )

    print("Payin Response:", r.text)

    assert r.status_code in [200, 201]

    return {
        "orderId": payload["orderId"],
        "amount": payload["amount"]
    }


# =========================
# WEBHOOK
# =========================

def send_webhook(payin):

    payload = {
        "RESPONSE_CODE": "000",
        "RESPONSE_STATUS": "SUCCESS",
        "ORDER_ID": payin["orderId"],
        "AMOUNT": payin["amount"],
        "RESPONSE_MESSAGE": "Transaction success",
        "TRANSACTION_ID": f"txn_{uuid.uuid4().hex[:6]}",
        "vpa": "",
         "UTR": "34658769"
    }

    try:

        r = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=(5, 30)
        )

        print("Webhook Response:", r.text)

        assert r.status_code in [200, 201, 404]

    except requests.exceptions.ReadTimeout:

        print("⚠️ Webhook timeout but continuing")


# =========================
# GET TRANSACTION
# =========================

def get_transaction(token, order_id):

    headers = HEADERS_1.copy()
    headers["authorization"] = f"Bearer {token}"

    params = {
        "orderId": order_id
    }

    response = requests.get(
        TXN_URL,
        headers=headers,
        params=params
    )

    print("Transaction Response:", response.text)

    assert response.status_code == 200

    res_json = response.json()

    if "data" in res_json:
        return res_json["data"]

    return res_json


# =========================
# CREATE COMPLAINT
# =========================


def create_complaint(token, txn):

    headers = HEADERS_1.copy()
    headers["authorization"] = f"Bearer {token}"

    # ✅ use actual transaction UTR
    actual_utr = (
        txn.get("responseUTR")
        or txn.get("bankUtr")
        or txn.get("txnUtr")
        or txn.get("transactionId")
    )

    payload = {
        "ackNo": "1",
        "utrs": [
            {
                "orderId": txn["orderId"],

                # ✅ REAL UTR FROM TRANSACTION
                "utr": actual_utr,

                "merchantName": USER_ID,
                "customerName": "Test",
                "complainterName": "Complaint User",
                "complainterPhone": f"9{random.randint(100000000,999999999)}",
                "complaintDate": time.strftime("%d-%m-%Y"),
                "email": f"user{uuid.uuid4().hex[:6]}@gmail.com",
                "phone": f"8{random.randint(100000000,999999999)}",
                "vpa": f"user{uuid.uuid4().hex[:5]}@ybl",

                # ✅ transaction amount
                "amount": float(txn["requestAmount"]),

                # ✅ complaint fee
                "fees": 100
            }
        ]
    }

    response = requests.post(
        COMPLAINT_URL,
        headers=headers,
        json=payload
    )

    print("Complaint Payload:", json.dumps(payload, indent=2))
    print("Complaint Response:", response.text)

    return response


# =========================
# MAIN TEST
# =========================

# =========================
# MAIN TEST
# =========================

def test_complaint_balance_deduction():

    token = get_token()

    # Step 1: Create Payin
    payin = create_payin()

    # Step 2: Send Webhook
    send_webhook(payin)

    # Step 3: Wait for txn creation
    time.sleep(5)

    # Step 4: Get Balance Before
    balance_before = get_balance(token)

    print("Balance Before:", balance_before)

    # Step 5: Fetch Transaction
    txn_data = get_transaction(token, payin["orderId"])

    txn = txn_data["transactionDetail"][0]

    # Step 6: Complaint values
    complaint_amount = float(txn["requestAmount"])
    complaint_fee = 100

    # Step 7: Create Complaint
    complaint_response = create_complaint(token, txn)

    assert complaint_response.status_code in [200, 201]

    # Step 8: Wait for balance update
    time.sleep(5)

    # Step 9: Get Balance After
    balance_after = get_balance(token)

    print("Balance After:", balance_after)

    # Step 10: Verify deduction
    expected_deduction = complaint_amount + complaint_fee

    actual_deduction = balance_before - balance_after

    print("Complaint Amount:", complaint_amount)
    print("Complaint Fees:", complaint_fee)
    print("Expected Deduction:", expected_deduction)
    print("Actual Deduction:", actual_deduction)

    assert actual_deduction == expected_deduction, (
        f"Balance deduction mismatch. "
        f"Expected Deduction: {expected_deduction}, "
        f"Actual Deduction: {actual_deduction}"
    )

    print("✅ Complaint amount + fees deducted successfully")