import socket
import sys
import threading

PRINT_LOCK = threading.Lock()
HOST = "127.0.0.1"
PORT = 8002
HTTP_requests = ["GET", "TRACE", "OPTIONS", "HEAD", "PUT", "POST", "DELETE"]


def print_with_lock(arg):
    with PRINT_LOCK:
        print(f"[{threading.current_thread().getName()}]" + arg)


def connect_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    return s


def client(method, url):
    server = connect_server()

    if method in HTTP_requests:
        HTTP_request(server, url, method)

    server.close()


def HTTP_request(server, url, method):
    request = f"{method} {url} HTTP/1.1\r\n\r\n"

    print_with_lock(f" Attempting '{method}' request to host '{HOST} on url '{url}'")
    server.sendall(request.encode("UTF-8"))

    data = server.recv(1024).decode("UTF-8")

    http_meta = data.split("\n")[0]

    response_body = "\n".join(data.split("\n")[1:]).strip()

    print_with_lock(f" Response from '{method}' request to '{HOST}' on '{url}' had metadata: {http_meta}")
    print_with_lock(f" Body received from '{method}' request: \n {response_body} ")


if 1 < sys.argv.__len__():
    method = sys.argv[1]
    url = sys.argv[2]
    number_of_clients = int(sys.argv[3])

    for i in range(number_of_clients):
        threading.Thread(target=client, name=f"Client{i}", args=(method, url)).start()
