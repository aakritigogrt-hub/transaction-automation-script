import requests
from ..config.base_url import BASE_URL
from ..config.headers import HEADERS
import pytest
import uuid
from ..utils.payload_factory import get_valid_payload
PAYIN_URL = f"{BASE_URL}/api/v1/payments/requests"
GET_TXN_URL = f"{BASE_URL}/api/v1/admin/transactions/get-txn-by-field"
PAYMENT_STATUS_URL = f"{BASE_URL}/api/v1/payments/status?isLookup=true"





LOGIN_URL = f"{BASE_URL}/api/v1/admin/auth/login"
LOGIN_PAYLOAD = {
    "email": "super@gmail.com",
    "password": "Admin@123",
    "recaptchaToken": "dummy_token"
}

COMMON_HEADERS = {
    "Content-Type": "application/json",
    "x-skip": "true"
}

@pytest.fixture(scope="session")
def auth_token():
    response = requests.post(
        LOGIN_URL,
        json=LOGIN_PAYLOAD,
        headers=COMMON_HEADERS
    )

    print("LOGIN RESPONSE:", response.text)

    assert response.status_code == 201

    token = (
        response.json().get("accessToken")
        or response.json().get("data", {}).get("accessToken")
    )

    assert token is not None, "Access token not found."

    return token

def test_payment_status(auth_token):

    # ==========================
    # Step 1 - Create Payin
    # ==========================
    payload = get_valid_payload()

    payin_response = requests.post(
        PAYIN_URL,
        headers=HEADERS,
        json=payload
    )

    assert payin_response.status_code == 201

    payin_data = payin_response.json()
    order_id = payin_data["ORDER_ID"]

    print("Order ID:", order_id)

    # ==========================
    # Step 2 - Admin Headers
    # ==========================
    admin_headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-skip": "true"
    }

    # ==========================
    # Step 3 - Get Transaction Details
    # ==========================
    txn_response = requests.get(
        GET_TXN_URL,
        headers=admin_headers,
        params={
            "field": "requestOrderId",
            "id": order_id
        }
    )

    assert txn_response.status_code == 200

    txn = txn_response.json()[0]      # Change this if your response structure differs

    transaction_id = txn["transactionId"]

    print("Transaction ID:", transaction_id)

    # ==========================
    # Step 4 - Payment Status API
    # ==========================
    status_payload = {
        "orderId": order_id,
        "transactionId": transaction_id
    }

    status_response = requests.post(
        PAYMENT_STATUS_URL,
        headers=admin_headers,
        json=status_payload
    )

    print(status_response.status_code)
    print(status_response.text)

    assert status_response.status_code == 201

    status_data = status_response.json()

    # Update these assertions according to your API response
    assert status_data is not None



def test_payment_status_invalid_order_id(auth_token):

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-skip": "true"
    }

    payload = {
        "orderId": f"ORD_{uuid.uuid4().hex[:10]}",
        "transactionId": str(uuid.uuid4())
    }

    response = requests.post(
        PAYMENT_STATUS_URL,
        headers=headers,
        json=payload
    )

    print(response.status_code)
    print(response.text)

    # Update according to your API

    assert response.status_code == 201

    data = response.json()

    assert data["RESPONSE_CODE"] == "999"
    assert data["RESPONSE_STATUS"] == "TRANSACTION_NOT_FOUND"