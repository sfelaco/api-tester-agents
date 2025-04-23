
import os
import uuid
import json
import datetime
import requests
import mysql.connector
from auth import get_oauth2_bearer_token

# DB connection
MYSQL_HOST = os.environ['MYSQL_HOST']
MYSQL_SCHEMA = os.environ['MYSQL_SCHEMA']
MYSQL_USER = os.environ['MYSQL_USER']
MYSQL_PASSWORD = os.environ['MYSQL_PASSWORD']

host, port = MYSQL_HOST.split(':')
port = int(port)

conn = mysql.connector.connect(
    host=host,
    port=port,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_SCHEMA,
    autocommit=True
)
cursor = conn.cursor()

def ensure_tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS run_sequence (
        id VARCHAR(36) PRIMARY KEY,
        date DATETIME
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS request (
        id VARCHAR(36) PRIMARY KEY,
        date DATETIME,
        api VARCHAR(256),
        api_path VARCHAR(512),
        method VARCHAR(10),
        http_code INT,
        outcome VARCHAR(10),
        request JSON,
        response JSON,
        run_sequence VARCHAR(36),
        CONSTRAINT run_sequence_fk FOREIGN KEY (run_sequence) REFERENCES run_sequence(id)
    )
    """)

ensure_tables()

def now():
    return datetime.datetime.now().replace(microsecond=0)

def insert_run_sequence(run_id, date):
    cursor.execute(
        "INSERT INTO run_sequence (id, date) VALUES (%s, %s)",
        (run_id, date)
    )

def insert_request(**kwargs):
    cursor.execute(
        """INSERT INTO request
        (id, date, api, api_path, method, http_code, outcome, request, response, run_sequence)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            kwargs['id'],
            kwargs['date'],
            kwargs['api'],
            kwargs['api_path'],
            kwargs['method'],
            kwargs['http_code'],
            kwargs['outcome'],
            json.dumps(kwargs['request']) if kwargs['request'] is not None else None,
            json.dumps(kwargs['response']) if kwargs['response'] is not None else None,
            kwargs['run_sequence']
        )
    )

BASE_URL = "https://petstore3.swagger.io/api/v3"

def get_headers(auth=True, extra=None):
    headers = {}
    if auth:
        token = get_oauth2_bearer_token()
        headers['Authorization'] = f"Bearer {token}"
    if extra:
        headers.update(extra)
    return headers

def check_pet_response(resp, expected_code, expected_fields=None):
    if resp.status_code != expected_code:
        return "FAILED"
    if expected_fields:
        try:
            data = resp.json()
            for f in expected_fields:
                if f not in data:
                    return "FAILED"
        except Exception:
            return "FAILED"
    return "OK"

def check_order_response(resp, expected_code):
    if resp.status_code != expected_code:
        return "FAILED"
    return "OK"

def check_user_response(resp, expected_code):
    if resp.status_code != expected_code:
        return "FAILED"
    return "OK"

def check_inventory_response(resp, expected_code):
    if resp.status_code != expected_code:
        return "FAILED"
    try:
        data = resp.json()
        if not isinstance(data, dict):
            return "FAILED"
    except Exception:
        return "FAILED"
    return "OK"

def check_api_response(resp, expected_code):
    if resp.status_code != expected_code:
        return "FAILED"
    return "OK"

def check_login_response(resp, expected_code):
    if resp.status_code != expected_code:
        return "FAILED"
    return "OK"

def check_logout_response(resp, expected_code):
    if resp.status_code != expected_code:
        return "FAILED"
    return "OK"

def check_delete_response(resp, expected_code):
    if resp.status_code != expected_code:
        return "FAILED"
    return "OK"

def check_upload_response(resp, expected_code):
    if resp.status_code != expected_code:
        return "FAILED"
    return "OK"

run_id = str(uuid.uuid4())
insert_run_sequence(run_id, now())

# --- API TESTS ---

# Helper data
pet_example = {
    "id": 10,
    "name": "doggie",
    "category": {"id": 1, "name": "Dogs"},
    "photoUrls": ["https://example.com/photo1.jpg"],
    "tags": [{"id": 1, "name": "tag1"}],
    "status": "available"
}
pet_valid = {
    "id": 123456,
    "name": "Fuffy",
    "category": {"id": 2, "name": "Cats"},
    "photoUrls": ["https://example.com/cat.jpg"],
    "tags": [{"id": 2, "name": "cute"}],
    "status": "pending"
}
pet_invalid = {
    "id": "notanint",
    "name": 123,
    "category": "notanobject",
    "photoUrls": "notalist",
    "tags": "notalist",
    "status": "notvalid"
}

order_example = {
    "id": 10,
    "petId": 198772,
    "quantity": 7,
    "shipDate": "2024-06-01T12:00:00Z",
    "status": "approved",
    "complete": True
}
order_valid = {
    "id": 11,
    "petId": 123456,
    "quantity": 2,
    "shipDate": "2024-06-02T10:00:00Z",
    "status": "placed",
    "complete": False
}
order_invalid = {
    "id": "badid",
    "petId": "badpetid",
    "quantity": "notanint",
    "shipDate": "notadate",
    "status": "notvalid",
    "complete": "notabool"
}

user_example = {
    "id": 10,
    "username": "theUser",
    "firstName": "John",
    "lastName": "James",
    "email": "john@email.com",
    "password": "12345",
    "phone": "12345",
    "userStatus": 1
}
user_valid = {
    "id": 20,
    "username": "testuser",
    "firstName": "Alice",
    "lastName": "Smith",
    "email": "alice@example.com",
    "password": "password",
    "phone": "555-1234",
    "userStatus": 2
}
user_invalid = {
    "id": "badid",
    "username": 123,
    "firstName": 456,
    "lastName": 789,
    "email": 12345,
    "password": 67890,
    "phone": 11111,
    "userStatus": "notanint"
}

# 1. /pet POST (addPet)
for idx, req in enumerate([pet_example, pet_valid, pet_invalid]):
    url = f"{BASE_URL}/pet"
    method = "POST"
    headers = get_headers()
    data = req
    resp = requests.post(url, headers=headers, json=data)
    outcome = "OK" if (idx < 2 and resp.status_code == 200) or (idx == 2 and resp.status_code in (400, 422)) else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/pet",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request=data,
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 2. /pet PUT (updatePet)
for idx, req in enumerate([pet_example, pet_valid, pet_invalid]):
    url = f"{BASE_URL}/pet"
    method = "PUT"
    headers = get_headers()
    data = req
    resp = requests.put(url, headers=headers, json=data)
    outcome = "OK" if (idx < 2 and resp.status_code == 200) or (idx == 2 and resp.status_code in (400, 422, 404)) else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/pet",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request=data,
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 3. /pet/findByStatus GET
for idx, status in enumerate(["available", "pending", "notvalid"]):
    url = f"{BASE_URL}/pet/findByStatus"
    method = "GET"
    headers = get_headers()
    params = {"status": status}
    resp = requests.get(url, headers=headers, params=params)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code == 400 else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/pet/findByStatus",
        api_path=resp.url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request=params,
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 4. /pet/findByTags GET
for idx, tags in enumerate([["tag1"], ["cute", "fluffy"], [123, None]]):
    url = f"{BASE_URL}/pet/findByTags"
    method = "GET"
    headers = get_headers()
    params = {"tags": ",".join([str(t) for t in tags])}
    resp = requests.get(url, headers=headers, params=params)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code == 400 else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/pet/findByTags",
        api_path=resp.url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request=params,
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 5. /pet/{petId} GET
for idx, petId in enumerate([10, pet_valid["id"], "notanid"]):
    url = f"{BASE_URL}/pet/{petId}"
    method = "GET"
    headers = get_headers()
    resp = requests.get(url, headers=headers)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code in (400, 404) else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/pet/{petId}",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request={"petId": petId},
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 6. /pet/{petId} POST (updatePetWithForm)
for idx, (petId, name, status) in enumerate([
    (10, "doggie", "available"),
    (pet_valid["id"], "Fuffy", "pending"),
    ("notanid", 123, "notvalid")
]):
    url = f"{BASE_URL}/pet/{petId}"
    method = "POST"
    headers = get_headers()
    params = {}
    if name is not None:
        params["name"] = name
    if status is not None:
        params["status"] = status
    resp = requests.post(url, headers=headers, params=params)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code == 400 else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/pet/{petId}",
        api_path=resp.url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request={"petId": petId, "name": name, "status": status},
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 7. /pet/{petId} DELETE
for idx, petId in enumerate([10, pet_valid["id"], "notanid"]):
    url = f"{BASE_URL}/pet/{petId}"
    method = "DELETE"
    headers = get_headers()
    resp = requests.delete(url, headers=headers)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code in (400, 404) else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/pet/{petId}",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request={"petId": petId},
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 8. /pet/{petId}/uploadImage POST
for idx, (petId, meta, filedata) in enumerate([
    (10, "A dog photo", b"testimagebytes"),
    (pet_valid["id"], "A cat photo", b"catimagebytes"),
    ("notanid", 123, None)
]):
    url = f"{BASE_URL}/pet/{petId}/uploadImage"
    method = "POST"
    headers = get_headers()
    files = None
    data = None
    params = {}
    if meta is not None:
        params["additionalMetadata"] = meta
    if filedata is not None:
        files = {'file': ('test.jpg', filedata, 'application/octet-stream')}
    resp = requests.post(url, headers=headers, params=params, files=files)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code in (400, 404) else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/pet/{petId}/uploadImage",
        api_path=resp.url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request={"petId": petId, "additionalMetadata": meta},
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 9. /store/inventory GET
for idx in range(3):
    url = f"{BASE_URL}/store/inventory"
    method = "GET"
    headers = get_headers(auth=False, extra={"api_key": "special-key"})
    resp = requests.get(url, headers=headers)
    outcome = "OK" if resp.status_code == 200 else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/store/inventory",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request=None,
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 10. /store/order POST (placeOrder)
for idx, req in enumerate([order_example, order_valid, order_invalid]):
    url = f"{BASE_URL}/store/order"
    method = "POST"
    headers = get_headers()
    data = req
    resp = requests.post(url, headers=headers, json=data)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code in (400, 422) else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/store/order",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request=data,
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 11. /store/order/{orderId} GET
for idx, orderId in enumerate([10, order_valid["id"], "notanid"]):
    url = f"{BASE_URL}/store/order/{orderId}"
    method = "GET"
    headers = get_headers()
    resp = requests.get(url, headers=headers)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code in (400, 404) else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/store/order/{orderId}",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request={"orderId": orderId},
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 12. /store/order/{orderId} DELETE
for idx, orderId in enumerate([10, order_valid["id"], "notanid"]):
    url = f"{BASE_URL}/store/order/{orderId}"
    method = "DELETE"
    headers = get_headers()
    resp = requests.delete(url, headers=headers)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code in (400, 404) else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/store/order/{orderId}",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request={"orderId": orderId},
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 13. /user POST (createUser)
for idx, req in enumerate([user_example, user_valid, user_invalid]):
    url = f"{BASE_URL}/user"
    method = "POST"
    headers = get_headers()
    data = req
    resp = requests.post(url, headers=headers, json=data)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code != 200 else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/user",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request=data,
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 14. /user/createWithList POST
for idx, req in enumerate([[user_example], [user_valid, user_example], [user_invalid, user_example]]):
    url = f"{BASE_URL}/user/createWithList"
    method = "POST"
    headers = get_headers()
    data = req
    resp = requests.post(url, headers=headers, json=data)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code != 200 else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/user/createWithList",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request=data,
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 15. /user/login GET
for idx, (username, password) in enumerate([
    ("theUser", "12345"),
    ("testuser", "password"),
    (123, None)
]):
    url = f"{BASE_URL}/user/login"
    method = "GET"
    headers = get_headers()
    params = {"username": username, "password": password}
    resp = requests.get(url, headers=headers, params=params)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code == 400 else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/user/login",
        api_path=resp.url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request=params,
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 16. /user/logout GET
for idx in range(3):
    url = f"{BASE_URL}/user/logout"
    method = "GET"
    headers = get_headers()
    resp = requests.get(url, headers=headers)
    outcome = "OK" if resp.status_code == 200 else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/user/logout",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request=None,
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 17. /user/{username} GET
for idx, username in enumerate(["theUser", "testuser", 123]):
    url = f"{BASE_URL}/user/{username}"
    method = "GET"
    headers = get_headers()
    resp = requests.get(url, headers=headers)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code in (400, 404) else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/user/{username}",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request={"username": username},
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 18. /user/{username} PUT
for idx, (username, req) in enumerate([
    ("theUser", user_example),
    ("testuser", user_valid),
    (123, user_invalid)
]):
    url = f"{BASE_URL}/user/{username}"
    method = "PUT"
    headers = get_headers()
    data = req
    resp = requests.put(url, headers=headers, json=data)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code in (400, 404) else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/user/{username}",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request=data,
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# 19. /user/{username} DELETE
for idx, username in enumerate(["theUser", "testuser", 123]):
    url = f"{BASE_URL}/user/{username}"
    method = "DELETE"
    headers = get_headers()
    resp = requests.delete(url, headers=headers)
    if idx < 2:
        outcome = "OK" if resp.status_code == 200 else "FAILED"
    else:
        outcome = "OK" if resp.status_code in (400, 404) else "FAILED"
    insert_request(
        id=str(uuid.uuid4()),
        date=now(),
        api="/user/{username}",
        api_path=url,
        method=method,
        http_code=resp.status_code,
        outcome=outcome,
        request={"username": username},
        response=resp.json() if resp.content else None,
        run_sequence=run_id
    )

# Print number of rows in request table
cursor.execute("SELECT COUNT(*) FROM request")
print(cursor.fetchone()[0])
