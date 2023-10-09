import requests
import re
import sys
import logging
import pickle
import os
import csv

# Configuration
FILENAME = "urls.txt"
CACHE_DIR = "cache"
NVD_CPE_API_URL = "https://services.nvd.nist.gov/rest/json/cpes/1.0"

# Set up logging
logging.basicConfig(level=logging.INFO)

def get_cache_filename(keyword):
    return os.path.join(CACHE_DIR, f"{keyword}.pkl")

def load_from_cache(keyword):
    cache_file = get_cache_filename(keyword)
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    return None

def save_to_cache(keyword, data):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    cache_file = get_cache_filename(keyword)
    with open(cache_file, 'wb') as f:
        pickle.dump(data, f)

def make_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve webpage {url}. Error: {e}")
        return None

def get_urls_from_file(keyword, filename=FILENAME):
    with open(filename, 'r') as file:
        for line in file:
            key, urls = line.strip().split(": ")
            if key == keyword:
                return urls.split(", ")
    return None, None, None, None

def scrape_trustradius_product_names(base_url):
    all_products = []
    for i in range(0, 251, 25):
        url = f"{base_url}?f={i}"
        content = make_request(url)
        if content:
            pattern = r'{"@context":"https://schema.org","@type":"ListItem","@id":"https://www.trustradius.com/products/[^"]+/reviews","name":"([^"]+)"'
            matches = re.findall(pattern, content)
            all_products.extend(matches)
    return all_products

def scrape_gartner_product_names(url):
    content = make_request(url)
    if not content:
        return []
    pattern = r'{"id":"[^"]+","seqId":\d+,"name":"([^"]+)","seoName":"[^"]+","vendors":\['
    matches = re.findall(pattern, content)
    return matches

def scrape_capterra_product_names(url):
    content = make_request(url)
    if not content:
        return []
    pattern = r'{"campaignID":"[^"]+","id":"[^"]+","rating":\d+\.\d+,"slug":"([^"]+)","totalReviews":\d+}'
    matches = re.findall(pattern, content)
    return matches

def scrape_github_product_names(url):
    content = make_request(url)
    if not content:
        return []
    pattern = r'style="max-height:275px" href="(/[^/]+/[^/]+)" data-view-component="true"'
    matches = re.findall(pattern, content)
    repo_names = [match.split('/')[-1] for match in matches]
    return repo_names

def generate_cpe(product_name):
    normalized_name = product_name.lower().replace(" ", "_").replace(",", "").replace(".", "")
    return f"cpe:/a:{normalized_name}:{normalized_name}:::::"

def get_cpe_from_nvd(product_name):
    """Query the NVD API for CPEs based on product name."""
    try:
        response = requests.get(NVD_CPE_API_URL, params={"keyword": product_name})
        response.raise_for_status()
        data = response.json()
        if data and "result" in data and "cpes" in data["result"]:
            # Return the first CPE match for simplicity
            return data["result"]["cpes"][0]["cpe23Uri"]
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve CPE from NVD for {product_name}. Error: {e}")
    return None

def main(keyword):
    cached_data = load_from_cache(keyword)
    if cached_data:
        logging.info(f"Loaded data for {keyword} from cache.")
        all_products = cached_data
    else:
        trustradius_url, gartner_url, capterra_url, github_url = get_urls_from_file(keyword)
        all_products = []
        
        if trustradius_url:
            trustradius_products = scrape_trustradius_product_names(trustradius_url)
            all_products.extend(trustradius_products)
            logging.info(f"TrustRadius Products for {keyword}: {', '.join(trustradius_products)}")

        if gartner_url:
            gartner_products = scrape_gartner_product_names(gartner_url)
            all_products.extend(gartner_products)

        if capterra_url:
            capterra_products = scrape_capterra_product_names(capterra_url)
            all_products.extend(capterra_products)

        if github_url:
            github_repos = scrape_github_product_names(github_url)
            all_products.extend(github_repos)

        save_to_cache(keyword, all_products)

    # Fetch CPEs from NVD and save results to CSV
    with open("results.csv", mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write header only if the file is new
        if file.tell() == 0:
            writer.writerow(["Keyword", "Product Name", "CPE"])
        for product in all_products:
            cpe = get_cpe_from_nvd(product) or generate_cpe(product)
            writer.writerow([keyword, product, cpe])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: main_script.py <keyword>")
    else:
        main(sys.argv[1])
