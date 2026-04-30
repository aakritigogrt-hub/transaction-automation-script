

import pytest
import requests
import json

from ..config.headers import  API_HEADERS_V2
from ..utils.payload_factory import get_v2_encrypt_payload
# =========================
# URLS
# =========================

BASE_URL = "https://staging.admin.kwicpe.com/api/api/v2"

ENCRYPT_URL = f"{BASE_URL}/payin/encrypt"
INITIATE_URL = f"{BASE_URL}/withdrawal/initiate"
DECRYPT_URL = f"{BASE_URL}/payin/decrypt"

TIMEOUT = 15


# =========================
# COMMON FLOW
# =========================

def full_flow(payload):
    # payload = get_v2_encrypt_payload()
    # ENCRYPT
    enc_res = requests.post(ENCRYPT_URL, headers=API_HEADERS_V2, json=payload, timeout=TIMEOUT)
    assert enc_res.status_code == 200, enc_res.text
    enc_json = enc_res.json()

    # INITIATE
    initiate_payload = {
        "iv": enc_json["iv"],
        "encryptedData": enc_json["encryptedData"],
        "authTag": enc_json["authTag"]
    }

    init_res = requests.post(
        INITIATE_URL,
        headers=API_HEADERS_V2,
        json=initiate_payload,
        timeout=TIMEOUT
    )
    assert init_res.status_code == 200, init_res.text
    init_json = init_res.json()

    # DECRYPT
    decrypt_payload = {
        "iv": init_json["iv"],
        "encryptedData": init_json["encryptedData"],
        "authTag": init_json["authTag"],
        "hexKey": payload["hexKey"]
    }

    dec_res = requests.post(DECRYPT_URL, headers=API_HEADERS_V2, json=decrypt_payload, timeout=TIMEOUT)
    assert dec_res.status_code == 200, dec_res.text

    decrypted = dec_res.json().get("decrypted", "")

    # Fix malformed JSON if needed
    if decrypted and not decrypted.strip().startswith("{"):
        decrypted = "{" + decrypted

    return json.loads(decrypted)


# =========================
# TEST CASES
# =========================

def test_success():
    payload = get_v2_encrypt_payload()
    res = full_flow(payload)
    print("SUCCESS:", res)
    assert "RESPONSE_CODE" in res


def test_invalid_mobile():
    payload = get_v2_encrypt_payload()
    payload["data"]["beneMobile"] = "123"
    print(payload)
    res = full_flow(payload)
    assert res["RESPONSE_CODE"] == "999"

def test_invalid_email():
    payload = get_v2_encrypt_payload()
    payload["data"]["beneEmail"] = "invalid-email"

    res = full_flow(payload)
    assert res["RESPONSE_CODE"] == "999"

def test_invalid_amount_encrypt():
    payload = get_v2_encrypt_payload()
    payload["data"]["amount"] = "abc"

    res = full_flow(payload)
    assert res["statusCode"] == 400
def test_missing_amount():
    payload = get_v2_encrypt_payload()
    payload["data"].pop("amount")

    res = full_flow(payload)
    print("MISSING AMOUNT:", res)
    assert res["statusCode"] == 400
    
def test_invalid_ifsc():
    payload = get_v2_encrypt_payload()
    payload["data"]["ifscCode"] = "INVALID123"

    res = full_flow(payload)
    print("INVALID IFSC:", res)

    assert res["RESPONSE_CODE"] == "999"
       
  





