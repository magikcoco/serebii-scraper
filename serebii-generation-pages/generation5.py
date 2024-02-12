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

        ## dextables MAP ##
        # dextables[0]: sprites table
        # dextables[1]: general info table, includes names, pokdex numbers, gender ratio, types, abilities, classification, height, weight, capture rate
        # base egg steps, exp growth, base happiness, effor values earned, flee flag, and entree forest level
        # dextables[2]: damage taken chart
        # dextables[3]: wild hold item and egg group(s) info
        # dextables[4]: evolutionary chain
        # dextables[5]: locations
        # dextables[6]: flavor text
        # dextables[7]: the first move table. there are a variable number of these, so counting upwards from here doesnt work
        # dextables[-1]: stats information, including base stats, is the last dextable on the page

        dextables_index = 1 # start at 1
        tr_tags = dextables[1].find_all('tr') # the rows of the target dextable

        ## tr_tags MAP ##
        # tr_tags[0]: labels for names, dex numbers, gender ratio, and type
        # tr_tags[1]: english name, other names, dex numbers, gender ratio, and type data
        # tr_tags[2]: japanese name (from an embedded table)
        # tr_tags[3]: french name (from an embedded table)
        # tr_tags[4]: german name (from an embedded table)
        # tr_tags[5]: korean name (from an embedded table)
        # tr_tags[6]: national pokedex number (from an embedded table)
        # tr_tags[7]: BW unova pokdex number (from an embedded table)
        # tr_tags[8]: B2W2 pokedex number (from an embedded table)
        # tr_tags[9]: Male percent (from an embedded table)
        # tr_tags[10]: Female percent (from an embedded table)
        # tr_tags[11]: abilites label, includes list of the abilities this pokemon has (useful for easy parsing)
        # tr_tags[12]: abilities data, including descriptions of what they do
        # tr_tags[13]: labels for classification, height, weight, capture rate, and base egg steps
        # tr_tags[14]: classification, height, weight, cap rate, and base egg steps data
        # tr_tags[15]: exp growth, base happiness, effort values earned, flee flag, and entree forest level labels
        # tr_tags[16]: exp growth, base happiness, effort values earned, flee flag, and entree forest level data

        td_tags = tr_tags[1].find_all('td', class_='fooinfo') # the columns in the target row

        ## td_tags MAP ##
        # td_tags[0]: english name
        # td_tags[1]: other names (ordered as japanese, french, german, korean)
        # td_tags[2]: dex numbers
        # td_tags[3]: gender ratios (ordered male, female)
        # td_tags[4]: type(s)

        ### NAMES DATA ###
        eng_name = td_tags[0].text.strip() # english name is the first block
        other_names = [name.strip() for name in td_tags[1].text.strip().split('\n')] # a list of the other name strings, in the second block
        jap_name = re.findall(r'[A-Za-z]+|[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+', other_names[0].split(": ")[1]) # a list for both spellings
        fre_name = other_names[1].split(": ")[1] # french name
        ger_name = other_names[2].split(": ")[1] # german name
        kor_name = other_names[3].split(": ")[1] # korean name (no latin script here)

        ### POKEDEX NUMBERS DATA ###
        numbers = td_tags[2].find_all('tr') # this td has another table embedded within
        # these are formatted like:
        # National: 	#001
        # BW Unova: 	#---
        # B2W2 Unova: 	#---
        try:
            dex_num = int(re.sub(r'\D', '', numbers[0].find_all('td')[1].text)) # national dex no.
        except ValueError:
            dex_num = 0 # something went wrong here, there should always be a national dex number
        try:
            bw_num = int(re.sub(r'\D', '', numbers[1].find_all('td')[1].text)) # black/white dex no.
        except ValueError:
            bw_num = 0 # expected if not in the unova dex
        try:
            bw2_num = int(re.sub(r'\D', '', numbers[2].find_all('td')[1].text)) #BW2 dex no.
        except ValueError:
            bw2_num = 0 # expected if not in the unova dex
        
        ### GENDER RATIO DATA ###
        ratios = td_tags[3].find_all('tr') # this td has another table embedded within
        # formatted like:
        # Male ♂:	87.5%
        # Female ♀:	12.5%
        mal_percent = float(re.sub(r'[^\d.]', '', ratios[0].find_all('td')[1].text))
        fem_percent = float(re.sub(r'[^\d.]', '', ratios[1].find_all('td')[1].text))

        ### TYPE DATA ###
        # this needs to be extracted from the link in either the href attribute of the embedded a tags or the img tag embedded within the a tag
        typing = [a_tag['href'].split('/')[-1].split('.')[0] for a_tag in td_tags[4].find_all('a')]

        # changing rows
        td_tags = tr_tags[11].find_all('td', class_="fooleft") # the columns in the target row

        ## td_tags MAP ##
        # td_tags[0]: abilities label

        ### ABILITIES DATA ###
        abilities = [ability.replace("(Hidden Ability)", "").strip() for ability in td_tags[0].text.split(": ")[1].split(" - ")]

        # changing rows
        td_tags = tr_tags[14].find_all('td', class_="fooinfo") # the columns in the target row

        ## td_tags MAP ##
        # td_tags[0]: classification data
        # td_tags[1]: height data
        # td_tags[2]: weight data
        # td_tags[3]: capture rate
        # td_tags[4]: base egg steps

        ### CLASSIFICATION DATA ###
        classification = td_tags[0].text.strip()

        ### HEIGHT DATA ###
        heights = [height.strip() for height in td_tags[1].text.split("\n")]
        imp_height = heights[0]
        met_height = heights[1]

        ### WEIGHT DATA ###
        weights = [weight.strip() for weight in td_tags[2].text.split("\n")]
        imp_weight = weights[0]
        met_weight = weights[1]

        ### CAPTURE RATE DATA ###
        cap_rate = int(re.sub(r'\D', '', td_tags[3].text))

        ### BASE EGG STEPS DATA ###
        base_egg_steps = int(re.sub(r'\D', '', td_tags[3].text))

        entry = {
                "National Dex Number": dex_num,
                "Black/White Dex Number": bw_num,
                "Black 2/White 2 Dex Number": bw2_num,
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
            }
        """
        to be added:
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