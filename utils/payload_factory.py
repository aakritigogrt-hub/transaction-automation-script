import uuid

def get_valid_payload():
    return {
        "orderId": f"ORD_{uuid.uuid4().hex[:10]}",
        "amount": "100",
        "customerEmail": "shim@example.com",
        "customerMobile": "8211233876",
        "customerName": "shami",
        "transactionMode": "UPI_INTENT",
        "vpa": "success@ybl"
    }



def get_valid_payload_v2():
    return {
        "data": {
            "orderId": f"ORD_{uuid.uuid4().hex[:10]}",
            "amount": "100",
            "customerEmail": "shami@example.com",
            "customerMobile": "8211233876",
            "customerName": "shamu",
            "transactionMode": "UPI_INTENT",
            "vpa": "success@ybl"
        },
        "hexKey": "f0f0f92f9bfbac7770c99b9caca27b1499d10dc89643e76918e535b984053c5d"   # 👈 CENTRALIZED HERE
    }

def get_valid_payout_payload():
    return {
        "accountType": "savings",
        "amount": "500",
        "mode": "IMPS",
        "ifscCode": "HDFC0002671",
        "branchname": "",
        "accountNo": "98798899989",
        "beneName": "sham",
        "beneAddress": "sham",
        "beneEmail": "sham@gmail.com",
        "beneMobile": "9088030107",
        "orderId": str(uuid.uuid4())[:16]
    }

def get_v2_encrypt_payload():
    return {
        "data": {
        "accountType": "savings",
        "amount": "50",
        "mode": "IMPS",
        "ifscCode": "HDFC0002671",
        "branchname": "",
        "accountNo": "98798899989",
        "beneName": "sham",
        "beneAddress": "sham",
        "beneEmail": "sham@gmail.com",
        "beneMobile": "9088030107",
        "orderId": str(uuid.uuid4())[:16]
            
        },
        "hexKey": "f0f0f92f9bfbac7770c99b9caca27b1499d10dc89643e76918e535b984053c5d"
    }