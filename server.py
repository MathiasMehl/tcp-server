import socket
import threading
import http
import time

HOST = '127.0.0.1'
PORT = 8002
PRINT_LOCK = threading.Lock()


def print_with_lock(arg):
    with PRINT_LOCK:
        print(arg)


def print_response_status(addr, method, url, status_code):
    print_with_lock(f"{addr} issued a '{method}' request to URL '{url}' "
                    f"response was: '{status_code} {http.HTTPStatus(status_code).phrase}'")


def http_response(status_code, body):
    reason_phrase = http.HTTPStatus(status_code).phrase
    return f"HTTP/1.1 {status_code} {reason_phrase}\r\n\r\n{body}".encode("UTF-8")


def handle_conn(conn, addr):
    print(f"Connection with {addr}\n")

    timeout = 30
    conn_time = time.time()

    while time.time() < conn_time + timeout:
        request = conn.recv(1024).decode("UTF-8")
        if not request:
            time.sleep(0.1)
            continue

        method = request.split()[0]
        url = request.split()[1]
        if not request.split()[2] == "HTTP/1.1":
            print_with_lock(f"[SERVER] Got a non HTTP/1.1 request from {addr}. closing socket")
            conn.sendall("Only HTTP/1.1 supported, try again")
            conn.close()
            return

        # HTTP-Version Status-Code Reason-Phrase CRLF
        # headers CRLF
        # message-body

        print(f"{addr} issued a '{method}' request to URL '{url}'")
        if method == "GET":
            if url == "/":
                # Garbage collector will handle this
                static_web_page = open('hello.html', 'r').read()

                response = http_response(200, static_web_page)
                conn.sendall(response)
                print_response_status(addr, method, url, 200)
            else:
                conn.sendall(http_response(404, ""))
                print_response_status(addr, method, url, 404)
        elif method == "PUT":
            conn.sendall(http_response(501, ""))
            print_response_status(addr, method, url, 501)
        elif method == "POST":
            conn.sendall(http_response(501, ""))
            print_response_status(addr, method, url, 501)
        elif method == "DELETE":
            conn.sendall(http_response(501, ""))
            print_response_status(addr, method, url, 501)

    print(f"Timeout reached for {addr}, closing connection")
    conn.close()


def start():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()

    print("Server started!")
    while True:

        active_connections = 0
        for th in threading.enumerate():
            if th.name == "active_conn":
                active_connections += 1

        print_with_lock(f"Active connections: {active_connections}")

        conn, addr = s.accept()
        threading.Thread(target=handle_conn, name="active_conn", args=(conn, addr)).start()


start()
