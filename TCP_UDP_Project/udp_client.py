
import socket

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ("127.0.0.1", 6000)

print("Connected to UDP Server!")

while True:
    message = input("Client: ")

    client.sendto(message.encode(), server_address)

    data, address = client.recvfrom(1024)

    print("Server:", data.decode())

    if message.lower() == "exit":
        break

client.close()
