def get_urls_from_file(keyword, filename=FILENAME):
    with open(filename, 'r') as file:
        for line in file:
            key, urls = line.strip().split(": ")
            if key == keyword:
                return urls.split(", ")
    return []

# ... [rest of the code remains unchanged]

def main(keyword):
    # ... [rest of the code remains unchanged]

    try:
        cached_data = load_from_cache(keyword)
        if cached_data:
            logging.info(f"Loaded data for {keyword} from cache.")
            all_products = cached_data
        else:
            urls_list = get_urls_from_file(keyword)
            all_products = []
            
            for url in urls_list:
                if "trustradius" in url:
                    trustradius_products = scrape_trustradius_product_names(url)
                    all_products.extend(trustradius_products)
                    logging.info(f"TrustRadius Products for {keyword}: {', '.join(trustradius_products)}")
                elif "gartner" in url:
                    gartner_products = scrape_gartner_product_names(url)
                    all_products.extend(gartner_products)
                elif "capterra" in url:
                    capterra_products = scrape_capterra_product_names(url)
                    all_products.extend(capterra_products)
                elif "github" in url:
                    github_repos = scrape_github_product_names(url)
                    all_products.extend(github_repos)

            save_to_cache(keyword, all_products)

        # ... [rest of the code remains unchanged]

    except KeyboardInterrupt:
        logging.info("Interrupted by user. Exiting gracefully.")
        sys.exit(0)   

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: main_script.py <keyword>")
    else:
        main(sys.argv[1])
