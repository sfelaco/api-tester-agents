
import os
import uuid
import json
import datetime
import requests
import mysql.connector
from auth import get_oauth2_bearer_token

# DB connection
MYSQL_HOST = os.environ["MYSQL_HOST"]
if ":" in MYSQL_HOST:
    MYSQL_HOST, MYSQL_PORT = MYSQL_HOST.split(":")
    MYSQL_PORT = int(MYSQL_PORT)
else:
    MYSQL_PORT = 3306
MYSQL_SCHEMA = os.environ["MYSQL_SCHEMA"]
MYSQL_USER = os.environ["MYSQL_USER"]
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]

def get_db():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_SCHEMA,
        autocommit=True
    )

def insert_run_sequence(db):
    run_id = str(uuid.uuid4())
    now = datetime.datetime.now()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO run_sequence (id, date) VALUES (%s, %s)",
        (run_id, now)
    )
    cursor.close()
    return run_id

def insert_request(db, req):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO request (id, date, api, api_path, method, http_code, outcome, request, response, run_sequence) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            req["id"], req["date"], req["api"], req["api_path"], req["method"],
            req["http_code"], req["outcome"], json.dumps(req["request"]) if req["request"] is not None else None,
            json.dumps(req["response"]) if req["response"] is not None else None,
            req["run_sequence"]
        )
    )
    cursor.close()

def get_headers(token, extra=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    if extra:
        headers.update(extra)
    return headers

def get_api_key_headers():
    # For endpoints requiring api_key, use a dummy value
    return {"api_key": "test-api-key"}

BASE_URL = "https://petstore3.swagger.io/api/v3"

def now():
    return datetime.datetime.now()

def make_request(db, run_id, method, api, api_path, url, headers, params=None, data=None, json_data=None, files=None, expected_codes=None, expected_schema=None, req_body=None, test_type="example"):
    req_id = str(uuid.uuid4())
    dt = now()
    try:
        resp = requests.request(method, url, headers=headers, params=params, data=data, json=json_data, files=files)
        try:
            resp_json = resp.json()
        except Exception:
            resp_json = None
        http_code = resp.status_code
        # Determine outcome
        outcome = "OK"
        if expected_codes and http_code not in expected_codes:
            outcome = "FAILED"
        # If expected_schema is provided, do a basic check
        if expected_schema and resp_json is not None and outcome == "OK":
            if not validate_schema(resp_json, expected_schema):
                outcome = "FAILED"
        # For negative test, expect error code
        if test_type == "invalid" and http_code in (200, 201):
            outcome = "FAILED"
    except Exception as e:
        http_code = 0
        resp_json = {"error": str(e)}
        outcome = "FAILED"
    insert_request(db, {
        "id": req_id,
        "date": dt,
        "api": api,
        "api_path": api_path,
        "method": method,
        "http_code": http_code,
        "outcome": outcome,
        "request": req_body,
        "response": resp_json,
        "run_sequence": run_id
    })

def validate_schema(data, schema):
    # Only basic validation: check required fields and types
    if not isinstance(schema, dict):
        return True
    if "type" in schema:
        t = schema["type"]
        if t == "object":
            if not isinstance(data, dict):
                return False
            props = schema.get("properties", {})
            required = schema.get("required", [])
            for r in required:
                if r not in data:
                    return False
            for k, v in props.items():
                if k in data and not validate_schema(data[k], v):
                    return False
        elif t == "array":
            if not isinstance(data, list):
                return False
            items = schema.get("items", {})
            for d in data:
                if not validate_schema(d, items):
                    return False
        elif t == "string":
            if not isinstance(data, str):
                return False
        elif t == "integer":
            if not isinstance(data, int):
                return False
        elif t == "boolean":
            if not isinstance(data, bool):
                return False
    return True

# Example data generators
def example_pet():
    return {
        "id": 123456,
        "name": "doggie",
        "category": {"id": 1, "name": "Dogs"},
        "photoUrls": ["https://example.com/photo1.jpg"],
        "tags": [{"id": 1, "name": "tag1"}],
        "status": "available"
    }

def valid_pet():
    return {
        "id": 654321,
        "name": "catto",
        "category": {"id": 2, "name": "Cats"},
        "photoUrls": ["https://example.com/photo2.jpg"],
        "tags": [{"id": 2, "name": "tag2"}],
        "status": "pending"
    }

def invalid_pet():
    return {
        "id": "not-an-integer",
        "name": 123,  # should be string
        "category": "not-an-object",
        "photoUrls": "not-a-list",
        "tags": "not-a-list",
        "status": "not-a-status"
    }

def example_order():
    return {
        "id": 10,
        "petId": 198772,
        "quantity": 7,
        "shipDate": "2024-06-01T12:00:00Z",
        "status": "approved",
        "complete": True
    }

def valid_order():
    return {
        "id": 11,
        "petId": 654321,
        "quantity": 2,
        "shipDate": "2024-06-02T10:00:00Z",
        "status": "placed",
        "complete": False
    }

def invalid_order():
    return {
        "id": "bad",
        "petId": "bad",
        "quantity": "bad",
        "shipDate": "not-a-date",
        "status": "not-a-status",
        "complete": "not-a-bool"
    }

def example_user():
    return {
        "id": 10,
        "username": "theUser",
        "firstName": "John",
        "lastName": "James",
        "email": "john@email.com",
        "password": "12345",
        "phone": "12345",
        "userStatus": 1
    }

def valid_user():
    return {
        "id": 11,
        "username": "testuser",
        "firstName": "Alice",
        "lastName": "Smith",
        "email": "alice@example.com",
        "password": "password",
        "phone": "555-1234",
        "userStatus": 2
    }

def invalid_user():
    return {
        "id": "bad",
        "username": 123,
        "firstName": 456,
        "lastName": 789,
        "email": 12345,
        "password": 67890,
        "phone": 11111,
        "userStatus": "bad"
    }

def main():
    db = get_db()
    run_id = insert_run_sequence(db)
    token = get_oauth2_bearer_token()

    # 1. /pet POST (addPet)
    for test_type, pet in [("example", example_pet()), ("valid", valid_pet()), ("invalid", invalid_pet())]:
        make_request(
            db, run_id, "POST", "/pet", f"{BASE_URL}/pet", f"{BASE_URL}/pet",
            get_headers(token, {"Content-Type": "application/json"}),
            json_data=pet,
            expected_codes=[200, 201, 422, 400],
            expected_schema=None,
            req_body=pet,
            test_type=test_type
        )

    # 2. /pet PUT (updatePet)
    for test_type, pet in [("example", example_pet()), ("valid", valid_pet()), ("invalid", invalid_pet())]:
        make_request(
            db, run_id, "PUT", "/pet", f"{BASE_URL}/pet", f"{BASE_URL}/pet",
            get_headers(token, {"Content-Type": "application/json"}),
            json_data=pet,
            expected_codes=[200, 422, 400, 404],
            expected_schema=None,
            req_body=pet,
            test_type=test_type
        )

    # 3. /pet/findByStatus GET
    for test_type, status in [("example", "available"), ("valid", "pending"), ("invalid", "notastatus")]:
        params = {"status": status}
        make_request(
            db, run_id, "GET", "/pet/findByStatus", f"{BASE_URL}/pet/findByStatus?status={status}", f"{BASE_URL}/pet/findByStatus",
            get_headers(token),
            params=params,
            expected_codes=[200, 400],
            expected_schema=None,
            req_body=params,
            test_type=test_type
        )

    # 4. /pet/findByTags GET
    for test_type, tags in [("example", ["tag1"]), ("valid", ["tag2", "tag3"]), ("invalid", [123, None])]:
        params = {"tags": ",".join([str(t) for t in tags])}
        make_request(
            db, run_id, "GET", "/pet/findByTags", f"{BASE_URL}/pet/findByTags?tags={params['tags']}", f"{BASE_URL}/pet/findByTags",
            get_headers(token),
            params=params,
            expected_codes=[200, 400],
            expected_schema=None,
            req_body=params,
            test_type=test_type
        )

    # 5. /pet/{petId} GET
    for test_type, petId in [("example", 123456), ("valid", 654321), ("invalid", "badid")]:
        url = f"{BASE_URL}/pet/{petId}"
        make_request(
            db, run_id, "GET", "/pet/{petId}", url, url,
            get_headers(token),
            expected_codes=[200, 400, 404],
            expected_schema=None,
            req_body={"petId": petId},
            test_type=test_type
        )

    # 6. /pet/{petId} POST (updatePetWithForm)
    for test_type, petId, name, status in [
        ("example", 123456, "doggie", "available"),
        ("valid", 654321, "catto", "pending"),
        ("invalid", "badid", 123, 456)
    ]:
        url = f"{BASE_URL}/pet/{petId}"
        params = {}
        if name is not None:
            params["name"] = name
        if status is not None:
            params["status"] = status
        make_request(
            db, run_id, "POST", "/pet/{petId}", f"{url}?name={name}&status={status}", url,
            get_headers(token),
            params=params,
            expected_codes=[200, 400],
            expected_schema=None,
            req_body={"petId": petId, "name": name, "status": status},
            test_type=test_type
        )

    # 7. /pet/{petId} DELETE
    for test_type, petId in [("example", 123456), ("valid", 654321), ("invalid", "badid")]:
        url = f"{BASE_URL}/pet/{petId}"
        make_request(
            db, run_id, "DELETE", "/pet/{petId}", url, url,
            get_headers(token),
            expected_codes=[200, 400, 404],
            expected_schema=None,
            req_body={"petId": petId},
            test_type=test_type
        )

    # 8. /pet/{petId}/uploadImage POST
    for test_type, petId, meta, file_content in [
        ("example", 123456, "A nice photo", b"testimagecontent"),
        ("valid", 654321, "Another photo", b"anotherimage"),
        ("invalid", "badid", 123, "notbytes")
    ]:
        url = f"{BASE_URL}/pet/{petId}/uploadImage"
        params = {}
        if meta is not None:
            params["additionalMetadata"] = meta
        files = None
        data = None
        if isinstance(file_content, bytes):
            files = {"file": ("test.jpg", file_content, "application/octet-stream")}
        else:
            data = file_content
        make_request(
            db, run_id, "POST", "/pet/{petId}/uploadImage", url, url,
            get_headers(token),
            params=params,
            files=files,
            data=data,
            expected_codes=[200, 400, 404],
            expected_schema=None,
            req_body={"petId": petId, "additionalMetadata": meta, "file": str(file_content)},
            test_type=test_type
        )

    # 9. /store/inventory GET
    url = f"{BASE_URL}/store/inventory"
    for test_type in ["example", "valid", "invalid"]:
        make_request(
            db, run_id, "GET", "/store/inventory", url, url,
            get_headers(token, get_api_key_headers()),
            expected_codes=[200],
            expected_schema=None,
            req_body=None,
            test_type=test_type
        )

    # 10. /store/order POST
    for test_type, order in [("example", example_order()), ("valid", valid_order()), ("invalid", invalid_order())]:
        make_request(
            db, run_id, "POST", "/store/order", f"{BASE_URL}/store/order", f"{BASE_URL}/store/order",
            get_headers(token, {"Content-Type": "application/json"}),
            json_data=order,
            expected_codes=[200, 400, 422],
            expected_schema=None,
            req_body=order,
            test_type=test_type
        )

    # 11. /store/order/{orderId} GET
    for test_type, orderId in [("example", 10), ("valid", 11), ("invalid", "badid")]:
        url = f"{BASE_URL}/store/order/{orderId}"
        make_request(
            db, run_id, "GET", "/store/order/{orderId}", url, url,
            get_headers(token),
            expected_codes=[200, 400, 404],
            expected_schema=None,
            req_body={"orderId": orderId},
            test_type=test_type
        )

    # 12. /store/order/{orderId} DELETE
    for test_type, orderId in [("example", 10), ("valid", 11), ("invalid", 2000)]:
        url = f"{BASE_URL}/store/order/{orderId}"
        make_request(
            db, run_id, "DELETE", "/store/order/{orderId}", url, url,
            get_headers(token),
            expected_codes=[200, 400, 404],
            expected_schema=None,
            req_body={"orderId": orderId},
            test_type=test_type
        )

    # 13. /user POST
    for test_type, user in [("example", example_user()), ("valid", valid_user()), ("invalid", invalid_user())]:
        make_request(
            db, run_id, "POST", "/user", f"{BASE_URL}/user", f"{BASE_URL}/user",
            get_headers(token, {"Content-Type": "application/json"}),
            json_data=user,
            expected_codes=[200],
            expected_schema=None,
            req_body=user,
            test_type=test_type
        )

    # 14. /user/createWithList POST
    for test_type, users in [
        ("example", [example_user()]),
        ("valid", [valid_user(), example_user()]),
        ("invalid", [invalid_user(), 123])
    ]:
        make_request(
            db, run_id, "POST", "/user/createWithList", f"{BASE_URL}/user/createWithList", f"{BASE_URL}/user/createWithList",
            get_headers(token, {"Content-Type": "application/json"}),
            json_data=users,
            expected_codes=[200],
            expected_schema=None,
            req_body=users,
            test_type=test_type
        )

    # 15. /user/login GET
    for test_type, username, password in [
        ("example", "theUser", "12345"),
        ("valid", "testuser", "password"),
        ("invalid", "baduser", "badpass")
    ]:
        params = {"username": username, "password": password}
        url = f"{BASE_URL}/user/login?username={username}&password={password}"
        make_request(
            db, run_id, "GET", "/user/login", url, url,
            get_headers(token),
            params=params,
            expected_codes=[200, 400],
            expected_schema=None,
            req_body=params,
            test_type=test_type
        )

    # 16. /user/logout GET
    for test_type in ["example", "valid", "invalid"]:
        url = f"{BASE_URL}/user/logout"
        make_request(
            db, run_id, "GET", "/user/logout", url, url,
            get_headers(token),
            expected_codes=[200],
            expected_schema=None,
            req_body=None,
            test_type=test_type
        )

    # 17. /user/{username} GET
    for test_type, username in [
        ("example", "theUser"),
        ("valid", "testuser"),
        ("invalid", "baduser")
    ]:
        url = f"{BASE_URL}/user/{username}"
        make_request(
            db, run_id, "GET", "/user/{username}", url, url,
            get_headers(token),
            expected_codes=[200, 400, 404],
            expected_schema=None,
            req_body={"username": username},
            test_type=test_type
        )

    # 18. /user/{username} PUT
    for test_type, username, user in [
        ("example", "theUser", example_user()),
        ("valid", "testuser", valid_user()),
        ("invalid", "baduser", invalid_user())
    ]:
        url = f"{BASE_URL}/user/{username}"
        make_request(
            db, run_id, "PUT", "/user/{username}", url, url,
            get_headers(token, {"Content-Type": "application/json"}),
            json_data=user,
            expected_codes=[200, 400, 404],
            expected_schema=None,
            req_body=user,
            test_type=test_type
        )

    # 19. /user/{username} DELETE
    for test_type, username in [
        ("example", "theUser"),
        ("valid", "testuser"),
        ("invalid", "baduser")
    ]:
        url = f"{BASE_URL}/user/{username}"
        make_request(
            db, run_id, "DELETE", "/user/{username}", url, url,
            get_headers(token),
            expected_codes=[200, 400, 404],
            expected_schema=None,
            req_body={"username": username},
            test_type=test_type
        )

    # Print number of rows in request table
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM request")
    count = cursor.fetchone()[0]
    print(count)
    cursor.close()
    db.close()

if __name__ == "__main__":
    main()
