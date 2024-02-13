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
        # contains all the target data
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
        tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable

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
        # td_tags[3]: capture rate data 
        # td_tags[4]: base egg steps data

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

        # changing rows
        td_tags = tr_tags[16].find_all('td', class_="fooinfo") # the columns in the target row

        ## td_tags MAP ##
        # td_tags[0]: xp growth data
        # td_tags[1]: base happiness data
        # td_tags[2]: effort values earned data
        # td_tags[3]: flee flag
        # td_tags[4]: entree forest level

        ### EXPERIENCE GROWTH DATA ###
        exp_datas = [exp_data for exp_data in td_tags[0].text.split(" Points")]
        xp_grow_pt = int(re.sub(r'\D', '', exp_datas[0]))
        xp_grow_sp = exp_datas[1]

        ### BASE HAPPINESS DATA ###
        base_happiness = int(td_tags[1].text.strip())

        ### EFFORT VALUES EARNED DATA ###
        ev_earned = [value.strip() for value in td_tags[2].text.split("\n")]

        ### FLEE FLAG DATA ###
        flee_flag = int(re.sub(r'\D', '', td_tags[3].text))

        ### ENTREE FOREST LEVEL ###
        forest_level = int(re.sub(r'\D', '', td_tags[4].text))

        # change tables
        dextables_index = dextables_index+2 # move to the wild hold items and egg groups table, skip the damage chart
        tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable

        ## tr_tags MAP ##
        # tr_tags[0]: labels for wild hold items, egg groups
        # tr_tags[1]: data for wild hold items and egg groups
        # tr_tags[2]: embedded table containing wild hold items
        # tr_tags[3]: embedded table containing egg group selectors

        td_tags = tr_tags[1].find_all('td', class_='fooinfo') # the columns in the target row

        ## td_tags MAP ##
        # td_tags[0]: wild hold items
        # td_tags[1]: egg groups

        ### WILD HOLD ITEM DATA ###
        wild_hold_items = wild_hold_item_parse(td_tags[0].text.strip())

        ### EGG GROUPS DATA ###
        egg_groups = []
        for tr_tag in td_tags[1].find('table').find_all('tr'):
            egg_groups.append(tr_tag.find_all('td')[1].find('a').text.strip())
        
        # change tables
        dextables_index = dextables_index + 1
        tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable

        ## tr_tags MAP ##
        # tr_tags[0]: label for evolutionary chain
        # tr_tags[1]: an embedded table called evochain
        # tr_tags[2]: row from the above embedded table

        td_tags = tr_tags[1].find_all('td')[1:] # cut off the first td, not needed

        ## td_tags MAP ##
        # td_tags[0]: first pokemon in the chain (always exists)
        # none of the following may exist
        # td_tags[1]: level or method by which the first pokemon evolves into the second
        # td_tags[2]: the second pokemon in the chain
        # td_tags[3]: level or method by which the second pokemon evolves into the third
        # td_tags[4]: the third pokemon in the chain

        evolutions = len(td_tags) # this should be either 1, 3, or 5 in length
        evolve_level, evolve_into, evolve_from = 0, 0, 0
        if evolutions == 5: # this means there are 3 pokemon in the chain
            # the images in the href elements point to a national dex number
            pkmn_one = int(re.sub(r'\D', '', td_tags[0].find('a')['href'].split('/')[-1].split('.')[0].strip()))
            pkmn_two = int(re.sub(r'\D', '', td_tags[2].find('a')['href'].split('/')[-1].split('.')[0].strip()))
            pkmn_three = int(re.sub(r'\D', '', td_tags[4].find('a')['href'].split('/')[-1].split('.')[0].strip()))
            # check different cases to see what this pokemon evolves into, and which they evolve from
            if dex_num == pkmn_one: # in this case, the pokemon being looked at is the first one in the evolution chain
                try:
                    evolve_level = int(re.sub(r'\D', '', td_tags[1].find('img')['src'].split('/')[-1].split('.')[0].strip()))
                except ValueError: # this will trigger if the pokemon does not evolve by level up, but by some other means (happiness, etc)
                    evolve_level = td_tags[1].find('img')['src'].split('/')[-1].split('.')[0].strip()
                evolve_into = pkmn_two # in this case the pokemon evolves into the second pokemon in the evolution chain
                evolve_from = pkmn_one # since the pokemon doesnt evolve from any pokemon, it will point to itself
            elif dex_num == pkmn_two: # in this case, the pokemon being looked at is the second one in the chain
                try:
                    evolve_level = int(re.sub(r'\D', '', td_tags[3].find('img')['src'].split('/')[-1].split('.')[0].strip()))
                except ValueError: # this will trigger if the pokemon does not evolve by level up, but by some other means (happiness, etc)
                    evolve_level = td_tags[3].find('img')['src'].split('/')[-1].split('.')[0].strip()
                evolve_into = pkmn_three # the second pokemon in the chain evoles into the third pokemon, and from the 1st
                evolve_from = pkmn_one
            else: # in this case, the pokemon is the third in the chain
                # being the last in the chain, it doesnt evolve, so its unnessecary to assign the evolve_level
                evolve_into = pkmn_three # it will point to itself for the evolve target
                evolve_from = pkmn_two # and evolves from the 2nd in the chain
        elif evolutions == 3: # in this case, the evolve chain contains only two pokemon
            # the same process as above, but only for two pokemon instead of three
            pkmn_one = int(re.sub(r'\D', '', td_tags[0].find('a')['href'].split('/')[-1].split('.')[0].strip()))
            pkmn_two = int(re.sub(r'\D', '', td_tags[2].find('a')['href'].split('/')[-1].split('.')[0].strip()))
            if dex_num == pkmn_one:
                try:
                    evolve_level = int(re.sub(r'\D', '', td_tags[1].find('img')['src'].split('/')[-1].split('.')[0].strip()))
                except ValueError:
                    evolve_level = td_tags[1].find('img')['src'].split('/')[-1].split('.')[0].strip()
                evolve_into = pkmn_two
                evolve_from = pkmn_one
            else:
                evolve_into = pkmn_two
                evolve_from = pkmn_one
        else: # this pokemon does not evolve
            evolve_into = pkmn_one
            evolve_from = pkmn_one
        
        # change table
        dextables_index = dextables_index + 1
        tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable

        ## tr_tags MAP ##
        # tr_tags[0]: label for locations
        # tr_tags[1]: black location
        # tr_tags[2]: white location
        # tr_tags[3]: black2 location
        # tr_tags[4]: white2 location

        ### LOCATIONS DATA ###
        locations = {}
        for tr_tag in tr_tags[1:]: # skip the first one, since its just the label
            td_tags = tr_tag.find_all('td')
            locations[td_tags[0].text.strip()] = td_tags[1].text.strip().split(", ")

        # change table
        dextables_index = dextables_index + 1
        tr_tags = dextables[dextables_index].find_all('tr')[1:]

        ## tr_tags MAP ##
        # tr_tags[0]: label for flavor text
        # tr_tags[1]: black flavor text, contains the flavor text for black, white, black2 and white2
        # tr_tags[2]: white flavor text
        # tr_tags[3]: black2 flavor text
        # tr_tags[4]: white2 flavor text

        ### FLAVOR TEXT DATA ###
        flavor_text = {}
        last_flavor = "No text" # necessary for reused td elements containing repeat flavor text across different games
        for tr_tag in tr_tags:
            td_tags = tr_tag.find_all('td')
            # this table is formatted in such a way that flavor text which is the same is not repeated
            if len(td_tags) > 1: # in this case there is flavor text
                last_flavor = td_tags[1].text.strip()
                flavor_text[td_tags[0].text.strip()] = last_flavor
            else:
                flavor_text[td_tags[0].text.strip()] = last_flavor

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
            }
        """
        to be added:
        "Moveset": moveset,
        "Base Stats": base_stats
        """
        
        print("Download Complete!")

        return eng_name,entry
    else:
        print("Download Failed: A problem occurred with the requested page.")

        return None, None