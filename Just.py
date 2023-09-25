from selenium import webdriver
from bs4 import BeautifulSoup

# Path to the ChromeDriver executable (adjust as necessary)
CHROMEDRIVER_PATH = '/path/to/chromedriver'

# Set up the Selenium driver
driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH)
driver.get('https://www.gartner.com/reviews/market/web-content-management')

# Give the page some time to load dynamically-loaded content
driver.implicitly_wait(10)

# Get the page source and parse with Beautiful Soup
soup = BeautifulSoup(driver.page_source, 'html.parser')
product_names = [img['alt'] for img in soup.find_all('img') if img.has_attr('alt') and img['alt']]

# Save the product names to a .txt file
with open('products.txt', 'w') as file:
    for product in product_names:
        file.write(product + '\n')

driver.quit()
print(product_names)
