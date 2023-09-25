import requests
from bs4 import BeautifulSoup

URL = 'https://www.gartner.com/reviews/market/web-content-management'
response = requests.get(URL)
soup = BeautifulSoup(response.content, 'html.parser')

# Find all anchor tags with the class "vendor-logo" and extract the alt attribute of the img tag within.
product_names = [a.img['alt'] for a in soup.find_all('a', class_='vendor-logo') if a.img]

print(product_names)
