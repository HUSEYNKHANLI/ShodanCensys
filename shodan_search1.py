import shodan
import time
import logging
import sys
import json
import csv
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

def search_shodan(query):
    logging.info(f"Searching Shodan for: {query}")
    try:
        results = shodan_api.search(query)
        return results['matches']
    except shodan.APIError as e:
        logging.error(f"Error: {e}")
        return []

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
        writer = csv.DictWriter(f, fieldnames=["ip_str", "org", "location", "data", "detection_method"])
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
    time.sleep(1)  # Rate limiting

    is_cpe_search = target.startswith("cpe:")
    shodan_results = search_shodan(target)
    processed_shodan = process_shodan_results(shodan_results, cpe_search=is_cpe_search, cpe=target)

    for entry in processed_shodan:
        print(entry)

    save_to_json(processed_shodan, "shodan_results.json")
    save_to_csv(processed_shodan, "shodan_results.csv")
