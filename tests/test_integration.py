# tests/test_integration.py
import pytest
from api import scoring

class DummyStore:
    def __init__(self):
        self.calls = []

    def get(self, key):
        self.calls.append(key)
        return "dummy"

def test_get_score_with_store():
    store = DummyStore()
    result = scoring.get_score(
        store,
        phone="71234567890",
        email="test@test.com",
        birthday="01.01.1990",
        gender=1,
        first_name="A",
        last_name="B"
    )
    assert isinstance(result, float)
    assert result > 0
