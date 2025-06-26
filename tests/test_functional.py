# tests/test_functional.py
import hashlib
import datetime
import pytest
from api import method_handler, OK, INVALID_REQUEST, FORBIDDEN, ADMIN_SALT, SALT

def gen_token(account, login, is_admin=False):
    if is_admin:
        raw = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
    else:
        raw = (account or "") + (login or "") + SALT
    return hashlib.sha512(raw.encode()).hexdigest()

def test_valid_online_score_user():
    token = gen_token("horns", "test")
    request = {
        "body": {
            "account": "horns",
            "login": "test",
            "method": "online_score",
            "token": token,
            "arguments": {
                "phone": "71234567890",
                "email": "email@test.com"
            }
        },
        "headers": {}
    }
    ctx = {}
    response, code = method_handler(request, ctx, None)
    assert code == OK
    assert isinstance(response, dict)
    assert "score" in response

def test_invalid_auth():
    request = {
        "body": {
            "account": "horns",
            "login": "test",
            "method": "online_score",
            "token": "invalid",
            "arguments": {
                "phone": "71234567890",
                "email": "email@test.com"
            }
        },
        "headers": {}
    }
    ctx = {}
    response, code = method_handler(request, ctx, None)
    assert code == FORBIDDEN

def test_admin_score_always_42():
    token = gen_token("horns", "admin", is_admin=True)
    request = {
        "body": {
            "account": "horns",
            "login": "admin",
            "method": "online_score",
            "token": token,
            "arguments": {
                "phone": "71234567890",
                "email": "email@test.com"
            }
        },
        "headers": {}
    }
    ctx = {}
    response, code = method_handler(request, ctx, None)
    assert code == OK
    assert response["score"] == 42
