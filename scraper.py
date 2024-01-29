import requests
from bs4 import BeautifulSoup
import sys

print("Running: ", __file__)
print("In environment: ", sys.prefix)

def scrape_website(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        for paragragh in paragraphs:
            print(paragragh.text)
    else:
        print("Failed to retrieve the webpage: "+response)

url = "https://www.serebii.net/pokemon/nationalpokedex.shtml"
scrape_website(url)
