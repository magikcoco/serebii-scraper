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

        entry = {
                "National Dex Number": dex_num,
                "Hoenn Dex Number": loc_num,
                "Name (english)": eng_name,
                "Name (japanese)": jap_name,
                "Name (french)": fre_name,
                "Name (german)": ger_name,
                "Name (korean)": kor_name,
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
            }
        
        print("Download Complete!")

        return eng_name, entry
    else:
        print("Download Failed: A problem occurred with the requested page.")

        return None, None