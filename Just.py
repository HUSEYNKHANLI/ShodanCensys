import requests
import re

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

def main():
    trustradius_url = "https://www.trustradius.com/cms"
    gartner_url = "https://www.gartner.com/reviews/market/web-content-management"

    # Scrape TrustRadius
    trustradius_products = scrape_trustradius_product_names(trustradius_url)
    print("TrustRadius Products:")
    for name in trustradius_products:
        print(name)

    print("\nGartner Products:")
    # Scrape Gartner
    gartner_products = scrape_gartner_product_names(gartner_url)
    for name in gartner_products:
        print(name)

if __name__ == "__main__":
    main()
