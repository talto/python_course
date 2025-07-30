import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

message = "hi server"
client_socket.sendto(message.encode('utf-8'), ('localhost', 8080))
data, addr = client_socket.recvfrom(1024)
print('got', data, 'from server', addr)
client_socket.close()