import shodan
import time
import logging
import sys
import json
import csv
import os
from decouple import config
import re

# For data preprocessing
from sklearn.feature_extraction.text import CountVectorizer

# Set up logging
logging.basicConfig(level=logging.INFO)

# API Key (use environment variable or a .env file for security)
SHODAN_API_KEY = config('SHODAN_API_KEY')

# Initialize the Shodan client
shodan_api = shodan.Shodan(SHODAN_API_KEY)

CACHE_FILE = "cve_cache.json"

# Load cache if exists
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)
else:
    cache = {}

def search_shodan(query, batch_size=50, batch_number=0):
    logging.info(f"Searching Shodan for: {query}, Batch: {batch_number}")
    try:
        results = shodan_api.search(query, page=batch_number+1)
        return results['matches'][:batch_size]
    except shodan.APIError as e:
        logging.error(f"Error: {e}")
        return []

def process_shodan_results(results, cpe_search=False, cpe=None):
    processed_data = []
    for result in results:
        data = {
            "ip_str": result["ip_str"],
            "org": result.get("org", "N/A"),
            "location": f'{result["location"]["city"]}, {result["location"]["country_code"]}',
            "data": result["data"].strip(),
            "vulnerabilities": []
        }

        # Fetch and process CVE details, if present
        if "vulns" in result:
            for cve_id in result["vulns"]:
                if cve_id not in cache:
                    try:
                        cve_details = shodan_api.exploit.get(cve_id)
                        cache[cve_id] = cve_details
                        time.sleep(1)
                    except shodan.APIError as e:
                        if 'Rate limit' in str(e):
                            logging.warning("Rate limit reached, sleeping for 60 seconds...")
                            time.sleep(60)
                            break
                        else:
                            logging.error(f"Error fetching CVE {cve_id}: {e}")
                data["vulnerabilities"].append(cache[cve_id])

        if cpe_search and cpe:
            data["detection_method"] = detect_method_from_data(data["data"], cpe)
        else:
            data["detection_method"] = "N/A"

        processed_data.append(data)
    return processed_data

def detect_method_from_data(data, cpe):
    parts = cpe.split(":")
    if len(parts) < 5:
        return "Detection method unknown."

    vendor, product = parts[3], parts[4]
    if re.search(f"{vendor}|{product}", data, re.IGNORECASE):
        return f"Detected via mentions of {vendor} or {product} in data."

    cookie_indicator = re.search(r"SET-COOKIE: ([^=]+)=", data, re.IGNORECASE)
    if cookie_indicator:
        return f"Detected via Set-Cookie header: {cookie_indicator.group(1)}."

    generator_indicator = re.search(r"Generator: ([^\r\n]+)", data, re.IGNORECASE)
    if generator_indicator:
        return f"Detected via Generator header: {generator_indicator.group(1)}."

    server_indicator = re.search(r"Server: ([^\r\n]+)", data, re.IGNORECASE)
    if server_indicator:
        return f"Detected via Server header: {server_indicator.group(1)}."

    return "Detection method unknown."

def process_shodan_results(results, cpe_search=False, cpe=None):
    processed_data = []
    for result in results:
        data = {
            "ip_str": result["ip_str"],
            "org": result.get("org", "N/A"),
            "location": f'{result["location"]["city"]}, {result["location"]["country_code"]}',
            "data": result["data"].strip()
        }

        if cpe_search and cpe:
            data["detection_method"] = detect_method_from_data(data["data"], cpe)
        else:
            data["detection_method"] = "N/A"

        processed_data.append(data)
    return processed_data

def save_to_json(data, filename="results.json"):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def save_to_csv(data, filename="results.csv"):
    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=["ip_str", "org", "location", "data", "detection_method", "vulnerabilities"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def gather_data_for_training(results):
    # This function will extract data and labels (CPEs) from the Shodan results
    data = []
    labels = []

    for result in results:
        banner_data = result["data"].strip()
        cpe = result.get("os", {}).get("cpe", None)  # Assuming 'os' has the CPE data. Adjust as needed.
        
        if cpe:
            data.append(banner_data)
            labels.append(cpe)

    return data, labels

def preprocess_data(data):
    # Convert the banners into numerical vectors
    vectorizer = CountVectorizer()
    vectorized_data = vectorizer.fit_transform(data)
    return vectorized_data, vectorizer

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(f"Usage: {sys.argv[0]} <search query> or {sys.argv[0]} cpe:<cpe_string>")
        sys.exit(1)

    target = sys.argv[1]
    
    batch_number = 0
    while True:
        # Handle Batching
        shodan_results = search_shodan(target, batch_size=50, batch_number=batch_number)
        if not shodan_results:
            break
        
        processed_shodan = process_shodan_results(shodan_results, cpe_search=target.startswith("cpe:"), cpe=target)
        
        # Handle Caching and Error Handling
        for entry in processed_shodan:
            cves = entry.get("cves", [])
            for cve in cves:
                if cve not in cache:
                    try:
                        cve_details = shodan_api.exploit.get(cve)
                        cache[cve] = cve_details
                        time.sleep(1)  # Respect the rate limit
                    except shodan.APIError as e:
                        if 'Rate limit' in str(e):
                            logging.warning("Rate limit reached, sleeping for 60 seconds...")
                            time.sleep(60)
                        else:
                            logging.error(f"Error fetching CVE {cve}: {e}")
        
        # Save results and cache
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
        
        save_to_json(processed_shodan, f"shodan_results_batch_{batch_number}.json")
        save_to_csv(processed_shodan, f"shodan_results_batch_{batch_number}.csv")
        
        batch_number += 1
        time.sleep(2)  # Pause between batches
