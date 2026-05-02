# import requests
# import pytest

# BASE_URL = "https://preprod.admin.kwicpe.com/api/v1"

# HEADERS = {
#     "accept": "application/json, text/plain, */*",
#     "Content-Type": "application/json",
#     "user-agent": "Mozilla/5.0",
#     "x-skip": "true"
# }


# def get_login_payload():
#     return {
#         "email": "admintest@gmail.com",
#         "password": "Test@99999",
#         "recaptchaToken": "dummy_token"
#     }


# @pytest.fixture
# def auth_token():
#     url = f"{BASE_URL}/admin/auth/login"

#     response = requests.post(url, headers=HEADERS, json=get_login_payload())
#     print("Login Response:", response.text)

#     assert response.status_code == 201

#     # ✅ FIX: correct token key
#     return response.json().get("accessToken")


# def test_check_balance(auth_token):
#     url = f"{BASE_URL}/admin/transactions/balance"

#     headers = {
#         "accept": "application/json, text/plain, */*",
#         "authorization": f"Bearer {auth_token}",
#         "user-agent": "Mozilla/5.0",
#         "x-encrypted": "true",
#         "x-skip": "true"
#     }

#     # ✅ EXACT params from Postman (working ones)
#     params = {
#         "data": "O1cAotUIoACHmCrrbF944kGz",
#         "iv": "COhJYzBEwxg69wDz"
#     }

#     response = requests.get(url, headers=headers, params=params)

#     print("Final URL:", response.request.url)
#     print("Balance Response:", response.text)

#     assert response.status_code == 200



import requests
import pytest

BASE_URL = "https://staging.admin.kwicpe.com/api/api/v1"

LOGIN_URL = f"{BASE_URL}/admin/auth/login"
BALANCE_URL = f"{BASE_URL}/admin/transactions/get-admin-balance"
TXN_URL = f"{BASE_URL}/admin/transactions/get-transaction-by-id"
RECON_URL = f"{BASE_URL}/reconciliation/create-reconcilation"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "x-skip": "true"
}

# =========================
# LOGIN FUNCTION
# =========================
def get_token():
    payload = {
        "email": "super@gmail.com",
        "password": "Admin@12345",
        "recaptchaToken": "dummy_token"
    }

    response = requests.post(LOGIN_URL, headers=HEADERS, json=payload)
    assert response.status_code in [200, 201]

    res = response.json()

    token = res.get("accessToken") or res.get("data", {}).get("accessToken")

    assert token is not None, "Token not found in response"

    return token


# =========================
# GET BALANCE
# =========================
def get_balance(token, user_id):
    headers = HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"

    params = {"userId": user_id}

    response = requests.get(BALANCE_URL, headers=headers, params=params)
    print("Balance Response:", response.text)

    assert response.status_code == 200

    balance = response.json()
    return balance


# ===================== ====
# GET TRANSACTION
# =========================
def get_transaction(token, order_id):
    headers = HEADERS.copy()
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
# CREATE CHARGEBACK
# =========================
import json

def create_recon(token, txn):
    headers = HEADERS.copy()
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

# -------------------------
    


# =========================
# MAIN TEST
# =========================
def test_chargeback_balance_deduction():
    order_id = "o996825604"  # change dynamically if needed
    user_id = "26ee893c-4531-4905-bf8e-9fdc2b5c07e1"
    # Step 1: Login
    token = get_token()

    # Step 2: Balance before
    balance_before = get_balance(token, user_id)
    print("Balance Before:", balance_before)

    # Step 3: Get transaction
    txn_data = get_transaction(token, order_id)
    txn = txn_data["transactionDetail"][0]
    txn = {k: v for k, v in txn.items() if k not in [
"status_code", "response_body", "response_time", "request_body"
]}
    amount = float(txn["requestAmount"])
   
    penalty = txn_data.get("totalComission", 500)

    # Step 4: Create chargeback
    create_recon(token, txn)

    # Step 5: Balance after
    balance_after = get_balance(token, user_id)
    print("Balance After:", balance_after)

    # Step 6: Validation
    expected_balance = balance_before - amount - penalty

    print("Expected Balance:", expected_balance)

    assert balance_after <= expected_balance