# ... [rest of the imports and functions remain unchanged]

def scrape_trustradius_product_names(base_url, keyword):
    all_products = []
    page = 0
    while True:
        if keyword == "firewalls":
            url = f"{base_url}?f={page*25}#products"
        else:
            url = f"{base_url}?f={page*25}"
        
        content = make_request(url)
        if content:
            pattern = r'{"@context":"https://schema.org","@type":"ListItem","@id":"https://www.trustradius.com/products/[^"]+/reviews","name":"([^"]+)"'
            matches = re.findall(pattern, content)
            if not matches:  # If no matches are found, we've reached the last page
                break
            all_products.extend(matches)
            page += 1
    return all_products

# ... [rest of the functions remain unchanged]

def main(keyword):
    # Check if results.csv exists, if not, create it with headers
    if not os.path.exists("results.csv"):
        with open("results.csv", mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Keyword", "Product Name", "CPE"])

    # ... [rest of the main function remains unchanged, except for the following change]

    if trustradius_url:
        trustradius_products = scrape_trustradius_product_names(trustradius_url, keyword)
        all_products.extend(trustradius_products)
        logging.info(f"TrustRadius Products for {keyword}: {', '.join(trustradius_products)}")

    # ... [rest of the main function remains unchanged]

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: main_script.py <keyword>")
    else:
        main(sys.argv[1])
