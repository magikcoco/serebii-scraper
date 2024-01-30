import requests
from bs4 import BeautifulSoup
import sys

print("Running: ", __file__)
print("In environment: ", sys.prefix)

def pokemon_page(link):
    print("Now downloading: "+link.text)

def national_dex_page(soup):
    table = soup.find('table') # find the table
    links = []
    for row in table.find_all('tr'): # iterate through table rows
        cells = row.find_all('td') # get all cells in row
        if len(cells) > 3: # check if there are at least 3 columns
            third_column = cells[3] # this is the cell with the target link
            link = third_column.find('a')
            if link and link.has_attr('href'):
                links.append(link['href'])
                pokemon_page(link)

def scrape_website(url):
    """
    scrape the serebii website for info
    """
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        national_dex_page(soup)
    else:
        print("Failed to retrieve the webpage: "+response)

url = "https://www.serebii.net/pokemon/nationalpokedex.shtml"
scrape_website(url)
