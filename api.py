#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime as _dt
import hashlib as _hashlib
import json as _json
import logging as _log
import random as _random
import re as _re
import uuid as _uuid
from argparse import ArgumentParser as _ArgumentParser
from http.server import BaseHTTPRequestHandler as _BaseHTTPRequestHandler, HTTPServer as _HTTPServer
from typing import Any, Dict, List, Tuple, Union, Optional

###############################################################################
# scoring.py fallback ---------------------------------------------------------
###############################################################################
try:
    import scoring  # type: ignore
except ModuleNotFoundError:  # pragma: no cover

    class _ScoringStub:  # pylint: disable=too-few-public-methods
        """Pure-Python replacement for missing *scoring.py* (demo only)."""

        @staticmethod
        def get_score(_store, phone=None, email=None, birthday=None, gender=None, first_name=None, last_name=None):  # type: ignore
            score = 0.0
            if phone:
                score += 1.5
            if email:
                score += 1.5
            if birthday and gender is not None:
                score += 1.5
            if first_name and last_name:
                score += 0.5
            return score

        @staticmethod
        def get_interests(_store, cid):  # type: ignore
            interests = [
                "cars",
                "pets",
                "travel",
                "hi-tech",
                "sport",
                "music",
                "books",
                "tv",
                "cinema",
                "geek",
                "otus",
            ]
            return _random.sample(interests, 2)

    scoring = _ScoringStub()  # type: ignore  # pylint: disable=invalid-name

###############################################################################
# Константы -------------------------------------------------------------------
###############################################################################
SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"

OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500

ERRORS: Dict[int, str] = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}

UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {UNKNOWN: "unknown", MALE: "male", FEMALE: "female"}

###############################################################################
# Слой Field-ов ---------------------------------------------------------------
###############################################################################


class FieldValidationError(ValueError):
    """Raised when a particular *Field* fails validation."""


class Field:  # pylint: disable=too-few-public-methods
    def __init__(self, *, required: bool = False, nullable: bool = False) -> None:
        self.required = bool(required)
        self.nullable = bool(nullable)
        self._name: Optional[str] = None

    # Descriptor protocol -------------------------------------------------
    def __set_name__(self, _owner, name):
        self._name = name

    def __get__(self, instance, _owner):
        return instance.__dict__.get(self._name) if instance is not None else self

    def __set__(self, instance, value):
        instance.__dict__[self._name] = value

    # Validation ----------------------------------------------------------
    def _is_empty(self, value):
        return value in (None, "", [], {}, ())

    def validate(self, value):
        if self._is_empty(value):
            if not self.nullable:
                raise FieldValidationError("value must not be empty")
            return
        self._validate(value)

    def _validate(self, value):  # noqa: D401
        raise NotImplementedError


class CharField(Field):
    def _validate(self, value):
        if not isinstance(value, str):
            raise FieldValidationError("must be a string")


class ArgumentsField(Field):
    def _validate(self, value):
        if not isinstance(value, dict):
            raise FieldValidationError("must be a dict")


class EmailField(CharField):
    _RE = _re.compile(r"[^@]+@[^@]+\.[^@]+")

    def _validate(self, value):
        super()._validate(value)
        if not self._RE.fullmatch(value):
            raise FieldValidationError("invalid email format")


class PhoneField(Field):
    _RE = _re.compile(r"7\d{10}")

    def _validate(self, value):
        if not self._RE.fullmatch(str(value)):
            raise FieldValidationError("must be 11 digits starting with '7'")


class DateField(Field):
    _FMT = "%d.%m.%Y"

    def _validate(self, value):
        if not isinstance(value, str):
            raise FieldValidationError("must be a string in DD.MM.YYYY format")
        try:
            _dt.datetime.strptime(value, self._FMT)
        except ValueError as exc:
            raise FieldValidationError("invalid date format") from exc


class BirthDayField(DateField):
    def _validate(self, value):
        super()._validate(value)
        bday = _dt.datetime.strptime(value, self._FMT).date()
        if (_dt.date.today() - bday).days / 365.2425 > 70:
            raise FieldValidationError("age must be <= 70 years")


class GenderField(Field):
    def _validate(self, value):
        if not isinstance(value, int) or value not in GENDERS:
            raise FieldValidationError("must be 0, 1 or 2")


class ClientIDsField(Field):
    def _validate(self, value):
        if not isinstance(value, list) or not value or not all(isinstance(i, int) for i in value):
            raise FieldValidationError("must be a non-empty list of integers")

###############################################################################
# Request-object layer --------------------------------------------------------
###############################################################################


class _RequestMeta(type):
    def __new__(mcs, name, bases, attrs):
        declared = {n: v for n, v in attrs.items() if isinstance(v, Field)}
        cls = super().__new__(mcs, name, bases, attrs)
        fields: Dict[str, Field] = {}
        for base in reversed(cls.__mro__):
            fields.update(getattr(base, "_fields", {}))
        fields.update(declared)
        cls._fields = fields  # type: ignore[attr-defined]
        return cls


class BaseRequest(metaclass=_RequestMeta):
    def __init__(self, **raw):
        self._errors: List[str] = []
        for name, field in self._fields.items():  # type: ignore[attr-defined]
            if name not in raw:
                if field.required:
                    self._errors.append(f"{name} is required")
                setattr(self, name, None)
                continue
            value = raw[name]
            try:
                field.validate(value)
            except FieldValidationError as exc:
                self._errors.append(f"{name}: {exc}")
            setattr(self, name, value)

    def is_valid(self):
        return not self._errors

    @property
    def errors(self):
        return ", ".join(self._errors)


class ClientsInterestsRequest(BaseRequest):
    """DTO for *clients_interests* method."""

    client_ids = ClientIDsField(required=True)
    date = DateField(nullable=True)


class OnlineScoreRequest(BaseRequest):
    """DTO for *online_score* method with cross-field validation."""

    first_name = CharField(nullable=True)
    last_name = CharField(nullable=True)
    email = EmailField(nullable=True)
    phone = PhoneField(nullable=True)
    birthday = BirthDayField(nullable=True)
    gender = GenderField(nullable=True)

    _PAIRS: Tuple[Tuple[str, str], ...] = (
        ("phone", "email"),
        ("first_name", "last_name"),
        ("gender", "birthday"),
    )

    @staticmethod
    def _is_set(value: Any) -> bool:
        """Return *True* for any non-empty value including 0 (gender)."""
        return value not in (None, "", [], {}, ())

    def __init__(self, **raw: Any) -> None:
        super().__init__(**raw)
        if not self._errors and not any(
            self._is_set(getattr(self, a)) and self._is_set(getattr(self, b))
            for a, b in self._PAIRS
        ):
            self._errors.append(
                "at least one pair (phone & email | first_name & last_name | gender & birthday) must be set"
            )


class MethodRequest(BaseRequest):
    """External RPC wrapper – carries auth + target method name."""

    account = CharField(nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True)

    @property
    def is_admin(self) -> bool:
        return self.login == ADMIN_LOGIN

###############################################################################
# Auth helper -----------------------------------------------------------------
###############################################################################


def check_auth(request: MethodRequest) -> bool:
    """Validate token and return *True* if correct."""
    if request.is_admin:
        digest_src = _dt.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
    else:
        digest_src = (request.account or "") + (request.login or "") + SALT
    digest = _hashlib.sha512(digest_src.encode("utf-8")).hexdigest()
    return digest == request.token

###############################################################################
# RPC-handlers ----------------------------------------------------------------
###############################################################################


def _handle_online_score(req: MethodRequest, ctx: Dict[str, Any], store: Any):
    score_req = OnlineScoreRequest(**req.arguments)
    if not score_req.is_valid():
        return score_req.errors, INVALID_REQUEST

    # which fields are actually present (0 counts as present)
    ctx["has"] = [
        f for f in score_req._fields  # type: ignore[attr-defined]
        if OnlineScoreRequest._is_set(getattr(score_req, f))
    ]

    if req.is_admin:
        score = 42
    else:
        score = scoring.get_score(
            store,
            phone=score_req.phone,
            email=score_req.email,
            birthday=score_req.birthday,
            gender=score_req.gender,
            first_name=score_req.first_name,
            last_name=score_req.last_name,
        )
    return {"score": score}, OK


def _handle_clients_interests(req: MethodRequest, ctx: Dict[str, Any], store: Any):
    interests_req = ClientsInterestsRequest(**req.arguments)
    if not interests_req.is_valid():
        return interests_req.errors, INVALID_REQUEST

    ctx["nclients"] = len(interests_req.client_ids)
    response = {cid: scoring.get_interests(store, cid) for cid in interests_req.client_ids}
    return response, OK


_METHOD_DISPATCH = {
    "online_score": _handle_online_score,
    "clients_interests": _handle_clients_interests,
}

###############################################################################
# Entry point for tests -------------------------------------------------------
###############################################################################


def method_handler(request: Dict[str, Any], ctx: Dict[str, Any], store: Any):
    body = request.get("body") or {}
    method_req = MethodRequest(**body)

    if not method_req.is_valid():
        return method_req.errors, INVALID_REQUEST

    if not check_auth(method_req):
        return ERRORS[FORBIDDEN], FORBIDDEN

    handler = _METHOD_DISPATCH.get(method_req.method)
    if handler is None:
        return ERRORS[NOT_FOUND], NOT_FOUND

    try:
        return handler(method_req, ctx, store)
    except Exception as exc:  # pragma: no cover
        _log.exception("Unexpected internal error: %s", exc)
        return ERRORS[INTERNAL_ERROR], INTERNAL_ERROR

###############################################################################
# HTTP transport -------------------------------------------------------------
###############################################################################


class MainHTTPHandler(_BaseHTTPRequestHandler):
    router = {"method": method_handler}
    store = None  # can be replaced with real storage

    def _request_id(self, headers):
        return headers.get("HTTP_X_REQUEST_ID", _uuid.uuid4().hex)

    def do_POST(self):  # noqa: D401
        code: int = OK
        response: Union[Dict[str, Any], str] = {}
        ctx: Dict[str, Any] = {"request_id": self._request_id(self.headers)}

        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            if not raw:
                request_json = {}
            else:
                try:
                    request_json = _json.loads(raw)
                except ValueError:
                    request_json = _json.loads(raw.decode("cp1251"))
        except Exception:
            code = BAD_REQUEST
            request_json = {}

        if code == OK:
            path = self.path.strip("/")
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request_json, "headers": self.headers}, ctx, self.store)
                except Exception as exc:  # pragma: no cover
                    _log.exception("Unexpected error: %s", exc)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        if code in ERRORS:
            payload = {"code": code, "error": response or ERRORS[code]}
        else:
            payload = {"code": code, "response": response}

        ctx.update(payload)
        _log.info(ctx)
        self.wfile.write(_json.dumps(payload).encode("utf-8"))

###############################################################################
# CLI launcher ---------------------------------------------------------------
###############################################################################


if __name__ == "__main__":
    parser = _ArgumentParser(description="Run scoring service HTTP server")
    parser.add_argument("-p", "--port", type=int, default=8080, help="port to bind (default: 8080)")
    parser.add_argument("-l", "--log", default=None, help="path to log-file (stdout if omitted)")
    args = parser.parse_args()

    _log.basicConfig(
        filename=args.log,
        level=_log.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )

    server = _HTTPServer(("localhost", args.port), MainHTTPHandler)
    _log.info("Starting server at port %s", args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover
        pass
    finally:
        server.server_close()
