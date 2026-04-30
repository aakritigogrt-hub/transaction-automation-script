
import requests
import pytest
import json
import copy

from ..utils.payload_factory import get_valid_payload_v2
from ..config.headers import  API_HEADERS_V2


# ==============================
# V2 ENDPOINTS
# ==============================

BASE_URL_V2 = "https://staging.admin.kwicpe.com/api/api/v2"

ENCRYPT_URL = f"{BASE_URL_V2}/payin/encrypt"
INITIATE_URL = f"{BASE_URL_V2}/payin/requests"
DECRYPT_URL = f"{BASE_URL_V2}/payin/decrypt"

TIMEOUT = 10


# ==============================
# COMMON FLOW FUNCTION
# ==============================

def perform_full_flow(payload):

    # ---------------- Encrypt ----------------
    encrypt_res = requests.post(
        ENCRYPT_URL,
        headers=API_HEADERS_V2,
        json=payload,
        timeout=TIMEOUT
    )
    assert encrypt_res.status_code == 200, encrypt_res.text
    encrypt_json = encrypt_res.json()

    # ---------------- Initiate ----------------
    initiate_payload = {
        "iv": encrypt_json["iv"],
        "encryptedData": encrypt_json["encryptedData"],
        "authTag": encrypt_json["authTag"],
         # pass hexKey here for easier flow (instead of decrypt step)
    }

    initiate_res = requests.post(
        INITIATE_URL,
        headers=API_HEADERS_V2,   # 👈 V2 API KEY from config
        json=initiate_payload,
        timeout=TIMEOUT
    )
    assert initiate_res.status_code == 200, initiate_res.text
    initiate_json = initiate_res.json()

    # ---------------- Decrypt ----------------
    decrypt_payload = {
        "iv": initiate_json["iv"],
        "encryptedData": initiate_json["encryptedData"],
        "authTag": initiate_json["authTag"],
        "hexKey":"f0f0f92f9bfbac7770c99b9caca27b1499d10dc89643e76918e535b984053c5d"
    }

    decrypt_res = requests.post(
        DECRYPT_URL,
        headers=API_HEADERS_V2,
        json=decrypt_payload,
        timeout=TIMEOUT
    )
    assert decrypt_res.status_code == 200, decrypt_res.text

    decrypted = decrypt_res.json().get("decrypted", "")

    if decrypted and not decrypted.strip().startswith("{"):
        decrypted = "{" + decrypted

    return json.loads(decrypted)


# ==============================
# TEST CASES
# ==============================

def test_full_payin_flow():
    payload = get_valid_payload_v2()

    result = perform_full_flow(payload)

    print("\nFULL FLOW RESULT:", result)

    assert "RESPONSE_CODE" in result
    assert "RESPONSE_MESSAGE" in result


# ------------------------------
# DUPLICATE ORDER ID
# ------------------------------

def test_duplicate_order_id():
    payload = get_valid_payload_v2()

    payload["data"]["orderId"] = "DUPLICATE_12345"

    result = perform_full_flow(payload)

    print("\nDUPLICATE RESULT:", result)

    assert result.get("RESPONSE_CODE") in ["999", "FAILED"]



# ------------------------------
# MISSING HEXKEY
# ------------------------------

def test_missing_hexkey():
    payload = get_valid_payload_v2()

    payload["hexKey"] = ""

    r = requests.post(ENCRYPT_URL, headers=API_HEADERS_V2, json=payload)

    print("\nMISSING HEXKEY:", r.text)

    assert r.status_code in [400, 422]




def test_invalid_email():

    payload = get_valid_payload_v2()

    # -------------------------
    # INVALID DATA CHANGE
    # -------------------------
    payload["data"]["customerEmail"] = "invalid-email"

    # -------------------------
    # FULL FLOW STILL RUNS
    # -------------------------
    result = perform_full_flow(payload)

    print("\nINVALID EMAIL RESULT:", result)

    # -------------------------
    # ASSERTION (IMPORTANT)
    # -------------------------
    assert result.get("RESPONSE_CODE") == "999" or \
           "INVALID" in result.get("RESPONSE_MESSAGE", "").upper() or \
           "EMAIL" in result.get("RESPONSE_MESSAGE", "").upper()



def test_invalid_customer_mobile():
    payload = get_valid_payload_v2()
    payload["data"]["customerMobile"] = "12345"

    result = perform_full_flow(payload)

    print("INVALID MOBILE RESPONSE:", result)

    assert result["RESPONSE_CODE"] in ["999", "400", "422"]


def test_missing_order_id():
    payload = get_valid_payload_v2()
    payload["data"].pop("orderId")

    result = perform_full_flow(payload)

    print("MISSING ORDERID RESPONSE:", result)

  


# =========================
# MISSING AMOUNT
# =========================

def test_missing_amount():
    payload = get_valid_payload_v2()
    payload["data"].pop("amount")

    result = perform_full_flow(payload)

    print("MISSING AMOUNT RESPONSE:", result)
    assert result["statusCode"] == 400

   


# =========================
# INVALID AMOUNT FORMAT
# =========================

def test_invalid_amount():
    payload = get_valid_payload_v2()
    payload["data"]["amount"] = "abc"

    result = perform_full_flow(payload)

    print("INVALID AMOUNT RESPONSE:", result)
    assert result["statusCode"] == 400
