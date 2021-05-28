import requests
from base64 import b64encode as b64e

from fixtures import *

# i'm afraid this fixture will be hard to maintain
# it may drift from actual registration procedure
def test_correct_login(clean_redis, create_user):
    data = {"username": "testing", "remoteAddress": "tests", "connectionId": "randomstr", "sessionId": "anotherrandom", "passwordBase64": b64e(b"qwerty").decode()}
    resp = requests.post("http://authconfig:6823/password", json=data)

    print(f"Data: {resp.json()}")
    print(f"Status code: {resp.status_code}")

    status = resp.json()
    assert status["success"]

def test_wrong_login(clean_redis):
    data = {"username": "wrong", "remoteAddress": "tests", "connectionId": "hello", "sessinId": "yes", "passwordBase64": b64e(b"definitely_wrong").decode()}
    resp = requests.post("http://authconfig:6823/password", json=data)

    print(f"Data: {resp.json()}")
    print(f"Status code: {resp.status_code}")

    status = resp.json()
    assert not status["success"]
