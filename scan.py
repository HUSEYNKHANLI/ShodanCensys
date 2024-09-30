import csv
import subprocess
import socket
from flask import Flask, request
import logging

# Initialize Flask app for callback server
app = Flask(__name__)

# Setup a log to capture exposed servers
logging.basicConfig(filename="exposed_cups_servers.log", level=logging.INFO, format="%(asctime)s %(message)s")
unique_ips = set()

# Endpoint to handle CUPS server callback
@app.route('/callback', methods=['GET', 'POST'])
def handle_callback():
    ip_address = request.remote_addr
    if ip_address not in unique_ips:
        unique_ips.add(ip_address)
        logging.info(f"Exposed CUPS server from IP: {ip_address}")
    return "Received", 200

# Function to read IP addresses from a CSV file
def read_ips_from_csv(file_path):
    ips = []
    with open(file_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            ips.append(row['ip'])
    return ips

# Function to send a UDP probe to port 631
def send_udp_probe(ip):
    try:
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)  # Set a timeout for the socket (5 seconds)

        # Construct a simple UDP packet (could be empty or have basic content)
        udp_probe_message = b'\x01'  # Simple byte message
        server_address = (ip, 631)  # Send to UDP port 631

        # Send the UDP packet
        print(f"Sending UDP probe to {ip} on port 631...")
        sock.sendto(udp_probe_message, server_address)

        # Try to receive a response (if any)
        try:
            data, _ = sock.recvfrom(4096)  # Buffer size is 4096 bytes
            print(f"Received response from {ip}: {data}")
        except socket.timeout:
            print(f"No response from {ip} on UDP port 631.")
        finally:
            sock.close()
    except Exception as e:
        print(f"Error while probing {ip} on UDP: {e}")

# Function to scan IPs using Nmap (as Zmap is for large-scale scans)
def scan_ips(ips):
    for ip in ips:
        try:
            print(f"Scanning {ip} for UDP port 631...")
            # Nmap command to scan UDP port 631 on a specific IP
            nmap_command = ["sudo", "nmap", "-sU", "-p", "631", ip]
            scan_output = subprocess.check_output(nmap_command).decode('utf-8')

            # Check if port 631 is open
            if "631/udp open" in scan_output:
                print(f"Port 631 is open on {ip}. Sending a UDP probe...")
                # Send a UDP probe to the open port
                send_udp_probe(ip)
        except subprocess.CalledProcessError as e:
            print(f"Error scanning {ip}: {e}")

# Main function
if __name__ == "__main__":
    # Start Flask server in background for handling callbacks
    from multiprocessing import Process
    p = Process(target=app.run, kwargs={"host": "0.0.0.0", "port": 80})
    p.start()

    # Read IPs from CSV file
    ips_to_scan = read_ips_from_csv("ips.csv")

    # Scan each IP from the CSV
    scan_ips(ips_to_scan)

    # Close the callback server after scanning
    p.join()