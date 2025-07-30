#!/usr/bin/env python3
"""Minimal multithreaded HTTP/1.1 server for OTUS *HTTP-Server* homework.

* Вербозный **INFO**-трейс включается только при `-l info`.
* Без `-l` или при указании пути к файлу логируются только WARN/ERR.
* Pure stdlib: `socket`, `threading`, без сторонних HTTP-библиотек.
"""
from __future__ import annotations

import argparse
import email.utils
import logging
import os
import socket
import threading
from typing import Dict
from urllib.parse import unquote, urlsplit

# ---------------------------------------------------------------------------
# Constants & MIME map
# ---------------------------------------------------------------------------
SERVER_IDENT = "CustomPythonHTTP/0.1"
BUF_SIZE = 16_384  # bytes per recv
DEFAULT_PORT = 8080
DEFAULT_HOST = "0.0.0.0"
DEFAULT_WORKERS = 64  # soft limit on concurrent threads

_CONTENT_TYPES: Dict[str, str] = {
    ".html": "text/html",
    ".css":  "text/css",
    ".js":   "application/javascript",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".swf": "application/x-shockwave-flash",
}
_DEFAULT_CONTENT_TYPE = "application/octet-stream"

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def http_date() -> str:
    return email.utils.formatdate(timeval=None, usegmt=True)


def guess_content_type(path: str) -> str:
    return _CONTENT_TYPES.get(os.path.splitext(path.lower())[1], _DEFAULT_CONTENT_TYPE)


def response_line(code: int, phrase: str) -> bytes:
    return f"HTTP/1.1 {code} {phrase}\r\n".encode()


_STATUS_PHRASES = {
    200: "OK",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
}

# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

def handle_client(conn: socket.socket, addr, root: str) -> None:  # noqa: D401
    logging.info("[+] Accepted %s:%s", *addr)
    try:
        raw = b""
        while b"\r\n\r\n" not in raw and len(raw) < 10 * 1024:
            chunk = conn.recv(BUF_SIZE)
            if not chunk:
                break
            raw += chunk
        if not raw:
            logging.info("[-] Empty request from %s:%s", *addr)
            return

        try:
            headers_raw, _ = raw.split(b"\r\n\r\n", 1)
        except ValueError:
            logging.info("[!] Malformed headers from %s:%s", *addr)
            return

        request_line = headers_raw.decode(errors="ignore").split("\r\n")[0]
        logging.info("[>] %s", request_line)
        try:
            method, target, _ = request_line.split()
        except ValueError:
            logging.info("[!] Invalid request line from %s:%s", *addr)
            return

        method = method.upper()
        if method not in {"GET", "HEAD"}:
            send_error(conn, 405)
            return

        path = unquote(urlsplit(target).path).lstrip("/")
        fs_path = os.path.join(root, path)
        if target.endswith("/") or os.path.isdir(fs_path):
            fs_path = os.path.join(fs_path, "index.html")
        fs_path = os.path.realpath(fs_path)
        if not fs_path.startswith(os.path.realpath(root)):
            send_error(conn, 403)
            return
        if not os.path.exists(fs_path):
            send_error(conn, 404)
            return
        if not os.access(fs_path, os.R_OK):
            send_error(conn, 403)
            return

        with open(fs_path, "rb") as fp:
            content = fp.read() if method == "GET" else b""
        mime = guess_content_type(fs_path)
        conn.sendall(build_headers(200, len(content), mime) + content)
    except OSError:
        logging.exception("[!] Unhandled OSError")
    finally:
        conn.close()
        logging.info("[x] Closed %s:%s", *addr)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

def build_headers(code: int, length: int = 0, ctype: str | None = None, *, keep_alive: bool = False) -> bytes:
    parts: list[bytes] = [
        response_line(code, _STATUS_PHRASES.get(code, "")),
        f"Date: {http_date()}\r\n".encode(),
        f"Server: {SERVER_IDENT}\r\n".encode(),
        f"Connection: {'keep-alive' if keep_alive else 'close'}\r\n".encode(),
    ]
    if code == 200:
        parts.append(f"Content-Length: {length}\r\n".encode())
        if ctype:
            parts.append(f"Content-Type: {ctype}\r\n".encode())
    parts.append(b"\r\n")
    return b"".join(parts)


def send_error(conn: socket.socket, code: int) -> None:
    body = f"<h1>{code} {_STATUS_PHRASES.get(code)}</h1>".encode()
    conn.sendall(build_headers(code, len(body), "text/html; charset=utf-8") + body)

# ---------------------------------------------------------------------------
# Server loop
# ---------------------------------------------------------------------------

def serve(host: str, port: int, root: str, max_workers: int) -> None:
    root = os.path.realpath(root)
    sem = threading.Semaphore(max_workers)

    def _target(c: socket.socket, a):
        try:
            handle_client(c, a, root)
        finally:
            sem.release()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen()
        srv.settimeout(1)
        logging.info("[≈] Serving %s on %s:%s (workers=%d)", root, host, port, max_workers)

        while True:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                logging.warning("[!] Ctrl+C – stopping")
                break

            if not sem.acquire(blocking=False):
                logging.warning("[!] Workers exhausted – rejecting %s:%s", *addr)
                conn.close()
                continue
            threading.Thread(target=_target, args=(conn, addr), daemon=True).start()


# ---------------------------------------------------------------------------
# CLI & entry point
# ---------------------------------------------------------------------------

def parse_cli():
    p = argparse.ArgumentParser(description="Simple multithreaded HTTP server (OTUS HW)")
    p.add_argument("-r", "--root", default=os.getcwd(), help="DOCUMENT_ROOT (default: CWD)")
    p.add_argument("-p", "--port", type=int, default=DEFAULT_PORT, help="Port (default: 8080)")
    p.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help="Max worker threads")
    p.add_argument("-l", "--log", default=None, help="'info' for verbose stdout or path to log file")
    return p.parse_args()


def setup_logging(log_opt: str | None) -> None:
    fmt = "[%(asctime)s] %(levelname).1s %(message)s"
    dfmt = "%Y.%m.%d %H:%M:%S"
    if log_opt == "info":
        logging.basicConfig(level=logging.INFO, format=fmt, datefmt=dfmt)
    else:
        logging.basicConfig(filename=log_opt, level=logging.WARNING, format=fmt, datefmt=dfmt)


def main():  # noqa: D401
    args = parse_cli()
    setup_logging(args.log)
    try:
        serve(DEFAULT_HOST, args.port, args.root, args.workers)
    except KeyboardInterrupt:
        logging.warning("[!] Stopped by user")


if __name__ == "__main__":
    main()