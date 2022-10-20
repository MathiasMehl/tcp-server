import socket
import threading
import http
import time
from apscheduler.schedulers.background import BackgroundScheduler
from dataclasses import dataclass

@dataclass
class Request:
    method: str
    url: str
    version: str

HOST = '127.0.0.1'
PORT = 8002
TIMEOUT = 30
PRINT_LOCK = threading.Lock()
SCHEDULER = BackgroundScheduler()

def print_with_lock(arg):
    with PRINT_LOCK:
        current_thead_name = threading.current_thread().getName()
        thread_name = current_thead_name if current_thead_name.startswith("CLIENT") else "SERVER"
        print(f"[{thread_name}]" + arg)


def print_num_active_connections():
    active_threads = 0
    for thread in threading.enumerate():
        if thread.getName().startswith("CLIENT"):
            active_threads += 1
    print_with_lock(f" Active connections: {active_threads}")


def print_response_status(method, url, status_code):
    print_with_lock(f" issued a '{method}' request to URL '{url}' "
                    f"request handled with status code: '{status_code} {http.HTTPStatus(status_code).phrase}'")


def create_http_response(status_code, body):
    reason_phrase = http.HTTPStatus(status_code).phrase
    return f"HTTP/1.1 {status_code} {reason_phrase}\r\n\r\n{body}".encode("UTF-8")


def send_and_print_http_response(conn, method, url, status_code, message_body):
    conn.sendall(create_http_response(status_code, message_body))
    print_response_status(method, url, status_code)


def handle_ping(conn):
    print_with_lock(" pinged server")
    conn.send("pong".encode())
    conn.close()


def handle_http_request(conn, request):
    if method == "GET":
        if url == "/":
            static_web_page = open('hello.html', 'r').read()

            send_and_print_http_response(conn, request.method, request.url, status_code=200, message_body=static_web_page)
        else:
            send_and_print_http_response(conn, request.method, request.url, status_code=404, message_body="")
    elif method == "TRACE":
        send_and_print_http_response(conn, request.method, request.url, status_code=200, message_body=request.url)
    elif method == "OPTIONS":
        send_and_print_http_response(conn, request.method, request.url, status_code=200, message_body=
        "(GET/HEAD (only at '/'), TRACE")
    elif method == "HEAD":
        if url == "/":
            static_web_page = open('hello.html', 'r').read()

            send_and_print_http_response(conn, request.method, request.url, status_code=200, message_body=
            f"'HTML document' with size: {len(static_web_page)} \n last modified: Some time ago")
        else:
            send_and_print_http_response(conn, request.method, request.url, status_code=404, message_body="")
    elif method == "PUT" or method == "POST" or method == "DELETE":
        send_and_print_http_response(conn, request.method, request.url, status_code=501, message_body="")
    else:
        send_and_print_http_response(conn, request.method, request.url, status_code=400, message_body="")

def parseRequest(request):
    splits = request.split()
    method = splits[0]
    url = splits[1]
    version = splits[2]

    return Request(method, url, version)

def handle_conn(conn, addr):
    print_with_lock(" Established connection with SERVER")

    last_request_timestamp = time.time()

    while time.time() < last_request_timestamp + TIMEOUT:
        request = conn.recv(1024).decode("UTF-8")
        if not request:
            time.sleep(0.1)
            continue
        last_request_timestamp = time.time()

        parsedRequest = parseRequest(request)

        if parsedRequest.method == "ping":
            handle_ping(conn)
            return

        if parsedRequest.version == "HTTP/1.1":
            handle_http_request(conn, parsedRequest)
        else:
            print_with_lock(" Sent an invalid request. closing socket")
            conn.sendall("Only HTTP/1.1 and 'ping' supported, try again")
            conn.close()
            return

    print_with_lock(" Timeout reached, closing connection")
    conn.close()


def start():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()

    print_with_lock(" Server started!")
    SCHEDULER.add_job(print_num_active_connections, 'interval', seconds=10)
    SCHEDULER.start()

    client_id = 0
    while True:
        print_num_active_connections()
        conn, addr = s.accept()
        client_id += 1
        threading.Thread(target=handle_conn, name=f"CLIENT{client_id}[{addr[0]}:{addr[1]}]",
                         args=(conn, addr)).start()


start()
