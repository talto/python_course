import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('localhost', 8080))

while True:
    data, addr = server_socket.recvfrom(1024)
    print('got', data, 'from', addr)
    response = "hi from server"
    server_socket.sendto(response.encode('utf-8'), addr)
