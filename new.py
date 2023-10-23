import requests
import re
import csv
from bs4 import BeautifulSoup

# URL for Synology DSM release notes
URL = "https://www.synology.com/en-global/releaseNote/DSM"

# Fetch the webpage content
response = requests.get(URL)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract version and date details
versions = []
for header in soup.find_all('h3'):
    version_text = header.get_text(strip=True)
    version_match = re.search(r'Version: ([\d\.]+-\d+)', version_text)
    if version_match:
        version = version_match.group(1)
        date_element = header.find_next('div')
        date_text = date_element.get_text(strip=True) if date_element else None
        versions.append((version, date_text))

# Save to CSV
with open('versions.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Version", "Date"])
    for item in versions:
        writer.writerow(item)

print(f"Saved {len(versions)} entries to versions.csv.")