print("Performance Analyzer Started!")
import socket
import threading
import time
import statistics
import matplotlib.pyplot as plt

HOST = "127.0.0.1"
TCP_PORT = 5001
UDP_PORT = 6001

TEST_MESSAGES = 100
WARMUP_MESSAGES = 5
PACKET_SIZE = 64

tcp_ready = threading.Event()
udp_ready = threading.Event()


# Receive an exact number of bytes over TCP
def receive_exact(conn, size):
    data = b""

    while len(data) < size:
        chunk = conn.recv(size - len(data))

        if not chunk:
            return None

        data += chunk

    return data


# TCP echo server
def tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, TCP_PORT))
    server.listen(1)
    tcp_ready.set()

    conn, address = server.accept()

    with conn:
        while True:
            data = receive_exact(conn, PACKET_SIZE)

            if data is None:
                break

            conn.sendall(data)

    server.close()


# UDP echo server
def udp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, UDP_PORT))
    udp_ready.set()

    while True:
        data, address = server.recvfrom(1024)

        if data == b"STOP":
            break

        server.sendto(data, address)

    server.close()


# Measure TCP round-trip time
def test_tcp():
    results = []

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, TCP_PORT))

    for i in range(WARMUP_MESSAGES + TEST_MESSAGES):
        message = f"TCP-{i}".encode().ljust(PACKET_SIZE, b" ")

        start = time.perf_counter_ns()

        client.sendall(message)
        reply = receive_exact(client, PACKET_SIZE)

        end = time.perf_counter_ns()

        if reply != message:
            raise RuntimeError("TCP response mismatch")

        if i >= WARMUP_MESSAGES:
            results.append((end - start) / 1_000_000)

    client.close()
    return results


# Measure UDP round-trip time
def test_udp():
    results = []

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(2)

    address = (HOST, UDP_PORT)

    for i in range(WARMUP_MESSAGES + TEST_MESSAGES):
        message = f"UDP-{i}".encode().ljust(PACKET_SIZE, b" ")

        start = time.perf_counter_ns()

        client.sendto(message, address)
        reply, server_address = client.recvfrom(1024)

        end = time.perf_counter_ns()

        if reply != message:
            raise RuntimeError("UDP response mismatch")

        if i >= WARMUP_MESSAGES:
            results.append((end - start) / 1_000_000)

    client.sendto(b"STOP", address)
    client.close()

    return results


# Start temporary servers
print("\nStarting TCP and UDP test servers...")

threading.Thread(target=tcp_server, daemon=True).start()
threading.Thread(target=udp_server, daemon=True).start()

if not tcp_ready.wait(5) or not udp_ready.wait(5):
    raise RuntimeError("Could not start test servers")

print("Both test servers are ready!")

# Run performance tests
tcp_times = test_tcp()
udp_times = test_udp()


# Calculate statistics
tcp_avg = statistics.mean(tcp_times)
udp_avg = statistics.mean(udp_times)

print("\n========== PERFORMANCE RESULTS ==========")

print("\nTCP RESULTS")
print("Average RTT:", round(tcp_avg, 4), "ms")
print("Minimum RTT:", round(min(tcp_times), 4), "ms")
print("Maximum RTT:", round(max(tcp_times), 4), "ms")

print("\nUDP RESULTS")
print("Average RTT:", round(udp_avg, 4), "ms")
print("Minimum RTT:", round(min(udp_times), 4), "ms")
print("Maximum RTT:", round(max(udp_times), 4), "ms")

if tcp_avg < udp_avg:
    print("\nTCP had lower average RTT in this test.")
elif udp_avg < tcp_avg:
    print("\nUDP had lower average RTT in this test.")
else:
    print("\nBoth protocols had equal average RTT.")


# Create performance graphs
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Average RTT comparison
axes[0].bar(
    ["TCP", "UDP"],
    [tcp_avg, udp_avg]
)

axes[0].set_title("Average Round-Trip Time")
axes[0].set_ylabel("Time (milliseconds)")
axes[0].grid(axis="y", alpha=0.3)

# Individual message RTT comparison
axes[1].plot(
    range(1, TEST_MESSAGES + 1),
    tcp_times,
    label="TCP"
)

axes[1].plot(
    range(1, TEST_MESSAGES + 1),
    udp_times,
    label="UDP"
)

axes[1].set_title("Message Response Time")
axes[1].set_xlabel("Message Number")
axes[1].set_ylabel("Time (milliseconds)")
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.suptitle("TCP vs UDP Performance Analysis")
plt.tight_layout()

plt.savefig("tcp_udp_comparison.png", dpi=300)

print("\nGraph saved as tcp_udp_comparison.png")

plt.show()
