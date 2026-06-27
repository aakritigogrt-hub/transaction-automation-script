import requests
import pytest

from ..config.base_url import BASE_URL
from ..config.headers import HEADERS
from ..utils.payload_factory import get_valid_payload

TIMEOUT = 30

PAYIN_URL = f"{BASE_URL}/api/v1/payments/requests"      # Change if your endpoint is different
STATUS_URL = f"{BASE_URL}/api/v1/admin/transactions/change-txn-status"
GET_TXN_URL = f"{BASE_URL}/api/v1/admin/transactions/get-txn-by-field"
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




def test_success_payment(auth_token):

    # Step 1 - Create Payin
    payload = get_valid_payload()

    response = requests.post(
        PAYIN_URL,
        headers=HEADERS,
        json=payload
    )

    assert response.status_code == 201

    data = response.json()
    order_id = data["ORDER_ID"]

    print(f"Generated Order ID: {order_id}")

    # Step 2 - Prepare Admin Headers
    admin_headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-skip": "true"
    }

    # Step 3 - Change Transaction Status
    status_payload = {
        "id": order_id,
        "utr": "",
        "status": "Success",
        "remark": ""
    }

    status_response = requests.post(
        STATUS_URL,
        headers=admin_headers,
        json=status_payload
    )

    print("Change Status Response:", status_response.text)

    assert status_response.status_code == 200

    # Step 4 - Fetch Transaction Details
    txn_response = requests.get(
        GET_TXN_URL,
        headers=admin_headers,
        params={
            "field": "requestOrderId",
            "id": order_id
        }
    )

    print("Get Transaction Response:", txn_response.text)

    assert txn_response.status_code == 200

    txn_data = txn_response.json()

    # Verify transaction exists
    assert txn_data.get("data") is not None

    # Verify order id
    assert txn_data["data"]["requestOrderId"] == order_id

    # Verify transaction status
    assert txn_data["response"]["RESPONSE_STATUS"] == "SUCCESS"