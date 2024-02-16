from helperfunctions import request_page, wild_hold_item_parse, setup_logger
from bs4 import BeautifulSoup
import re

logger = setup_logger()

def scrape_page(url):
    """
    handles grabbing info from generation 4 pages on serebii
    expects a url to a gen4 pokedex page for a specific pokemon on serebii
    returns a string of the english name for the pokemon, and a dictionary containing the info for that pokemon which was scraped from the page
    if request_page from helperfunctions returns None, then this will return None, None
    """
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
        # base egg steps, exp growth, base happiness, effor values earned, color, and safari zone flee rate
        # dextables[2]: damage taken chart
        # dextables[3]: wild hold item and egg group(s) info
        # dextables[4]: evolutionary chain
        # dextables[5]: flavor text
        # dextables[6]: locations
        # dextables[7]: the first move table. there are a variable number of these, so counting upwards from here doesnt work
        # dextables[-1]: stats information, including base stats, is the last dextable on the page

        # default values
        tr_tags = None
        td_tags = None
        found_data = True
        
        dextables_index = 1 # skipping the first one
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find any dextable elements, aborting...")
            return None, None

        ## tr_tags MAP ##
        # tr_tags[0]: labels for names, dex numbers, gender ratio, and type
        # tr_tags[1]: english name, japanese name, dex numbers, gender ratio, and type data
        # tr_tags[2]: national pokedex number (from an embedded table)
        # tr_tags[3]: johto pokedex number (from an embedded table)
        # tr_tags[4]: male ratio (from an embedded table)
        # tr_tags[5]: female ratio (from an embedded table)
        # tr_tags[6]: abilities label
        # tr_tags[7]: abilities data
        # tr_tags[8]: label for classification, height, weight, capture rate, and base egg steps
        # tr_tags[9]: data for classification, height, weight, capture rate, and base egg steps
        # tr_tags[10]: label for xp growth, base happiness, effort values earned, color, safari zone flee rate
        # tr_tags[11]: data for xp growth, base happiness, effort values earned, color, safari zone flee rate

        try:
            td_tags = tr_tags[1].find_all('td', class_='fooinfo') # the columns in the target row
        except Exception:
            logger.warning("Failed to find name, dex number, gender ratio, and type data...")
            found_data = False
        
        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: english name
            # td_tags[1]: japanse name
            # td_tags[2]: national and johto dex number
            # td_tags[3]: gender ratios (ordered male, female)
            # td_tags[4]: type(s)

            ### NAME DATA ###
            entry['Name (english)'] = td_tags[0].text.strip()
            entry['Name (japanse)'] = re.findall(r'[A-Za-z]+|[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+', td_tags[1].text.strip())

            ### DEX NUMBERS DATA ###
            numbers = td_tags[2].text.strip().split("#")[1:]
            entry['National Dex Number'] = int(re.sub(r'\D', '', numbers[0].strip())) # strips out everything that would make parsing as int fail
            entry['Johto Dex Number'] = int(re.sub(r'\D', '', numbers[1].strip())) # strips out everything that would make parsing as int fail

            ### GENDER RATIO DATA ###
            gender_ratio = td_tags[3].text.strip().split(":")[1:]
            entry['Male Ratio'] = float(re.sub(r'[^\d.]', '', gender_ratio[0].strip()))
            entry['Female Ratio']  = float(re.sub(r'[^\d.]', '', gender_ratio[1].strip()))

            ### TYPE DATA ###
            entry['Types'] = [a_tag['href'].split('/')[-1].split('.')[0] for a_tag in td_tags[4].find_all('a')[:2]]
        else:
            # need the name here or else theres no way to save the data properly
            logger.critical("Without a name no key is available to save data, aborting...")
            return None, None

        try: # changing rows
            td_tags = tr_tags[6].find_all('td', class_="fooleft") # the columns in the target row
        except Exception:
            logger.warning("Failed to find ability data...")
            found_data = False
        
        if found_data:
            ### ABILITIES DATA ###
            entry['Abilities'] = [ability.strip() for ability in td_tags[0].text.split(": ")[1].split(" & ")]
        else:
            found_data = True

        try: # changing rows
            td_tags = tr_tags[9].find_all('td', class_="fooinfo") # the columns in the target row
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
            entry['Classification'] = td_tags[0].text.strip()

            ### HEIGHT DATA ###
            entry['Height'] = td_tags[1].text.strip()

            ### WEIGHT DATA ###
            entry['Weight'] = td_tags[2].text.strip()

            ### CAPTURE RATE DATA ###
            entry['Capture Rate'] = int(re.sub(r'\D', '', td_tags[3].text))

            ### BASE EGG STEPS DATA ###
            entry['Base Egg Steps'] = int(re.sub(r'\D', '', td_tags[3].text))
        else:
            found_data = True

        try: # changing rows
            td_tags = tr_tags[11].find_all('td', class_="fooinfo") # the columns in the target row
        except Exception:
            logger.warning("Failed to find XP growth, base happiness, EVs earned, color, and safari zone flee rate data...")
            found_data = False
        
        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: xp growth data
            # td_tags[1]: base happiness data
            # td_tags[2]: effort values earned data
            # td_tags[3]: color
            # td_tags[4]: safari zone flee rate

            ### EXPERIENCE GROWTH DATA ###
            exp_datas = [exp_data for exp_data in td_tags[0].text.split(" Points")]
            entry['XP Growth Points'] = int(re.sub(r'\D', '', exp_datas[0]))
            entry['XP Growth Speed'] = exp_datas[1]

            ### BASE HAPPINESS DATA ###
            entry['Base Happiness'] = int(td_tags[1].text.strip())

            ### EFFORT VALUES EARNED DATA ###
            entry['Effort Values Earned'] = [value.strip() for value in td_tags[2].text.split("\n")]

            ### FLEE FLAG DATA ###
            entry['Color'] = td_tags[3].text.strip()

            ### ENTREE FOREST LEVEL ###
            entry['Safari Zone Flee Rate'] = int(re.sub(r'\D', '', td_tags[4].text))
        else:
            found_data = False

        # wild hold items and egg groups
        dextables_index = dextables_index + 2 # skip over damage taken table
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable, aborting...")
            # return none for key if there is no name
            return entry.setdefault('Name (english)', None), entry

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
            # default to none for missing name
            return entry.setdefault('Name (english)', None), entry

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
        
        # flavor text
        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr')[1:] # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable, aborting...")
            # default to name none to indicate there is an issue
            return entry.setdefault('Name (english)', None), entry

        ## tr_tags MAP ##
        # tr_tags[0]: label for flavor text
        # tr_tags[1]: diamond flavor text, contains the flavor text for black, white, black2 and white2
        # tr_tags[2]: pearl flavor text
        # tr_tags[3]: platinum flavor text
        # tr_tags[4]: heartgold flavor text (has its own flavor text)
        # tr_tags[5]: soulsilver flavor text (has its own flavor text)

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

        # locations
        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable, aborting...")
            # return none if no key
            return entry.setdefault('Name (english)', None), entry

        ## tr_tags MAP ##
        # tr_tags[0]: label for locations
        # tr_tags[1]: ruby location
        # tr_tags[2]: sapphire location
        # tr_tags[3]: emerald location
        # tr_tags[4]: firered location
        # tr_tags[5]: leafgreen location
        # tr_tags[6]: colosseum location
        # tr_tags[7]: XD location
        # tr_tags[8]: diamond location
        # tr_tags[9]: pearl location
        # tr_tags[10]: platinum location
        # tr_tags[11]: heartgold location
        # tr_tags[12]: soulsilver location

        try:
            ### LOCATIONS DATA ###
            entry['Locations'] = {}
            for tr_tag in tr_tags[1:-1]: # skip the first one, since its just the label, and the last one which is a link to trianer locations
                td_tags = tr_tag.find_all('td')
                entry['Locations'][td_tags[0].text.strip()] = re.split(r',|\n', td_tags[1].text.strip()) #locations split on newline as well as commas
        except Exception:
            logger.warning("Failed to find locations data...")
        
        # moveset
        dextables_index = dextables_index + 1
        # this boolean is used to iterate through moveset tables, because there arent always the same amount of them
        more_move_tables = False # default value
        try:
            more_move_tables = not ("Stats" in dextables[dextables_index].find('tr').text)
        except Exception:
            logger.critical("Failed to find next dextable, aborting...")
            # default to name none to indicate a problem
            return entry.setdefault('Name (english)', None), entry
        
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
                # default to none for name
                return entry.setdefault('Name (english)', None), entry
        
        #add to dictionary
        entry['Moveset'] = moveset

        # change table
        # the dextables index is only advanced by 1 because its advanced already in the last iteration of the movesset while loop
        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable, aborting...")
            # default to name none to indicate a problem
            return entry.setdefault('Name (english)', None), entry
        
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

        return entry.setdefault('Name (english)', None), entry
    else:
        logger.critical("Download Failed: A problem occurred with the requested page.")

        return None, None