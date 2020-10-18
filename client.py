import socket
import sys
import threading
import time

PRINT_LOCK = threading.Lock()
HOST = "127.0.0.1"
PORT = 8002
HTTP_requests = ["GET", "TRACE", "OPTIONS", "HEAD", "PUT", "POST", "DELETE"]


def print_with_lock(arg):
    with PRINT_LOCK:
        print(f"[{threading.current_thread().getName()}]" + arg)


def connect_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((HOST, PORT))

    return server


def send_and_receive_data(server, request):
    server.sendall(request.encode("UTF-8"))

    data = server.recv(1024).decode("UTF-8")

    http_meta = data.split("\n")[0]

    response_body = "\n".join(data.split("\n")[1:]).strip()

    return http_meta, response_body


def ping_server(server):
    start_time = time.time()
    send_and_receive_data(server, "ping")
    elapsed_time = time.time() - start_time
    print(f"pinged {server.getpeername()} | ping : {elapsed_time}")


def client(method, url):
    server = connect_server()

    if method in HTTP_requests:
        http_request(server, url, method)
    elif method == "ping":
        ping_server(server)

    server.close()


def http_request(server, url, method):
    request = f"{method} {url} HTTP/1.1\r\n\r\n"

    http_meta, response_body = send_and_receive_data(server, request)

    print_with_lock(f" Attempting '{method}' request to host '{HOST} on url '{url}'")

    send_and_receive_data(server, request)

    print_with_lock(f" Response from '{method}' request to '{HOST}' on '{url}' had metadata: {http_meta}")
    print_with_lock(f" Body received from '{method}' request: \n {response_body} ")


if 1 < sys.argv.__len__():
    method = sys.argv[1]
    url = sys.argv[2]
    number_of_clients = int(sys.argv[3])

    for i in range(number_of_clients):
        threading.Thread(target=client, name=f"Client{i}", args=(method, url)).start()
