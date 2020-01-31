import socket
import sys
import threading

PRINT_LOCK = threading.Lock()

PORT = 8002


def print_with_lock(arg: str):
    with PRINT_LOCK:
        print(f"[{threading.current_thread().getName()}]" + arg)


def send_basic_get_request(host, url):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, PORT))

    # Method Request-URI HTTP-Version CRLF
    # headers CRLF
    # message-body
    request = f"GET {url} HTTP/1.1\r\n\r\n"

    print_with_lock(f" Attempting GET request to host '{host} on url '{url}'")
    s.sendall(request.encode("UTF-8"))

    data = s.recv(1024).decode("UTF-8")

    http_code = data.split("\n")[0]

    response_body = "\n".join(data.split("\n")[1:]).strip()

    print_with_lock(f" Response from GET request to '{host}' on '{url}' had status code: {http_code}")
    print_with_lock(f" Body received from GET request: \n {response_body} ")

    s.close()


if 1 < sys.argv.__len__():
    request = sys.argv[1]
    host = sys.argv[2]
    url = sys.argv[3]
    number_of_clients = sys.argv[4]

    if request == "GET":
        for i in range(int(number_of_clients)):
            threading.Thread(target=send_basic_get_request, name=f"Client{i}", args=(host, url)).start()
        # send_basic_get_request(host, url)
    else:
        print("Either first argument was not a HTTP request, or it was not implemented yet")
