# tests/test_fields.py
import pytest
from api import EmailField, PhoneField, GenderField, BirthDayField, FieldValidationError
from datetime import datetime

def test_email_field_valid():
    field = EmailField()
    field.validate("test@example.com")

def test_email_field_invalid():
    field = EmailField()
    with pytest.raises(FieldValidationError):
        field.validate("invalid-email")

def test_phone_field_valid():
    field = PhoneField()
    field.validate("71234567890")

def test_phone_field_invalid():
    field = PhoneField()
    with pytest.raises(FieldValidationError):
        field.validate("81234567890")

def test_gender_field_valid():
    for value in [0, 1, 2]:
        GenderField().validate(value)

def test_gender_field_invalid():
    with pytest.raises(FieldValidationError):
        GenderField().validate(5)

def test_birthday_field_too_old():
    field = BirthDayField()
    with pytest.raises(FieldValidationError):
        field.validate("01.01.1900")

def test_birthday_field_valid():
    field = BirthDayField()
    field.validate("01.01.1990")
