import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect(('localhost', 8080))
message = "hi server"
client_socket.sendall(message.encode('utf-8'))
data = client_socket.recv(1024)
print('SERVER SEND DATE', data)
client_socket.close()