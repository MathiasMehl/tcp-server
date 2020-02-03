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


def send_and_print_response(conn, method, url, status_code, body):
    conn.sendall(create_http_response(status_code, body))
    print_response_status(method, url, status_code)


def create_http_response(status_code, body):
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

        # HTTP-Version Status-Code Reason-Phrase CRLF
        # headers CRLF
        # message-body

        method = request.split()[0]
        url = request.split()[1]
        if not request.split()[2] == "HTTP/1.1":
            print_with_lock(f" Sent a non HTTP/1.1 request. closing socket")
            conn.sendall("Only HTTP/1.1 supported, try again")
            conn.close()
            return

        print_with_lock(f" Issued a '{method}' request to URL '{url}'")
        if method == "GET":
            if url == "/":
                static_web_page = open('hello.html', 'r').read()

                send_and_print_response(conn, method, url, 200, static_web_page)
            else:
                send_and_print_response(conn, method, url, 404, "")
        elif method == "TRACE":
            send_and_print_response(conn, method, url, 200, request)
        elif method == "OPTIONS":
            send_and_print_response(conn, method, url, 200,
                                    "(GET (only at '/'), TRACE, HEAD (only at '/')")
        elif method == "HEAD":
            if url == "/":
                static_web_page = open('hello.html', 'r').read()

                send_and_print_response(conn, method, url, 200,
                                        f"'HTML document' with size: {len(static_web_page)} \n last modified: Some time ago")
            else:
                send_and_print_response(conn, method, url, 404, "")
        elif method == "PUT":
            send_and_print_response(conn, method, url, 501, "")
        elif method == "POST":
            send_and_print_response(conn, method, url, 501, "")
        elif method == "DELETE":
            send_and_print_response(conn, method, url, 501, "")
        else:
            send_and_print_response(conn, method, url, 400, "")

    print_with_lock(f" Timeout reached, closing connection")
    conn.close()


def start():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()

    print_with_lock(" Server started!")
    scheduler.add_job(print_num_active_connections, 'interval', seconds=10)
    scheduler.start()

    client_ID = 0
    while True:
        print_num_active_connections()
        conn, addr = s.accept()
        client_ID += 1
        threading.Thread(target=handle_conn, name=f"CLIENT{client_ID}[{addr[0]}:{addr[1]}]",
                         args=(conn, addr)).start()


start()
