from helperfunctions import request_page, wild_hold_item_parse
from bs4 import BeautifulSoup
import re

def scrape_page(url):
    """
    handles grabbing info from generation 5 pages on serebii
    expects a url to a gen5 pokedex page for a specific pokemon on serebii
    returns a string of the english name for the pokemon, and a dictionary containing the info for that pokemon which was scraped from the page
    if request_page from helperfunctions returns None, then this will return None, None
    """
    print(f"Now downloading: {url}")
    soup = request_page(url) # get the page to scrape
    if soup is not None: # check for null
        dextables = soup.find_all('table', class_='dextable')

        dextables_index = 1 # start at 1
        tr_tags = dextables[1].find_all('tr')

        # names
        td_tags = tr_tags[1].find_all('td', class_='fooinfo')
        eng_name = td_tags[0].text.strip()
        other_names = [name.strip() for name in td_tags[1].text.strip().split('\n')]
        jap_name = re.findall(r'[A-Za-z]+|[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+', other_names[0].split(": ")[1])
        fre_name = other_names[1].split(": ")[1]
        ger_name = other_names[2].split(": ")[1]
        kor_name = other_names[3].split(": ")[1]

        # numbers
        numbers = td_tags[2].find_all('tr')
        try:
            dex_num = int(re.sub(r'\D', '', numbers[0].find_all('td')[1].text.strip()))
        except ValueError:
            dex_num = 0
        try:
            bw_num = int(re.sub(r'\D', '', numbers[1].find_all('td')[1].text.strip()))
        except ValueError:
            bw_num = 0
        try:
            bw2_num = int(re.sub(r'\D', '', numbers[2].find_all('td')[1].text.strip()))
        except ValueError:
            bw2_num = 0
        
        entry = {
                "National Dex Number": dex_num,
                "Black/White Dex Number": bw_num,
                "Black 2/White 2 Dex Number": bw2_num,
                "Name (english)": eng_name,
                "Name (japanese)": jap_name,
                "Name (french)": fre_name,
                "Name (german)": ger_name,
                "Name (korean)": kor_name,
            }
        """
        to be added:

        "Male Ratio": mal_percent,
        "Female Ratio": fem_percent,
        "Type": typing,
        "Abilites": abilities,
        "Classification": classification,
        "Height (imperial)": imp_height,
        "Height (metric)": met_height,
        "Weight (imperial)": imp_weight,
        "Weight (metric)": met_weight,
        "Capture Rate": cap_rate,
        "Base Egg Steps": base_egg_steps,
        "XP Growth Points": xp_grow_pt,
        "XP Growth Speed": xp_grow_sp,
        "Base Happiness": base_happiness,
        "Effort Values Earned": ev_earned,
        "Flee Flag": flee_flag,
        "Entree Forest Level": forest_level,
        "Wild Hold Items": wild_hold_items,
        "Egg Groups": egg_groups,
        "Evolves at level": evolve_level,
        "Evolves Into": evolve_into,
        "Evolves From": evolve_from,
        "Locations": locations,
        "Flavor Text": flavor_text,
        "Moveset": moveset,
        "Base Stats": base_stats
        """
        
        print("Download Complete!")

        return eng_name,entry
    else:
        print("Download Failed: A problem occurred with the requested page.")

        return None, None