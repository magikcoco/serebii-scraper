import requests
from bs4 import BeautifulSoup
import sys

print("Running: ", __file__)
print("In environment: ", sys.prefix)

def request_page(url):
    response = requests.get(url)
    print(f"Webpage response: {response.status_code}")
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        return None

def gen_one_page(url):
    print(f"Now downloading: {url}")

def gen_two_page(url):
    print(f"Now downloading: {url}")

def gen_three_page(url):
    print(f"Now downloading: {url}")

def gen_four_page(url):
    print(f"Now downloading: {url}")

def gen_five_page(url):
    print(f"Now downloading: {url}")

def gen_six_page(url):
    print(f"Now downloading: {url}")

def gen_seven_page(url):
    print(f"Now downloading: {url}")

def gen_eight_page(url):
    print(f"Now downloading: {url}")

def gen_nine_page(url):
    print(f"Now downloading: {url}")

def gen_page(gen, url):
    if gen == 1:
        gen_one_page(url)
    elif gen == 2:
        gen_two_page(url)
    elif gen == 3:
        gen_three_page(url)
    elif gen == 4:
        gen_two_page(url)
    elif gen == 5:
        gen_three_page(url)
    elif gen == 6:
        gen_two_page(url)
    elif gen == 7:
        gen_three_page(url)
    elif gen == 8:
        gen_two_page(url)
    elif gen == 9:
        gen_three_page(url)
    else:
        print(f"Unsupported generation: {gen}")

def pokemon_page(url):
    print("Accessing: "+url)
    soup = request_page(url)
    if soup is not None:
        target_table_index = 2
        tables = soup.find_all('table', class_='dextab')
        for table in tables:
            if table.find('td', class_='pkmn'):
                links = table.find_all('a')
                total_links = len(links)
                for index, link in enumerate(links):
                    gen = total_links - index
                    gen_page(gen, "https://www.serebii.net"+link['href'])

def scrape_website(url):
    """
    scrape the serebii website for info
    """
    print(f"Accessing: {url}")
    soup = request_page(url)
    if soup is not None:
        table = soup.find('table') # find the table
        links = []
        for row in table.find_all('tr'): # iterate through table rows
            cells = row.find_all('td') # get all cells in row
            if len(cells) > 3: # check if there are at least 3 columns
                third_column = cells[3] # this is the cell with the target link
                link = third_column.find('a')
                if link and link.has_attr('href'):
                    links.append(link['href'])
                    pokemon_page("https://www.serebii.net"+link['href'])

url = "https://www.serebii.net/pokemon/nationalpokedex.shtml"
scrape_website(url)
