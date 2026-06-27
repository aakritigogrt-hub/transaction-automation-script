import requests
import pytest
import random
import uuid
from ..config.headers import HEADERS
from ..config.base_url import BASE_URL
# =====================================================
# CONFIG
# =====================================================

LOGIN_URL = f"{BASE_URL}/api/v1/admin/auth/login"

GET_BALANCE_URL = (
    f"{BASE_URL}/api/v1/wallet/get-provider-avilable-balance?page=1"
)

PAYOUT_URL = (
    f"{BASE_URL}/api/v1/payout/initiate"
)


PROVIDER_ID="13a7d37b-f2ca-4848-ba5b-6ae900451b2d"
HEADERS_1 = {
    "accept": "application/json",
    "content-type": "application/json",
    "x-skip": "true",
    "skipCaptcha": "true"
}

# =====================================================
# LOGIN FUNCTION
# =====================================================

def get_token():
    payload = {
        "email": "super@gmail.com",
        "password": "Admin@123",
        "recaptchaToken": "dummy_token"
    }

    r = requests.post(LOGIN_URL, headers=HEADERS_1, json=payload)

    assert r.status_code in [200, 201]

    res = r.json()

    token = res.get("accessToken") or res.get("data", {}).get("accessToken")

    assert token, "Token not found"

    return token


# =====================================================
# COMMON HEADERS
# =====================================================

def get_headers(token):

    return {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "content-type": "application/json"
    }


# =====================================================
# FETCH PROVIDER BALANCE
# =====================================================

def get_provider_balance(headers):

    response = requests.get(
        GET_BALANCE_URL,
        headers=headers
    )

    print("\n========== BALANCE RESPONSE ==========")
    print(response.status_code)

    response_json = response.json()

    print(response_json)

    assert response.status_code in [200, 201]

    providers = response_json.get("data", {}).get("data", [])

    provider_balance = None

    for provider in providers:

        provider_id = provider.get("providerId")

        if provider_id == PROVIDER_ID:

            provider_balance = float(
                provider.get("balance", 0)
            )

            break

    assert provider_balance is not None, \
        f"Balance not found for provider {PROVIDER_ID}"

    return provider_balance


# =====================================================
# PAYOUT PAYLOAD
# =====================================================

def get_valid_payout_payload():

    amount = random.randint(200, 500)

    payload =  {
        "accountType": "savings",
        "amount": "500",
        "mode": "IMPS",
        "ifscCode": "HDFC0002671",
        "branchname": "SBI",
        "accountNo": "98798899989",
        "beneName": "shaIm",
        "beneAddress": "shaOm",
        "beneEmail": "shOm@gmail.com",
        "beneMobile": "9088930107",
        "orderId": str(uuid.uuid4())[:16]
    }

    return payload


# =====================================================
# SEND PAYOUT
# =====================================================

def send_payout(payload):

    response = requests.post(
        PAYOUT_URL,
        json=payload,
        headers=HEADERS
    )

    print("\n========== PAYOUT RESPONSE ==========")
    print(response.status_code)

    try:
        response_json = response.json()
        print(response_json)
        return response_json
    except:
        print(response.text)
        raise Exception("Invalid payout response")


# =====================================================
# VERIFY BALANCE DEDUCTION
# =====================================================

def verify_provider_balance_after_payout(
    old_balance,
    headers,
    payout_amount,
    response
):

    # ================================================
    # FETCH NEW BALANCE
    # ================================================

    new_balance = get_provider_balance(headers)

    print(f"\n✅ NEW BALANCE : {new_balance}")

    # ================================================
    # FETCH COMMISSION
    # ================================================

    try:
        commission = float(
            response.get("COMMISSION")
        )
    except:
        commission = 10

    print(f"\n✅ COMMISSION : {commission}")

    # ================================================
    # VERIFY BALANCE
    # ================================================

    expected_balance = (
        old_balance
        - payout_amount
        - commission
    )

    print(f"\nEXPECTED BALANCE : {expected_balance}")
    print(f"ACTUAL BALANCE   : {new_balance}")

    assert round(new_balance, 2) == round(expected_balance, 2), (
        f"\nBalance mismatch!"
        f"\nExpected : {expected_balance}"
        f"\nActual   : {new_balance}"
    )

    print("\n✅ PAYOUT BALANCE VERIFIED SUCCESSFULLY")


# =====================================================
# TEST CASE
# =====================================================

@pytest.mark.payout
def test_provider_balance_after_payout():

    # ================================================
    # STEP 1 : LOGIN
    # ================================================

    token = get_token()

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "content-type": "application/json"
    }
    # ================================================
    # STEP 2 : FETCH OLD BALANCE
    # ================================================

    old_balance = get_provider_balance(headers)

    print(f"\n✅ OLD BALANCE : {old_balance}")

    # ================================================
    # STEP 3 : CREATE PAYOUT PAYLOAD
    # ================================================

    payload = get_valid_payout_payload()

    payout_amount = float(payload["amount"])

    print("\n========== PAYOUT REQUEST ==========")
    print(payload)

    # ================================================
    # STEP 4 : SEND PAYOUT
    # ================================================

    response = send_payout(payload)

    # ================================================
    # STEP 5 : VALIDATE PAYOUT RESPONSE
    # ================================================

    if response["RESPONSE_CODE"] == "500":

        assert response["RESPONSE_STATUS"] == "SETTLEMENT_PROCESS"

        assert response["ORDER_ID"] is not None

        print("\n✅ PAYOUT INITIATED SUCCESSFULLY")

    elif response["RESPONSE_CODE"] == "999":

        pytest.fail(
            f"Insufficient wallet balance : "
            f"{response['RESPONSE_MESSAGE']}"
        )

    else:

        pytest.fail(
            f"Unexpected response : {response}"
        )

    # ================================================
    # STEP 6 : VERIFY BALANCE
    # ================================================

    verify_provider_balance_after_payout(
        old_balance=old_balance,
        headers=headers,
        payout_amount=payout_amount,
        response=response
    )