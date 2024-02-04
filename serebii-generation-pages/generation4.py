from helperfunctions import request_page, wild_hold_item_parse
from bs4 import BeautifulSoup
import re

def scrape_page(url):
    """
    handles grabbing info from generation 3 pages on serebii
    xpects a url to a gen3 pokedex page for a specific pokemon on serebii
    returns a string of the english name for the pokemon, and a dictionary containing the info for that pokemon which was scraped from the page
    if request_page from helperfunctions returns None, then this will return None, None
    """
    print(f"Now downloading: {url}")
    soup = request_page(url) # get the page to scrape
    if soup is not None: # check for null
        dextables = soup.find_all('table', class_='dextable')
        dextables_index = 1 # skipping the first one
        tr_tags = ((BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr'))
        td_tags = tr_tags[1].find_all('td', class_='fooinfo')
        eng_name = td_tags[0].text.strip()
        jap_name = re.findall(r'[A-Za-z]+|[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+', td_tags[1].text.strip())
        numbers = td_tags[2].text.strip().split("#")[1:]
        dex_num = int(re.sub(r'\D', '', numbers[0].strip())) # strips out everything that would make parsing as int fail
        loc_num = int(re.sub(r'\D', '', numbers[1].strip())) # strips out everything that would make parsing as int fail


        entry = {
                "National Dex Number": dex_num,
                "Hoenn Dex Number": loc_num,
                "Name (english)": eng_name,
                "Name (japanese)": jap_name
            }
        
        print("Download Complete!")

        return eng_name, entry
    else:
        print("Download Failed: A problem occurred with the requested page.")

        return None, None