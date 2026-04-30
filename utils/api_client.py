# import requests
# import time


# def send_payout(request, url, headers, payload):
#     start = time.time()

#     response = requests.post(url, headers=headers, json=payload)

#     log = {
#         "url": url,
#         "request": payload,
#         "status_code": response.status_code,
#         "response": safe_json(response),
#         "response_time": round(time.time() - start, 3)
#     }

#     # 🔥 Attach logs to test
#     if hasattr(request.node, "api_logs"):
#         request.node.api_logs.append(log)
#     else:
#         request.node.api_logs = [log]

#     return response


# def safe_json(response):
#     try:
#         return response.json()
#     except:
#         return response.text


import requests
import time

def send_request(request, method, url, headers=None, payload=None):
    print("🔥 FUNCTION CALLED")   # <-- ADD THIS FIRST

    import requests
    import time

    start = time.time()

    response = requests.post(url, headers=headers, json=payload)

    log = {
        "url": url,
        "request": payload,
        "status_code": response.status_code,
        "response": response.text
    }

    print("LOG ADDED:", log)   # <-- YOUR PRINT

    if not hasattr(request.node, "api_logs"):
        request.node.api_logs = []

    request.node.api_logs.append(log)

    return response