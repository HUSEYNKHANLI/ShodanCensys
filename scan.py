import socket
import struct

def craft_ipp_get_printer_attributes_request():
    # IPP request format:
    # - Version (2 bytes)
    # - Operation ID (2 bytes)
    # - Request ID (4 bytes)
    # - Operation attributes (varies)
    
    # IPP Version 1.1 (0x0101)
    version = b'\x01\x01'
    
    # Operation ID for Get-Printer-Attributes (0x000B)
    operation_id = b'\x00\x0B'
    
    # Request ID (arbitrary, using 0x00000001)
    request_id = b'\x00\x00\x00\x01'
    
    # Operation attributes
    # - Begin attribute group (0x01 indicates Operation attributes)
    attribute_group_tag = b'\x01'
    
    # - charset (0x47), length (0x0008), value ('utf-8')
    charset_tag = b'\x47' + struct.pack('>H', len('attributes-charset')) + b'attributes-charset' + struct.pack('>H', len('utf-8')) + b'utf-8'
    
    # - natural language (0x48), length (0x000B), value ('en-us')
    language_tag = b'\x48' + struct.pack('>H', len('attributes-natural-language')) + b'attributes-natural-language' + struct.pack('>H', len('en-us')) + b'en-us'
    
    # - printer-uri (0x45), length (0x000B), value ('ipp://printer')
    printer_uri_tag = b'\x45' + struct.pack('>H', len('printer-uri')) + b'printer-uri' + struct.pack('>H', len('ipp://printer')) + b'ipp://printer'
    
    # End of attributes (0x03)
    end_of_attributes = b'\x03'
    
    # Combine everything into a full IPP request
    ipp_request = version + operation_id + request_id + attribute_group_tag + charset_tag + language_tag + printer_uri_tag + end_of_attributes
    
    return ipp_request

def send_ipp_udp_probe(ip):
    try:
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)  # Set a timeout for the socket (5 seconds)
        
        # Get the IPP request packet
        ipp_request = craft_ipp_get_printer_attributes_request()
        server_address = (ip, 631)  # Send to UDP port 631
        
        # Send the UDP packet
        print(f"Sending IPP Get-Printer-Attributes UDP probe to {ip} on port 631...")
        sock.sendto(ipp_request, server_address)
        
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

# Example usage
ip = "192.168.1.10"  # Replace with target IP
send_ipp_udp_probe(ip)