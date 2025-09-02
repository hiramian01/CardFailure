import requests
import json
import getpass


def get_token(username, password):
    """Authenticate and return access token"""
    payload = {
        "username": username,
        "password": password   
    }

    response = requests.post(
        url = 'http://t2-log-collector.verizon.com:9999/token', 
        json=payload, 
        timeout = (30, 200), 
        auth = (username, password)
    )

    response.raise_for_status   #raise error if auth fails
    return response.json().get("access_token")


def create_case(token, payload):
    """Create a case"""

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        url = 'http://t2-log-collector.verizon.com:9999/createCase', 
        json=payload, 
        timeout = (30, 200), 
        headers=headers
    )

    response.raise_for_status   #raise error if auth fails
    return response.json().get("CaseNumber")


def get_case_info(token, case): 
    """Retrieves information regarding a case"""

    headers = {
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "case": case
    }
    response = requests.get(
        url = 'http://t2-log-collector.verizon.com:9999/cases', 
        json=payload, 
        timeout = (30, 200), 
        headers=headers
    )
    response.raise_for_status   #raise error if auth fails
    return response.json()


if __name__ == '__main__':

    #credentials
    username = "collector"
    password = "collector!!!"

    payload = {
        "tid": "testingtid12345",
        "vendor": "Ciena",
        "caseType": "Standard",
        "ContactEmail": "hira.mian@verizon.com",
        "BusinessImpact": "Degraded Performance/Capacity",
        "Subject": "Testing from API",
        "ProblemDescription": "Testing from the API"
    }

    try:
        token = get_token(username, password)
        print("Access Token:", token)

        case = create_case(token, payload)
        print("Created Case:", case)

        result = get_case_info(token, case)
        print("Created Case Info\n:", result)

    except requests.exceptions.RequestException as e:
        print("Error during API call:", e)








