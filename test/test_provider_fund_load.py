import requests
import pytest
import random

# =====================================================
# CONFIG
# =====================================================

LOGIN_URL = "https://staging.admin.kwicpe.com/api/api/v1/admin/auth/login"

GET_BALANCE_URL = (
    "https://staging.admin.kwicpe.com/api/api/v1/"
    "wallet/get-provider-avilable-balance?page=1"
)
WALLET_LOAD_URL = "https://staging.admin.kwicpe.com/api/api/v1/wallet/wallet-load"
PPROVE_WALLET_LOAD_URL = "https://staging.admin.kwicpe.com/api/api/v1/wallet/approve-load-wallet"
EMAIL = "super@gmail.com"
PASSWORD = "Admin@12345"

PROVIDER_ID = "8bb39faf-bf01-4519-89a5-2742f98a2749"
HEADERS_1 = {
    "accept": "application/json",
    "content-type": "application/json",
    "x-skip": "true"
}


# =====================================================
# LOGIN FUNCTION
# =====================================================

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

# =====================================================
# TEST CASE : PROVIDER FUND UPLOAD
# =====================================================

    return token


# =====================================================
# FETCH PROVIDER BALANCE
# =====================================================
def get_provider_balance(headers):

    response = requests.get(
        GET_BALANCE_URL,
        headers=headers
    )

    print("\n========== BALANCE API RESPONSE ==========")
    print(response.status_code)

    response_json = response.json()

    print(response_json)

    assert response.status_code in [200, 201]

    # =========================================
    # ACTUAL PROVIDER LIST
    # =========================================

    providers = response_json.get("data", {}).get("data", [])

    provider_balance = None

    # =========================================
    # FIND MATCHING PROVIDER
    # =========================================

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

@pytest.mark.wallet
def test_provider_wallet_load_and_approve():

    # =================================================
    # STEP 1 : LOGIN
    # =================================================

    token = get_token()

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "content-type": "application/json"
    }
    old_balance = get_provider_balance(headers)

    print(f"\n✅ OLD BALANCE : {old_balance}")
    # =================================================
    # STEP 2 : LOAD WALLET
    # =================================================

    uploadAmount = random.randint(1, 100)

    wallet_payload = {
    "providerId": PROVIDER_ID,
    "uploadAmount": str(uploadAmount)
}

    print("\n========== WALLET LOAD REQUEST ==========")
    print(wallet_payload)

    wallet_response = requests.post(
        WALLET_LOAD_URL,
        json=wallet_payload,
        headers=headers
    )

    print("\n========== WALLET LOAD RESPONSE ==========")
    print("STATUS :", wallet_response.status_code)

    try:
        wallet_json = wallet_response.json()
        print(wallet_json)
    except:
        print(wallet_response.text)

    assert wallet_response.status_code in [200, 201]

    wallet_json = wallet_response.json()

    # =================================================
    # FETCH LOAD REQUEST ID
    # =================================================

    data = wallet_json.get("data")

    if data is None:
        raise Exception(
            f"Wallet Load API did not return data.\nFull Response: {wallet_json}"
        )

    # if data is list
    if isinstance(data, list):
        load_wallet_id = data[0].get("id")

    # if data is dict
    elif isinstance(data, dict):
        load_wallet_id = data.get("id")

    else:
        raise Exception(
            f"Unexpected data format : {type(data)}"
        )

    assert load_wallet_id is not None, \
        "Wallet Load ID Not Found"

    print("\n✅ LOAD WALLET ID :", load_wallet_id)

    # =================================================
    # STEP 3 : APPROVE WALLET LOAD
    # =================================================

    approve_payload = {
        "id": load_wallet_id,
        "status": "APPROVED"
    }

    print("\n========== APPROVE REQUEST ==========")
    print(approve_payload)

    approve_response = requests.post(
        PPROVE_WALLET_LOAD_URL,
        json=approve_payload,
        headers=headers
    )

    print("\n========== APPROVE RESPONSE ==========")
    print("STATUS :", approve_response.status_code)

    try:
        approve_json = approve_response.json()
        print(approve_json)
    except:
        print(approve_response.text)

    # =================================================
    # ASSERTIONS
    # =================================================

    assert approve_response.status_code in [200, 201]

    approve_json = approve_response.json()

    assert approve_json.get("success") == True

    print("\n✅ PROVIDER FUND LOAD APPROVED SUCCESSFULLY")

    new_balance = get_provider_balance(headers)

    print(f"\n✅ NEW BALANCE : {new_balance}")

    # =================================================
    # STEP 6 : VERIFY BALANCE
    # =================================================

    expected_balance = old_balance + uploadAmount

    print(f"\nEXPECTED BALANCE : {expected_balance}")
    print(f"ACTUAL BALANCE   : {new_balance}")

    assert new_balance == expected_balance, \
        (
            f"Balance mismatch!\n"
            f"Expected : {expected_balance}\n"
            f"Actual   : {new_balance}"
        )

    print("\n✅ BALANCE VERIFIED SUCCESSFULLY")