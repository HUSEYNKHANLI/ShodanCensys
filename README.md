# ShodanCensys
Of course! Below is a `README.md` format for your script, suitable for GitHub:

---

# Target Search Tool

This script facilitates the search of a given target across various online platforms: Shodan, Censys, and Google. It processes and visualizes the results to provide insights into the target's online presence.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features
1. **Search Platforms**: Utilizes Shodan, Censys, and Google to search for a given target.
2. **Concurrent Searching**: Employs parallel processing to expedite searches.
3. **Data Visualization**: Plots the distribution of IP addresses by country.
4. **Data Export**: Exports search results to both JSON and CSV formats.

## Prerequisites
- Python 3.x
- Required Python libraries: `os`, `shodan`, `re`, `requests`, `json`, `csv`, `BeautifulSoup`, `argparse`, `logging`, `censys.search`, `ThreadPoolExecutor`, `decouple`, and `matplotlib`.

## Setup
1. Clone this repository:
```bash
git clone <repository-url>
```
2. Navigate to the project directory and install the required packages:
```bash
cd <directory-name>
pip install -r requirements.txt
```
3. Setup your environment variables or configuration file for the Censys API credentials (`CENSYS_API_ID` & `CENSYS_API_SECRET`).

## Usage
Execute the script and provide a target for the search:
```bash
python script.py <target>
```
Replace `<target>` with the specific term or entity you wish to search 
