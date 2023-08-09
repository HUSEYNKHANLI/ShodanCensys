import os
import shodan
import re
import requests
import json
import csv
from bs4 import BeautifulSoup
import argparse
import time
import logging
import censys.search
from concurrent.futures import ThreadPoolExecutor
from decouple import config


# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up argument parser
parser = argparse.ArgumentParser(description="Search for a target using Shodan, Censys, and Google.")
parser.add_argument('target', type=str, help="The target you want to search for.")
args = parser.parse_args()

# Use the target provided by the user
target = args.target

# Censys API credentials
CENSYS_API_ID = config('CENSYS_API_ID')
CENSYS_API_SECRET = config('CENSYS_API_SECRET')



# Initialize Censys API
censys_search = censys.search
censys_api = censys_search.CensysHosts(api_id=CENSYS_API_ID, api_secret=CENSYS_API_SECRET)




# Function to search Censys
def search_censys(target):
    try:
        censys_results = list(censys_api.search(target))
        return censys_results
    except Exception as e:
        logging.error(f"An error occurred while searching Censys: {e}")
        return []

# Function to update the patterns file with a new pattern
def update_patterns(new_pattern):
    patterns.append(new_pattern)
    with open(patterns_file_path, "w") as f:
        json.dump(patterns, f)

# Function to load or generate patterns
def load_patterns():
    if os.path.exists(patterns_file_path):
        with open(patterns_file_path, "r") as f:
            return json.load(f)
    else:
        patterns = generate_patterns(target)
        with open(patterns_file_path, "w") as f:
            json.dump(patterns, f)
        return patterns

# Function to search for keywords in banners using Google
def search_banner_keywords_with_google(target):
    time.sleep(3)  # Wait for 3 seconds before making a request
    try:
        response = requests.get(f"https://www.google.com/search?q={target}+banner+keywords")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = soup.find_all('div', class_='BNeawe UPmit AP7Wnd')
        return [result.text for result in search_results]
    except Exception as e:
        logging.error(f"Error occurred while searching banner keywords on Google: {e}")
        return []

# Function to generate regex patterns
def generate_patterns(target):
    banner_keywords = [target, rf"<title>{target}</title>"]
    scores = [1, 2]  # Score of 1 for general presence, Score of 2 for presence in title
    return [{"regex": keyword, "score": score} for keyword, score in zip(banner_keywords, scores)]

# Function to search Shodan
def search_shodan(target):
    api = shodan.Shodan(os.environ["SHODAN_API_KEY"])
    try:
        time.sleep(1)  # Ensure we respect Shodan's rate limit
        return api.search(target)
    except shodan.exception.APIError as e:
        logging.error(f"Shodan API error occurred while searching for target '{target}': {e}")
        return {'matches': []}
    except Exception as e:
        logging.error(f"Unexpected error occurred while searching Shodan for target '{target}': {e}")
        return {'matches': []}

# Function to calculate score
def calculate_score(banner, patterns):
    score = 0
    try:
        for pattern in patterns:
            if re.search(pattern['regex'], banner, re.IGNORECASE):
                score += pattern['score']
        return score
    except Exception as e:
        logging.error(f"Error occurred while calculating score: {e}")
        return 0

# Function to process the Shodan results
def process_shodan_results(results, patterns):
    output = []
    for result in results.get('matches', []):
        try:
            banner = result['data']
            score = calculate_score(banner, patterns)
            output.append({"Score": score, "IP": result["ip_str"], "Data": banner})
        except Exception as e:
            logging.error(f"Error occurred while processing Shodan results: {e}")
    return output

# Function to save results to a JSON file
def save_to_json(results, filename="results.json"):
    with open(filename, "w") as f:
        json.dump(results, f)

# Function to save results to a CSV file
def save_to_csv(results, filename="results.csv"):
    with open(filename, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["Score", "IP", "Data"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

# Function to summarize the results
def summarize_results(processed_results):
    summary = {}
    for result in processed_results:
        ip = result['IP']
        score = result['Score']
        summary[ip] = summary.get(ip, 0) + score

    # Convert the summary dictionary into a list of dictionaries for uniformity
    summary_list = [{"IP": ip, "Total Score": score} for ip, score in summary.items()]
    return summary_list

def process_censys_results(results):
    """
    Process the results from Censys search.
    """
    output = []
    for result in results.get('results', []):
        try:
            ip = result['ip']
            metadata = result.get('metadata', {})
            country = metadata.get('country', 'Unknown')
            os_version = metadata.get('os_version', 'Unknown')
            protocols = result.get('protocols', [])
            
            # Score: Just a simple score based on number of protocols for demonstration. You can enhance this.
            score = len(protocols)
            
            output.append({
                "Score": score,
                "IP": ip,
                "Country": country,
                "OS Version": os_version,
                "Protocols": protocols
            })
        except Exception as e:
            logging.error(f"Error processing Censys result: {e}")
    
    return output
    
# Main execution starts here
try:
    # Load or generate patterns
    patterns_file_path = "patterns.json"
    patterns = load_patterns()

    # Using ThreadPoolExecutor to parallelize the searches
    with ThreadPoolExecutor(max_workers=2) as executor:
        shodan_future = executor.submit(search_shodan, target)
        censys_future = executor.submit(search_censys, target)
        
        shodan_results = shodan_future.result()
        censys_results = censys_future.result()

    # Process Shodan results
    processed_shodan_results = process_shodan_results(shodan_results, patterns)
    
    # Process Censys results (if you wish to do something with them)
    # For now, let's just print them
    for result in censys_results:
        logging.info(result)

    # Save to JSON and CSV
    save_to_json(processed_shodan_results)
    save_to_csv(processed_shodan_results)

except Exception as e:
    logging.critical(f"An unexpected error occurred during execution: {e}")
