
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server.bind(("127.0.0.1", 6000))

print("UDP Server Started...")
print("Waiting for messages...")

while True:
    data, address = server.recvfrom(1024)

    message = data.decode()

    print("Client:", message)

    if message.lower() == "exit":
        server.sendto("Goodbye!".encode(), address)
        break

    reply = input("Server: ")

    server.sendto(reply.encode(), address)

server.close()
