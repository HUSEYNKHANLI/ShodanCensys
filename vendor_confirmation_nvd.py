import requests
from urllib.parse import urlparse

def is_vendor_confirmed(cve_id):
    base_url = f"https://services.nvd.nist.gov/rest/json/cve/1.0/{cve_id}"
    response = requests.get(base_url)
    
    if response.status_code != 200:
        print(f"Error fetching data for {cve_id}. Status code: {response.status_code}")
        return False
    
    data = response.json()
    cve_data = data.get("result", {}).get("CVE_Items", [{}])[0]
    references = cve_data.get("cve", {}).get("references", {}).get("reference_data", [])
    vendor_data = cve_data.get("cve", {}).get("affects", {}).get("vendor", {}).get("vendor_data", [{}])
    
    # Extract vendor names from the CVE details
    vendors = [v.get("vendor_name", "").lower() for v in vendor_data]
    
    for ref in references:
        url = ref.get("url", "")
        domain = urlparse(url).netloc
        
        # Check if the domain or URL contains any of the vendor names
        for vendor in vendors:
            if vendor in domain or vendor.replace(" ", "") in domain:
                return True
            
            # Optionally, fetch the content of the reference link and check for vendor's name
            # Note: This can be slow and might be subject to rate limits or access restrictions
            # content = requests.get(url).text.lower()
            # if vendor in content:
            #     return True

    return False

# Example usage
if __name__ == "__main__":
    cve_id = input("Enter the CVE ID: ")  # Get CVE ID from user input
    if is_vendor_confirmed(cve_id):
        print(f"Vendor has confirmed the vulnerability for {cve_id} based on reference links in the NVD database.")
    else:
        print(f"Vendor has not confirmed the vulnerability for {cve_id} based on reference links in the NVD database.")
