import aiohttp
import asyncio
import csv
import re
import sys
import logging
import pickle
import os

# Configuration
FILENAME = "urls.txt"
CACHE_DIR = "cache"

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

async def make_request_async(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            logging.error(f"Failed to retrieve webpage {url}. Error: {e}")
            return None

def get_urls_from_file(keyword, filename=FILENAME):
    with open(filename, 'r') as file:
        for line in file:
            key, urls = line.strip().split(": ")
            if key == keyword:
                return urls.split(", ")
    return None, None, None, None

async def scrape_trustradius_product_names_async(base_url):
    all_products = []
    tasks = [scrape_trustradius_page(base_url, i) for i in range(0, 251, 25)]
    results = await asyncio.gather(*tasks)
    for products in results:
        all_products.extend(products)
    return all_products

async def scrape_trustradius_page(base_url, i):
    url = f"{base_url}?f={i}"
    content = await make_request_async(url)
    if content:
        pattern = r'{"@context":"https://schema.org","@type":"ListItem","@id":"https://www.trustradius.com/products/[^"]+/reviews","name":"([^"]+)"'
        matches = re.findall(pattern, content)
        return matches
    return []

async def scrape_gartner_product_names_async(url):
    content = await make_request_async(url)
    if content:
        pattern = r'{"id":"[^"]+","seqId":\d+,"name":"([^"]+)","seoName":"[^"]+","vendors":\['
        matches = re.findall(pattern, content)
        return matches
    return []

async def scrape_capterra_product_names_async(url):
    content = await make_request_async(url)
    if content:
        pattern = r'{"campaignID":"[^"]+","id":"[^"]+","rating":\d+\.\d+,"slug":"([^"]+)","totalReviews":\d+}'
        matches = re.findall(pattern, content)
        return matches
    return []

async def scrape_github_product_names_async(url):
    content = await make_request_async(url)
    if content:
        pattern = r'style="max-height:275px" href="(/[^/]+/[^/]+)" data-view-component="true"'
        matches = re.findall(pattern, content)
        repo_names = [match.split('/')[-1] for match in matches]
        return repo_names
    return []

def generate_cpe(product_name):
    normalized_name = product_name.lower().replace(" ", "_").replace(",", "").replace(".", "")
    return f"cpe:/a:{normalized_name}:{normalized_name}:::::"

def save_to_csv(keyword, data, filename="results.csv"):
    """Save the scraped results to a CSV file."""
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write header only if the file is new
        if file.tell() == 0:
            writer.writerow(["Keyword", "Product Name", "CPE"])
        for product in data:
            cpe = generate_cpe(product)
            writer.writerow([keyword, product, cpe])

async def main(keyword):
    # Try loading from cache first
    cached_data = load_from_cache(keyword)
    if cached_data:
        logging.info(f"Loaded data for {keyword} from cache.")
        all_products = cached_data
    else:
        trustradius_url, gartner_url, capterra_url, github_url = get_urls_from_file(keyword)
        all_products = []
        
        if trustradius_url:
            trustradius_products = await scrape_trustradius_product_names_async(trustradius_url)
            all_products.extend(trustradius_products)
            logging.info(f"TrustRadius Products for {keyword}: {', '.join(trustradius_products)}")

        if gartner_url:
            gartner_products = await scrape_gartner_product_names_async(gartner_url)
            all_products.extend(gartner_products)
            logging.info(f"Gartner Products for {keyword}: {', '.join(gartner_products)}")

        if capterra_url:
            capterra_products = await scrape_capterra_product_names_async(capterra_url)
            all_products.extend(capterra_products)
            logging.info(f"Capterra Products for {keyword}: {', '.join(capterra_products)}")

        if github_url:
            github_repos = await scrape_github_product_names_async(github_url)
            all_products.extend(github_repos)
            logging.info(f"GitHub Repositories for {keyword}: {', '.join(github_repos)}")

        save_to_cache(keyword, all_products)

    save_to_csv(keyword, all_products)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: main_script.py <keyword>")
    else:
        asyncio.run(main(sys.argv[1]))
