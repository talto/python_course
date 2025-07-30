import socket
import multiprocessing


def connect_to_server(client_name):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = f"hi server from {client_name}"
    client_socket.sendto(message.encode('utf-8'), ('localhost', 8080))
    data, addr = client_socket.recvfrom(1024)
    print('got', data, 'from server', addr)
    client_socket.close()


for i in range(5):
    client_proces = multiprocessing.Process(target=connect_to_server, args=(i,))
    client_proces.start()