import requests
import re
import sys

def get_urls_from_file(keyword, filename="urls.txt"):
    with open(filename, 'r') as file:
        for line in file:
            key, urls = line.strip().split(": ")
            if key == keyword:
                return urls.split(", ")
    return None, None, None, None

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

def scrape_capterra_product_names(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve Capterra webpage. Status code: {response.status_code}")
        return []

    content = response.text
    pattern = r'{"campaignID":"[^"]+","id":"[^"]+","rating":\d+\.\d+,"slug":"([^"]+)","totalReviews":\d+}'
    matches = re.findall(pattern, content)
    return matches

def scrape_github_product_names(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve GitHub webpage. Status code: {response.status_code}")
        return []

    content = response.text
    pattern = r'style="max-height:275px" href="(/[^/]+/[^/]+)" data-view-component="true"'
    matches = re.findall(pattern, content)
    # Extracting only the repository name from the matches
    repo_names = [match.split('/')[-1] for match in matches]
    return repo_names

def main(keyword):
    trustradius_url, gartner_url, capterra_url, github_url = get_urls_from_file(keyword)
    
    if not trustradius_url:
        print(f"No TrustRadius URL found for keyword: {keyword}")
    else:
        # Scrape TrustRadius
        trustradius_products = scrape_trustradius_product_names(trustradius_url)
        print(f"TrustRadius Products for {keyword}:")
        for name in trustradius_products:
            print(name)

    if not gartner_url:
        print(f"No Gartner URL found for keyword: {keyword}")
    else:
        print(f"\nGartner Products for {keyword}:")
        # Scrape Gartner
        gartner_products = scrape_gartner_product_names(gartner_url)
        for name in gartner_products:
            print(name)

    if not capterra_url:
        print(f"No Capterra URL found for keyword: {keyword}")
    else:
        print(f"\nCapterra Products for {keyword}:")
        # Scrape Capterra
        capterra_products = scrape_capterra_product_names(capterra_url)
        for name in capterra_products:
            print(name)

    if not github_url:
        print(f"No GitHub URL found for keyword: {keyword}")
    else:
        print(f"\nGitHub Repositories for {keyword}:")
        # Scrape GitHub
        github_repos = scrape_github_product_names(github_url)
        for name in github_repos:
            print(name)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: main_script.py <keyword>")
    else:
        main(sys.argv[1])
