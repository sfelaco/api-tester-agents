import os
from dotenv import load_dotenv
import requests

load_dotenv()

def get_bearer_token():
    
    print("Retrieving bearer token...")
    
    idm_endpoint = os.environ.get("IDM_URL")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    
    if not all([idm_endpoint, client_id, client_secret]):
        missing = []
        if not idm_endpoint: missing.append("IDM_URL")
        if not client_id: missing.append("CLIENT_ID")
        if not client_secret: missing.append("CLIENT_SECRET")
        raise ValueError(f"Env variables missing: {', '.join(missing)}")
    
    url = idm_endpoint

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    response = requests.post(url, data=payload)

    if response.status_code != 200:
        print("getTokenRequest failed:")
        print(f"Status Code: {response.status_code}")
        print(response.text)
        return None
    else:
        response_body = response.text

        if not response_body:
            print("Empty response")
            return None
        else:
            json_data = response.json()
            bearer_token = json_data.get("access_token")
            return f"Bearer {bearer_token}"


if __name__ == "__main__":
    token = get_bearer_token()
    if token:
        print(token)
    else:
        print("Failed to retrieve bearer token.")
