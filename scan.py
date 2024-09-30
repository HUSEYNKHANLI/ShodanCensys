import csv
import subprocess
import requests
from flask import Flask, request
import logging
from geolite2 import geolite2

# Initialize Flask app for callback server
app = Flask(__name__)

# Setup a log to capture exposed servers
logging.basicConfig(filename="exposed_cups_servers.log", level=logging.INFO, format="%(asctime)s %(message)s")
unique_ips = set()

# Setup GeoIP database
reader = geolite2.reader()

# Endpoint to handle CUPS server callback
@app.route('/callback', methods=['GET', 'POST'])
def handle_callback():
    ip_address = request.remote_addr
    if ip_address not in unique_ips:
        unique_ips.add(ip_address)
        location = reader.get(ip_address)
        logging.info(f"Exposed CUPS server from IP: {ip_address}, Location: {location}")
    return "Received", 200

# Function to read IP addresses from a CSV file
def read_ips_from_csv(file_path):
    ips = []
    with open(file_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            ips.append(row['ip'])
    return ips

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
                print(f"Port 631 is open on {ip}. Sending a probe...")
                # Send a probe to see if CUPS server responds
                response = requests.get(f"http://{ip}:631", timeout=5)
                if response.status_code == 200:
                    print(f"Received valid response from {ip}")
        except subprocess.CalledProcessError as e:
            print(f"Error scanning {ip}: {e}")
        except requests.exceptions.RequestException as e:
            print(f"No response from {ip}: {e}")

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