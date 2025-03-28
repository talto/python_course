import socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 8080))
server_socket.listen(5)
while True:
    client_socket, addr = server_socket.accept()
    data = client_socket.recv(1024)
    print('CLIENT SEND', data)
    response = "hi from server"
    client_socket.sendall(response.encode('utf-8'))
    client_socket.close()