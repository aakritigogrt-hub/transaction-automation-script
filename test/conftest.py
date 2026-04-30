import pytest
import requests
import time
import json
import os

REPORT_FILE = "reports/final_report.json"
results = []


# =========================
# AUTO PATCH REQUESTS
# =========================
@pytest.fixture(autouse=True)
def capture_api_calls(request, monkeypatch):
    logs = []

    original_post = requests.post

    def patched_post(*args, **kwargs):
        start = time.time()

        response = original_post(*args, **kwargs)

        log = {
            "url": args[0] if args else kwargs.get("url"),
            "method": "POST",
            "headers": kwargs.get("headers"),
            "request_body": kwargs.get("json"),
            "status_code": response.status_code,
            "response_body": safe_json(response),
            "response_time": round(time.time() - start, 3)
        }

        print("🔥 AUTO LOG:", log)   # DEBUG

        logs.append(log)
        return response

    monkeypatch.setattr(requests, "post", patched_post)

    # attach logs to test
    request.node.api_logs = logs


def safe_json(response):
    try:
        return response.json()
    except:
        return response.text


# =========================
# REPORT GENERATION
# =========================
def pytest_sessionstart(session):
    os.makedirs("reports", exist_ok=True)


def pytest_runtest_makereport(item, call):
    if call.when == "call":
        result = {
            "test_name": item.name,
            "status": "PASSED" if call.excinfo is None else "FAILED",
        }

        if hasattr(item, "api_logs"):
            result["api_logs"] = item.api_logs

        if call.excinfo:
            result["error"] = str(call.excinfo.value)

        results.append(result)


def pytest_sessionfinish(session, exitstatus):
    with open(REPORT_FILE, "w") as f:
        json.dump(results, f, indent=2)