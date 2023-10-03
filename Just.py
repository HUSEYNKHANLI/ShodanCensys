import requests
import re
import sys

def get_urls_from_file(keyword, filename="urls.txt"):
    with open(filename, 'r') as file:
        for line in file:
            key, urls = line.strip().split(": ")
            if key == keyword:
                return urls.split(", ")
    return None, None

def scrape_trustradius_product_names(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve TrustRadius webpage. Status code: {response.status_code}")
        return []

    content = response.text
    pattern = r'{"@context":"https://schema.org","@type":"ListItem","@id":"https://www.trustradius.com/products/[^"]+/reviews","name":"([^"]+)"'
    matches = re.findall(pattern, content)
    return matches

def scrape_gartner_product_names(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve Gartner webpage. Status code: {response.status_code}")
        return []

    content = response.text
    pattern = r'{"id":"[^"]+","seqId":\d+,"name":"([^"]+)","seoName":"[^"]+","vendors":\['
    matches = re.findall(pattern, content)
    return matches

def main(keyword):
    trustradius_url, gartner_url = get_urls_from_file(keyword)
    
    if not trustradius_url or not gartner_url:
        print(f"No URLs found for keyword: {keyword}")
        return

    # Scrape TrustRadius
    trustradius_products = scrape_trustradius_product_names(trustradius_url)
    print(f"TrustRadius Products for {keyword}:")
    for name in trustradius_products:
        print(name)

    print(f"\nGartner Products for {keyword}:")
    # Scrape Gartner
    gartner_products = scrape_gartner_product_names(gartner_url)
    for name in gartner_products:
        print(name)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: main_script.py <keyword>")
    else:
        main(sys.argv[1])
