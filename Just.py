import requests
from bs4 import BeautifulSoup

URL = 'https://www.gartner.com/reviews/market/web-content-management'
response = requests.get(URL)
soup = BeautifulSoup(response.content, 'html.parser')

# Trying a more general approach by just looking for img tags with alt attributes.
product_names = [img['alt'] for img in soup.find_all('img') if img.has_attr('alt') and img['alt']]

# Save the product names to a .txt file
with open('products.txt', 'w') as file:
    for product in product_names:
        file.write(product + '\n')

print(product_names)
