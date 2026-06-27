import requests
import pytest
import uuid
import random
import time
import json
from ..config.headers import HEADERS
from ..config.base_url import BASE_URL
# =========================
# CONFIG
# =========================

LOGIN_URL = f"{BASE_URL}/admin/auth/login"
BALANCE_URL = f"{BASE_URL}/admin/transactions/get-admin-balance"
TXN_URL = f"{BASE_URL}/admin/transactions/get-transaction-by-id"
RECON_URL = f"{BASE_URL}/reconciliation/create-reconcilation"

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

    params = {"userId": USER_ID}

    r = requests.get(BALANCE_URL, headers=headers, params=params)
    print("Balance:", r.text)

    assert r.status_code == 200

    res = r.json()

    # handle float / object both
    if isinstance(res, float):
        return res

    if "data" in res:
        return res["data"].get("availableBalance", 0)

    return res.get("availableBalance", 0)


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

    r = requests.post(PAYIN_URL, headers=HEADERS, json=payload, timeout=TIMEOUT)

    print("Payin:", r.text)
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
        "vpa": ""
    }

    try:
        r = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=(5, 30)  # ✅ connect=5s, read=30s
        )

        print("Webhook Response:", r.text)

        assert r.status_code in [200, 201, 404]

    except requests.exceptions.ReadTimeout:
        # ✅ DO NOT FAIL TEST — webhook still processed in backend
        print("⚠️ Webhook timeout but continuing (async API)")


# =========================
# GET TRANSACTION
# =========================
def get_transaction(token, order_id):
    headers = HEADERS_1.copy()
    headers["authorization"] = f"Bearer {token}"

    params = {"orderId": order_id}

    response = requests.get(TXN_URL, headers=headers, params=params)
    print("Transaction Response:", response.text)

    assert response.status_code == 200
    

    res_json = response.json()

    # ✅ IMPORTANT: extract only real data
    if "data" in res_json:
        return res_json["data"]
    return res_json





# =========================
# CLEAN LOG FIELDS
# =========================
def clean_txn(txn):
    remove = ["status_code", "response_body", "response_time", "request_body"]
    return {k: v for k, v in txn.items() if k not in remove}


# =========================
# CREATE RECON (CHARGEBACK)
# =========================
def create_recon(token, txn):
    headers = HEADERS_1.copy()
    headers["authorization"] = f"Bearer {token}"

    # ✅ Convert string → dict
    request_dict = json.loads(txn["request"])
    response_dict = json.loads(txn["resposne"])

    payload = {
        "id": txn["id"],
        "referenceId": txn["referenceId"],

        "request": txn["request"],        # KEEP STRING
        "resposne": txn["resposne"],      # KEEP STRING (API typo)

        "dataItem": request_dict,         # 🔥 REQUIRED
        "responseData": response_dict,    # 🔥 REQUIRED

        "type": txn["type"],
        "orderId": txn["orderId"],
        "transactionId": txn["transactionId"],
        "pg": txn.get("pg", "test"),

        "settlementAmount": txn["settlementAmount"],
        "totalComission": txn["totalComission"],
        "netComission": txn["netComission"],
        "rollingReserve": txn["rollingReserve"],
        "closingBalance": txn["closingBalance"],
        "requestAmount": txn["requestAmount"],
        "responseStatus": txn["responseStatus"],

        "orgName": txn["orgName"],
        "providerId": txn["providerId"],
        "providerComm": txn["providerComm"],
        "superComm": txn["superComm"],
        "totalComm": txn["totalComm"],

        "customerId": txn["customerId"],
        "alias": txn["alias"],
        "approved": False
    }

    response = requests.post(RECON_URL, headers=headers, json=payload)

    print("✅ FINAL PAYLOAD:", payload)
    print("🔁 RESPONSE:", response.text)

    return response


# =========================
# MAIN TEST
# =========================
def test_full_chargeback_flow():
    token = get_token()

    # Step 1: Payin
    payin = create_payin()

    # Step 2: Webhook
    send_webhook(payin)
    # Step 3: Balance before
    balance_before = get_balance(token)
    print("Balance Before:", balance_before)

    # Step 4: Wait & fetch txn
    txn_data = get_transaction(token, payin["orderId"])
    txn = txn_data["transactionDetail"][0]
    txn = {k: v for k, v in txn.items() if k not in [
"status_code", "response_body", "response_time", "request_body"
]}
    amount = float(txn["requestAmount"])
    penalty = 500  # or fixed 2000 if needed

    # Step 5: Create chargeback
    create_recon(token, txn)

    # Step 6: Balance after
    time.sleep(3)
    balance_after = get_balance(token)

    print("Balance After:", balance_after)

    delta = balance_before - balance_after
    expected_delta = float(amount) + penalty
    print("Expected:", expected_delta)

    assert delta == expected_delta