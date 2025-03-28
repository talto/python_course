import socket
import threading
def connect_to_server(client_name):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 8080))
    message = f"hi server from {client_name}"
    client_socket.sendall(message.encode('utf-8'))
    data = client_socket.recv(1024)
    print('SERVER SEND DATE', data)
    client_socket.close()
# for i in range(5):
#     client_thread = threading.Thread(target=connect_to_server, args=(i,))
#     client_thread.start()
for i in range(5):
    connect_to_server(i)