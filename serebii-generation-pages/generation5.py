from helperfunctions import request_page, wild_hold_item_parse, setup_logger
from bs4 import BeautifulSoup
import re

logger = setup_logger()

def scrape_page(url):
    """
    handles grabbing info from generation 5 pages on serebii
    expects a url to a gen5 pokedex page for a specific pokemon on serebii
    returns a string of the english name for the pokemon, and a dictionary containing the info for that pokemon which was scraped from the page
    if request_page from helperfunctions returns None, then this will return None, None
    """
    global logger
    logger.info(f"Now downloading: {url}")
    soup = request_page(url) # get the page to scrape
    if soup is not None: # check for null
        # declare the entry dictionary
        entry = {}

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

        # default values
        tr_tags = None
        td_tags = None
        found_data = True

        dextables_index = 1 # start at 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find any dextable elements, aborting...")
            return None, None

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

        try:
            td_tags = tr_tags[1].find_all('td', class_='fooinfo') # the columns in the target row
        except Exception:
            logger.warning("Failed to find name, dex number, gender ratio, and type data...")
            found_data = False

        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: english name
            # td_tags[1]: other names (ordered as japanese, french, german, korean)
            # td_tags[2]: dex numbers
            # td_tags[3]: gender ratios (ordered male, female)
            # td_tags[4]: type(s)

            ### NAMES DATA ###
            other_names = [name.strip() for name in td_tags[1].text.strip().split('\n')] # a list of the other name strings, in the second block
            # add directly to the dictionary
            entry['Name (english)'] = td_tags[0].text.strip() # english name is the first block
            entry['Name (japanese)'] = re.findall(r'[A-Za-z]+|[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+', other_names[0].split(": ")[1]) # a list for both spellings
            entry['Name (french)'] = other_names[1].split(": ")[1] # french name
            entry['Name (german)'] = other_names[2].split(": ")[1] # german name
            entry['Name (korean)'] = other_names[3].split(": ")[1] # korean name (no latin script here)

            ### POKEDEX NUMBERS DATA ###
            numbers = td_tags[2].find_all('tr') # this td has another table embedded within
            # these are formatted like:
            # National: 	#001
            # BW Unova: 	#---
            # B2W2 Unova: 	#---
            try:
                entry['National Dex Number'] = int(re.sub(r'\D', '', numbers[0].find_all('td')[1].text)) # national dex no.
            except ValueError:
                entry['National Dex Number'] = 0 # something went wrong here, there should always be a national dex number
            try:
                entry['Black/White Dex Number'] = int(re.sub(r'\D', '', numbers[1].find_all('td')[1].text)) # black/white dex no.
            except ValueError:
                entry['Black/White Dex Number'] = 0 # expected if not in the unova dex
            try:
                entry['Black 2/White 2 Dex Number'] = int(re.sub(r'\D', '', numbers[2].find_all('td')[1].text)) #BW2 dex no.
            except ValueError:
                entry['Black 2/White 2 Dex Number'] = 0 # expected if not in the unova dex
            
            ### GENDER RATIO DATA ###
            ratios = td_tags[3].find_all('tr') # this td has another table embedded within
            # formatted like:
            # Male ♂:	87.5%
            # Female ♀:	12.5%
            entry['Male Ratio'] = float(re.sub(r'[^\d.]', '', ratios[0].find_all('td')[1].text))
            entry['Female Ratio'] = float(re.sub(r'[^\d.]', '', ratios[1].find_all('td')[1].text))

            ### TYPE DATA ###
            # this needs to be extracted from the link in either the href attribute of the embedded a tags or the img tag embedded within the a tag
            entry['Types'] = [a_tag['href'].split('/')[-1].split('.')[0] for a_tag in td_tags[4].find_all('a')]
        else:
            # need the national dex number here or else theres no way to save the data properly
            logger.critical("Without a national dex number no key is available to save data, aborting...")
            return None, None

        try: # changing rows
            td_tags = tr_tags[11].find_all('td', class_="fooleft") # the columns in the target row
        except Exception:
            logger.warning("Failed to find ability data...")
            found_data = False

        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: abilities label

            ### ABILITIES DATA ###
            entry['Abilities'] = [ability.replace("(Hidden Ability)", "").strip() for ability in td_tags[0].text.split(": ")[1].split(" - ")]
        else:
            found_data = True

        try: # changing rows
            td_tags = tr_tags[14].find_all('td', class_="fooinfo") # the columns in the target row
        except Exception:
            logger.warning("Failed to find classification, height, weight, capture rate, and base egg step data...")
            found_data = False
        
        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: classification data
            # td_tags[1]: height data
            # td_tags[2]: weight data
            # td_tags[3]: capture rate data 
            # td_tags[4]: base egg steps data

            ### CLASSIFICATION DATA ###
            classification = td_tags[0].text.strip()
            # add it to the dictonary
            entry['Classification'] = classification

            ### HEIGHT DATA ###
            heights = [height.strip() for height in td_tags[1].text.split("\n")]
            entry['Height (imp)'] = heights[0]
            entry['Height (met)'] = heights[1]

            ### WEIGHT DATA ###
            weights = [weight.strip() for weight in td_tags[2].text.split("\n")]
            entry['Weight (imp)'] = weights[0]
            entry['Weight (met)'] = weights[1]

            ### CAPTURE RATE DATA ###
            entry['Capture Rate'] = int(re.sub(r'\D', '', td_tags[3].text))

            ### BASE EGG STEPS DATA ###
            entry['Base Egg Steps'] = int(re.sub(r'\D', '', td_tags[3].text))
        else:
            found_data = True

        try: # changing rows
            td_tags = tr_tags[16].find_all('td', class_="fooinfo") # the columns in the target row
        except Exception:
            logger.warning("Failed to find XP growth, base happiness, EVs earned, flee flag, and entree forest level data...")
            found_data = False

        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: xp growth data
            # td_tags[1]: base happiness data
            # td_tags[2]: effort values earned data
            # td_tags[3]: flee flag
            # td_tags[4]: entree forest level

            ### EXPERIENCE GROWTH DATA ###
            exp_datas = [exp_data for exp_data in td_tags[0].text.split(" Points")]
            entry["XP Growth Points"] = int(re.sub(r'\D', '', exp_datas[0]))
            entry["XP Growth Speed"] = exp_datas[1]

            ### BASE HAPPINESS DATA ###
            entry["Base Happiness"] = int(td_tags[1].text.strip())

            ### EFFORT VALUES EARNED DATA ###
            entry["Effort Values Earned"] = [value.strip() for value in td_tags[2].text.split("\n")]

            ### FLEE FLAG DATA ###
            entry["Flee Flag"] = int(re.sub(r'\D', '', td_tags[3].text))

            ### ENTREE FOREST LEVEL ###
            entry["Entree Forest Level"] = int(re.sub(r'\D', '', td_tags[4].text))
        else:
            found_data = False

        # change tables
        dextables_index = dextables_index+2 # move to the wild hold items and egg groups table, skip the damage chart
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable, aborting...")
            # return non for key if there is no dex number
            return entry.setdefault('National Dex Number', None), entry

        ## tr_tags MAP ##
        # tr_tags[0]: labels for wild hold items, egg groups
        # tr_tags[1]: data for wild hold items and egg groups
        # tr_tags[2]: embedded table containing wild hold items
        # tr_tags[3]: embedded table containing egg group selectors

        try: # changing rows
            td_tags = tr_tags[1].find_all('td', class_='fooinfo') # the columns in the target row
        except Exception:
            logger.warning("Failed to find XP growth, base happiness, EVs earned, flee flag, and entree forest level data...")
            found_data = False

        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: wild hold items
            # td_tags[1]: egg groups

            ### WILD HOLD ITEM DATA ###
            entry['Wild Hold Items'] = wild_hold_item_parse(td_tags[0].text.strip())

            ### EGG GROUPS DATA ###
            entry['Egg Groups'] = []
            for tr_tag in td_tags[1].find('table').find_all('tr'):
                entry['Egg Groups'].append(tr_tag.find_all('td')[1].find('a').text.strip())
        else:
            found_data = True

        # change tables
        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable, aborting...")
            # default 
            return entry.setdefault('National Dex Number', None), entry

        ## tr_tags MAP ##
        # tr_tags[0]: label for evolutionary chain
        # tr_tags[1]: an embedded table called evochain
        # tr_tags[2]: row from the above embedded table

        try: # changing rows
            td_tags = tr_tags[1].find_all('td')[1:] # cut off the first td, not needed
        except Exception:
            logger.warning("Failed to find evolution chain data...")
            found_data = False

        if found_data:
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
                if entry['National Dex Number'] == pkmn_one: # in this case, the pokemon being looked at is the first one in the evolution chain
                    try:
                        evolve_level = int(re.sub(r'\D', '', td_tags[1].find('img')['src'].split('/')[-1].split('.')[0].strip()))
                    except ValueError: # this will trigger if the pokemon does not evolve by level up, but by some other means (happiness, etc)
                        evolve_level = td_tags[1].find('img')['src'].split('/')[-1].split('.')[0].strip()
                    evolve_into = pkmn_two # in this case the pokemon evolves into the second pokemon in the evolution chain
                    evolve_from = pkmn_one # since the pokemon doesnt evolve from any pokemon, it will point to itself
                elif entry['National Dex Number'] == pkmn_two: # in this case, the pokemon being looked at is the second one in the chain
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
                if entry['National Dex Number'] == pkmn_one:
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
            
            # add to dictionary
            entry['Evolve Level'] = evolve_level
            entry['Evolves From'] = evolve_from
            entry['Evolves Into'] = evolve_into
        else:
            found_data = True
        
        # change table
        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable, aborting...")
            # return none if no key
            return entry.setdefault('National Dex Number', None), entry

        ## tr_tags MAP ##
        # tr_tags[0]: label for locations
        # tr_tags[1]: black location
        # tr_tags[2]: white location
        # tr_tags[3]: black2 location
        # tr_tags[4]: white2 location

        try:
            ### LOCATIONS DATA ###
            entry['Locations'] = {}
            for tr_tag in tr_tags[1:]: # skip the first one, since its just the label
                td_tags = tr_tag.find_all('td')
                entry['Locations'][td_tags[0].text.strip()] = td_tags[1].text.strip().split(", ")
        except Exception:
            logger.warning("Failed to find locations data...")

        # change table
        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr')[1:] # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable, aborting...")
            # default to pokedex number none to indicate there is an issue
            return entry.setdefault('National Dex Number', None), entry

        ## tr_tags MAP ##
        # tr_tags[0]: label for flavor text
        # tr_tags[1]: black flavor text, contains the flavor text for black, white, black2 and white2
        # tr_tags[2]: white flavor text
        # tr_tags[3]: black2 flavor text
        # tr_tags[4]: white2 flavor text

        try:
            ### FLAVOR TEXT DATA ###
            entry['Flavor Text'] = {}
            last_flavor = "No text" # necessary for reused td elements containing repeat flavor text across different games
            for tr_tag in tr_tags:
                td_tags = tr_tag.find_all('td')
                # this table is formatted in such a way that flavor text which is the same is not repeated
                if len(td_tags) > 1: # in this case there is flavor text
                    last_flavor = td_tags[1].text.strip()
                    entry['Flavor Text'][td_tags[0].text.strip()] = last_flavor
                else:
                    entry['Flavor Text'][td_tags[0].text.strip()] = last_flavor
        except Exception:
            logger.warning("Failed to find flavor text data...")

        # change tables
        dextables_index = dextables_index + 1
        # this boolean is used to iterate through moveset tables, because there arent always the same amount of them
        more_move_tables = False # default value
        try:
            more_move_tables = not ("Stats" in dextables[dextables_index].find('tr').text)
        except Exception:
            logger.critical("Failed to find next dextable, aborting...")
            # default to pokedex number none to indicate a problem
            return entry.setdefault('National Dex Number', None), entry
        
        ### MOVESET DATA ###
        moveset = {}
        while(more_move_tables):
            tr_tags = dextables[dextables_index].find_all('tr')
            label = tr_tags[0].text.strip()
            if "Level" in label or "TM" in label:
                name_index = 1
            else:
                name_index = 0
            sub_moveset = {}
            for tr_tag in tr_tags[2::2]:
                td_tags = tr_tag.find_all('td')
                if name_index:
                    try:
                        level = int(td_tags[0].text.strip())
                    except ValueError: # if not level then set level to 0
                        level = 0
                else:
                    level = 0
                if len(td_tags) > 1: # prevents some weirdness with tables embedded in tables getting picked up as labels
                    sub_moveset[td_tags[name_index].text.strip()] = level
            moveset[label] = sub_moveset
            dextables_index = dextables_index + 1
            try:
                more_move_tables = not ("Stats" in dextables[dextables_index].find('tr').text)
            except Exception:
                logger.critical("Failed to find next dextable, aborting...")
                # default to none for dex num
                return entry.setdefault('National Dex Number', None), entry
        
        #add to dictionary
        entry['Moveset'] = moveset
        
        # change table
        # the dextables index isnt advanced here because its advanced already in the last iteration of the movesset while loop
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable, aborting...")
            # default to pokedex number none to indicate a problem
            return entry.setdefault('National Dex Number', None), entry

        ### BASE STATS DATA ###
        entry['Base Stats'] = {}
        try:
            labels = [td.text.strip() for td in tr_tags[1].find_all('td')[1:]]
            td_tags = tr_tags[2].find_all('td')[1:]
            for label, td_tag in zip(labels, td_tags):
                entry['Base Stats'][label] = int(td_tag.text.strip())
        except Exception:
            logger.warning("Failed to find base stats data...")
        
        logger.info("Download Completed!")

        return entry.setdefault('National Dex Number', None), entry
    else:
        logger.critical("Download Failed: A problem occurred with the requested page!")

        return None, None