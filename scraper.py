import sys
sys.path.insert(0, './serebii-generation-pages')
import generation1, generation2, generation3, generation4, generation5
from helperfunctions import request_page, setup_logger
from autosavedict import AutoSaveDict
from bs4 import BeautifulSoup
import requests, re, time


logger = setup_logger()
logger.info(f"Running: '{__file__}' in environment: '{sys.prefix}'")

pokemondict = AutoSaveDict(file_path="./pokedex_data.json") # save json to current directory

def scrape_gen_page(gen, url):
    """
    handles redirecting to the appropriate generation-specific function
    """
    global logger, pokemondict
    # generation pages vary slightly in format so each generation is split into seperate functions
    # additionally if only one page is changed, not all of them break
    if gen == 1:
        key, value = generation1.scrape_page(url)
        if key is not None and value is not None:
            gendict = pokemondict.setdefault("Gen 1", {})
            gendict[key] = value
            pokemondict["Gen 1"] = gendict
        else:
            logger.error(f"No data was returned for {url}, value was: {value}")
        exit() #TODO: remove this
    elif gen == 2:
        key, value = generation2.scrape_page(url)
        if key is not None and value is not None:
            gendict = pokemondict.setdefault("Gen 2", {})
            gendict[key] = value
            pokemondict["Gen 2"] = gendict
        else:
            logger.error(f"No data was returned for {url}, value was: {value}")
    elif gen == 3:
        key, value = generation3.scrape_page(url)
        if key is not None and value is not None:
            gendict = pokemondict.setdefault("Gen 3", {})
            gendict[key] = value
            pokemondict["Gen 3"] = gendict
        else:
            logger.error(f"No data was returned for {url}, value was: {value}")
    elif gen == 4:
        key, value = generation4.scrape_page(url)
        if key is not None and value is not None:
            gendict = pokemondict.setdefault("Gen 4", {})
            gendict[key] = value
            pokemondict["Gen 4"] = gendict
        else:
            logger.error(f"No data was returned for {url}, value was: {value}")
    elif gen == 5:
        key, value = generation5.scrape_page(url)
        if key is not None and value is not None:
            gendict = pokemondict.setdefault("Gen 5", {})
            gendict[key] = value
            pokemondict["Gen 5"] = gendict
        else:
            logger.error(f"No data was returned for {url}, value was: {value}")
    elif gen == 6:
        #gen_six_page(url)
        logger.warning("Skipping gen 6...")
    elif gen == 7:
        #gen_seven_page(url)
        logger.warning("Skipping gen 7...")
    elif gen == 8:
        #gen_eight_page(url)
        logger.warning("Skipping gen 8...")
    elif gen == 9:
        #gen_nine_page(url)
        logger.warning("Skipping gen 9...")
    else:
        logger.warning(f"Unsupported generation: {gen}") # the last good one was 5, they should have never left using sprites

def scrape_pokemon_page(url):
    """
    grabs a table of links for each generation in which the target pokemon appears and calls pen_page on each one
    """
    logger.info("Accessing: "+url)
    soup = request_page(url) # get the page and make sure its not None
    if soup is not None:
        #target_table_index = 2 # the table we want is the 2nd one of class dextab
        tables = soup.find_all('table', class_='dextab')
        for table in tables:
            if table.find('td', class_='pkmn'): # the target table contains td elements of class pkmn, which no other dextab table has
                links = table.find_all('a')
                total_links = len(links)
                for index, link in enumerate(links):
                    gen = total_links - index # they are listed in descending generation, so the first number should be the highest
                    scrape_gen_page(gen, "https://www.serebii.net"+link['href']) #call gen_page with the full url

def scrape_national_dex_page(url):
    """
    scrape the serebii website for info
    """
    logger.info(f"Accessing: {url}")
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
                    scrape_pokemon_page("https://www.serebii.net"+link['href'])

start = time.time()
url = "https://www.serebii.net/pokemon/nationalpokedex.shtml" # this is currently the link to the national pokedex page on serebii
scrape_national_dex_page(url)
end = time.time()
exec_time = end - start
logger.info(f"Execution time: {exec_time}")
