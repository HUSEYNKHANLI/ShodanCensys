import requests

def is_vendor_confirmed(cve_id):
    base_url = f"https://services.nvd.nist.gov/rest/json/cve/1.0/{cve_id}"
    response = requests.get(base_url)
    
    if response.status_code != 200:
        print(f"Error fetching data for {cve_id}. Status code: {response.status_code}")
        return False
    
    data = response.json()
    cve_data = data.get("result", {}).get("CVE_Items", [{}])[0]
    references = cve_data.get("cve", {}).get("references", {}).get("reference_data", [])
    
    # List of domains or keywords to consider as vendor or legitimate sources
    legit_sources = ["vendor_domain.com", "legit_source.com"]  # Replace with actual domains or keywords
    
    for ref in references:
        url = ref.get("url", "")
        for source in legit_sources:
            if source in url:
                return True

    return False

# Example usage
if __name__ == "__main__":
    cve_id = input("Enter the CVE ID: ")  # Get CVE ID from user input
    if is_vendor_confirmed(cve_id):
        print(f"Vendor has confirmed the vulnerability for {cve_id} based on reference links in the NVD database.")
    else:
        print(f"Vendor has not confirmed the vulnerability for {cve_id} based on reference links in the NVD database.")
