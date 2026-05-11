import requests
import uuid
import pytest
import time
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================

BASE_URL = "https://preprod.admin.kwicpe.com/api/v1"

LOGIN_URL = f"{BASE_URL}/admin/auth/login"
FUND_LOAD_URL = f"{BASE_URL}/fundLoad/add"
TXN_URL = f"{BASE_URL}/admin/transactions/get-monthly-transaction-by-id"

USER_ID = "39a898fa-242a-4c09-a181-17548848df5c"

LOGIN_PAYLOAD = {
    "email": "super@gmail.com",
    "password": "Admin@123",
    "recaptchaToken": "dummy_token"

}

COMMON_HEADERS = {
    "Content-Type": "application/json",
     "x-skip": "true"
}

# =========================
# FIXTURE: LOGIN
# =========================

@pytest.fixture(scope="session")
def auth_token():
    response = requests.post(LOGIN_URL, json=LOGIN_PAYLOAD, headers=COMMON_HEADERS)
    print("\nLOGIN RESPONSE:", response.text)

    assert response.status_code == 201, "Login failed"
    token = response.json().get("accessToken") or response.json().get("data", {}).get("accessToken")

    return token


# =========================
# HELPER: GET WALLET BALANCE
# =========================

def get_wallet_balance(token):
    headers = {
        **COMMON_HEADERS,
        "Authorization": f"Bearer {token}",
        "x-skip": "true"
    }

    now = datetime.utcnow()
    start = (now - timedelta(days=1)).isoformat() + "Z"
    end = now.isoformat() + "Z"

    params = {
        "startDate": start,
        "endDate": end,
        "userId": USER_ID
    }

    response = requests.get(TXN_URL, headers=headers, params=params)
    print("\nTRANSACTION RESPONSE:", response.text)

    assert response.status_code == 200, "Transaction API failed"

    data = response.json()

    try:
        wallet_amount = float(data["dateRanges"][0]["walletAmount"])
        return wallet_amount
    except (KeyError, IndexError, ValueError):
        pytest.fail(f"Invalid wallet response format: {data}")


# =========================
# HELPER: ADD FUND
# =========================

def add_fund(token, amount):
    headers = {
        **COMMON_HEADERS,
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "userId": USER_ID,
        "depositAmount": str(amount),
        "utr": f"UTR{uuid.uuid4().hex[:10]}",
        "remark": "Pytest Wallet Load",
        "paymentMode": "Bank Transfer"
    }

    response = requests.post(FUND_LOAD_URL, json=payload, headers=headers)
    print("\nFUND LOAD RESPONSE:", response.text)

    assert response.status_code in [200, 201], "Fund load failed"

    return response.json()


# =========================
# HELPER: WAIT FOR BALANCE UPDATE
# =========================

def wait_for_wallet_update(token, expected_balance, retries=6, delay=2):
    for i in range(retries):
        current_balance = get_wallet_balance(token)
        print(f"Retry {i+1}: {current_balance}")

        if current_balance >= expected_balance:
            return current_balance

        time.sleep(delay)

    pytest.fail("Wallet balance not updated after retries")


# =========================
# TEST CASE
# =========================

def test_wallet_fund_flow(auth_token):
    token = auth_token

    # Step 1: Get wallet BEFORE
    before_balance = get_wallet_balance(token)
    print(f"\nWallet BEFORE: {before_balance}")

    # Step 2: Add fund
    amount_to_add = 100
    add_fund(token, amount_to_add)

    # Step 3: Wait for update
    expected_balance = before_balance + amount_to_add
    after_balance = wait_for_wallet_update(token, expected_balance)

    print(f"\nWallet AFTER: {after_balance}")

    # Step 4: Final Assertion
    assert after_balance == expected_balance, \
        f"Wallet not updated correctly: before={before_balance}, after={after_balance}"