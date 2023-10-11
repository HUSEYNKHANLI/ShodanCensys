def scrape_trustradius_product_names(base_url):
    all_products = []
    i = 0
    while True:
        if i == 0:
            url = f"{base_url}"
        else:
            url = f"{base_url}?f={i}"
        content = make_request(url)
        if content:
            pattern = r'{"@context":"https://schema.org","@type":"ListItem","@id":"https://www.trustradius.com/products/[^"]+/reviews","name":"([^"]+)"'
            matches = re.findall(pattern, content)
            if not matches:  # No product names found, indicating it's the last page
                break
            all_products.extend(matches)
            i += 25
        else:
            break
    return all_products
