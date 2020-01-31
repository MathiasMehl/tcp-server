import socket
import threading
import http
import time
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
HOST = '127.0.0.1'
PORT = 8002
TIMEOUT = 30
PRINT_LOCK = threading.Lock()
CLIENTS_LOCK = threading.Lock()


def print_with_lock(arg: str):
    with PRINT_LOCK:
        print(f"[{threading.current_thread().getName()}]" + arg)


def print_num_active_connections():
    active_threads = 0
    for thread in threading.enumerate():
        if thread.getName().startswith("CLIENT"):
            active_threads += 1
    with PRINT_LOCK:
        print(f"[SERVER] Active connections: {active_threads}")


def print_response_status(method, url, status_code):
    print_with_lock(f" issued a '{method}' request to URL '{url}' "
                    f"request handled with status code: '{status_code} {http.HTTPStatus(status_code).phrase}'")


def http_response(status_code, body):
    reason_phrase = http.HTTPStatus(status_code).phrase
    return f"HTTP/1.1 {status_code} {reason_phrase}\r\n\r\n{body}".encode("UTF-8")


def handle_conn(conn, addr):
    print_with_lock(f" Established connection with SERVER\n")

    last_request = time.time()

    while time.time() < last_request + TIMEOUT:
        request = conn.recv(1024).decode("UTF-8")
        if not request:
            time.sleep(0.1)
            continue
        last_request = time.time()

        method = request.split()[0]
        url = request.split()[1]
        if not request.split()[2] == "HTTP/1.1":
            print_with_lock(f" Sent a non HTTP/1.1 request. closing socket")
            conn.sendall("Only HTTP/1.1 supported, try again")
            conn.close()
            return

        # HTTP-Version Status-Code Reason-Phrase CRLF
        # headers CRLF
        # message-body

        print_with_lock(f" Issued a '{method}' request to URL '{url}'")
        if method == "GET":
            if url == "/":
                # Garbage collector will handle this
                static_web_page = open('hello.html', 'r').read()

                conn.sendall(http_response(200, static_web_page))
                print_response_status(method, url, 200)
            else:
                conn.sendall(http_response(404, ""))
                print_response_status(method, url, 404)
        elif method == "TRACE":
            conn.sendall(http_response(200, request))
            print_response_status(method, url, 200)
        elif method == "OPTIONS":
            conn.sendall(http_response(200, "(GET (only at '/'), TRACE, HEAD (only at '/')"))
            print_response_status(method, url, 200)
        elif method == "HEAD":
            if url == "/":
                # Garbage collector will handle this
                static_web_page = open('hello.html', 'r').read()

                conn.sendall(http_response(200,
                                           f"HTML document with size: {len(static_web_page)}, "
                                           f"last modified: Some time ago"))
                print_response_status(method, url, 200)
            else:
                conn.sendall(http_response(404, ""))
                print_response_status(method, url, 404)
        elif method == "PUT":
            conn.sendall(http_response(501, ""))
            print_response_status(method, url, 501)
        elif method == "POST":
            conn.sendall(http_response(501, ""))
            print_response_status(method, url, 501)
        elif method == "DELETE":
            conn.sendall(http_response(501, ""))
            print_response_status(method, url, 501)
        else:
            conn.sendall(http_response(400, ""))
            print_response_status(method, url, 400)

    print_with_lock(f" Timeout reached, closing connection")
    conn.close()


def start():
    threading.current_thread().name = 'SERVER'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()

    print_with_lock(" Server started!")
    scheduler.add_job(print_num_active_connections, 'interval', seconds=15)
    scheduler.start()

    clients = 0
    while True:
        print_num_active_connections()
        conn, addr = s.accept()
        with CLIENTS_LOCK:
            clients += 1
            threading.Thread(target=handle_conn, name=f"CLIENT{clients}[{addr[0]}:{addr[1]}]",
                             args=(conn, addr)).start()


start()
