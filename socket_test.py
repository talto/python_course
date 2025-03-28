import socket
# 94.158.219.154
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('94.158.219.154', 8080))
message = "hi server, that is me, Peter!"
client_socket.sendall(message.encode('utf-8'))
data = client_socket.recv(1024)
print('Peter SERVER SEND DATE', data )
client_socket.close()