import uuid

def get_valid_payload():
    return {
        "email": "admintest@gmail.com",
        "password": "Test@99999",
        "recaptchaToken": "valid_token_dummy"
    }


def get_invalid_email_payload():
    payload = get_valid_payload()
    payload["email"] = "wrong@gmail.com"
    return payload


def get_invalid_password_payload():
    payload = get_valid_payload()
    payload["password"] = "Wrong@123"
    return payload


def get_empty_email_payload():
    payload = get_valid_payload()
    payload["email"] = ""
    return payload


def get_empty_password_payload():
    payload = get_valid_payload()
    payload["password"] = ""
    return payload


def get_missing_email_payload():
    payload = get_valid_payload()
    payload.pop("email")
    return payload


def get_missing_password_payload():
    payload = get_valid_payload()
    payload.pop("password")
    return payload


def get_invalid_recaptcha_payload():
    payload = get_valid_payload()
    payload["recaptchaToken"] = "invalid_token"
    return payload