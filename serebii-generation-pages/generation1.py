from helperfunctions import request_page, wild_hold_item_parse, setup_logger
from bs4 import BeautifulSoup
import re

logger = setup_logger()

def scrape_page(url):
    """
    handles grabbing info from generation 1 pages on serebii
    expects a url to a gen1 pokedex page for a specific pokemon on serebii
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
        # dextables[0]: pictures
        # dextables[1]: names, other names, dex numbers, gender ratio, type, classification, height, weight, capture rate, base egg steps
        # dextables[2]: xp growth, base happiness, effort values earned (appears to just be the base stats???)
        # dextables[3]: damage table
        # dextables[4]: wild hold item and egg groups
        # dextables[5]: evolution chart
        # dextables[6]: locations
        # dextables[7]: first move table
        # dextables[-1]: base stats

        # default values
        tr_tags = None # these are tr elements
        td_tags = None # td elements
        found_data = True # flag on wether to proceed into something

        dextables_index = 1 # for generation 3, start at the first dextable
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find any dextable elements, aborting...")
            return entry.setdefault('Name (english)', None), entry # nothing to return in this case, but follow the standard pattern anyway
        
        ## tr_tags MAP ##
        # tr_tags[0]: the label for label for name, other names, numbers, type
        # tr_tags[1]: the data under the above
        # tr_tags[2]: japanese name (embedded table)
        # tr_tags[3]: french name (embedded table)
        # tr_tags[4]: german name (embedded table)
        # tr_tags[5]: korean name (embedded table)
        # tr_tags[6]: labels for classification, height, weight, capture rate, and base egg steps
        # tr_tags[7]: data for the above

        try:
            td_tags = tr_tags[1].find_all('td', class_=['fooinfo', 'cen']) # the columns in the target row
        except Exception:
            found_data = False
        
        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: english name
            # td_tags[1]: japanese, french, german, and korean names
            # td_tags[2]: national and johto dex number
            # td_tags[3]: gender ratio
            # td_tags[4]: types

            ### NAME DATA ###
            entry['Name (english)'] = td_tags[0].text.strip()
            inner_table_td_tags = td_tags[1].find_all('td')[1::2]
            entry['Name (japanese)'] = re.findall(r'[A-Za-z]+|[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+', inner_table_td_tags[0].text.strip())
            entry['Name (french)'] = inner_table_td_tags[1].text.strip()
            entry['Name (german)'] = inner_table_td_tags[2].text.strip()
            entry['Name (korean)'] = inner_table_td_tags[3].text.strip()

            ### DEX NUMBER DATA ###
            entry['National Dex Number'] = int(re.sub(r'\D', '', td_tags[2].text.strip())) # strips out everything that would make parsing as int fail

            ### TYPE DATA ###
            entry['Types'] = [a_tag['href'].split('/')[-1].split('.')[0] for a_tag in td_tags[3].find_all('a')[:2]]
        else:
            # need the name here or else theres no way to save the data properly
            logger.warning("Failed to find name, dex number data...")
            logger.critical("Without a name no key is available to save data, aborting...")
            return entry.setdefault('Name (english)', None), entry # this will return null for the name but just for the sake of the pattern
        
        try:
            td_tags = tr_tags[7].find_all('td', class_='fooinfo') # the columns in the target row
        except Exception:
            found_data = False
        
        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: english name
            # td_tags[1]: japanese, french, german, and korean names
            # td_tags[2]: national and johto dex number
            # td_tags[3]: gender ratio
            # td_tags[4]: types

            ### CLASSIFICATION DATA ###
            entry['Classification'] = td_tags[0].text.strip()

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
        else:
            # need the name here or else theres no way to save the data properly
            logger.warning("Failed to find classification, height, weight, capture rate, and base egg step...")
            found_data = True

        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find any dextable elements, aborting...")
            return entry.setdefault('Name (english)', None), entry
        
        ## tr_tags MAP ##
        # tr_tags[0]: labels
        # tr_tags[1]: data

        try:
            td_tags = tr_tags[1].find_all('td', class_='fooinfo') # the columns in the target row
        except Exception:
            found_data = False
        
        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: xp growth
            # td_tags[1]: base happiness
            # td_tags[2]: effort values earned (appears to be base stats)

            ### XP GROWTH DATA ###
            exp_datas = [exp_data for exp_data in td_tags[0].text.split(" Points")]
            entry['XP Growth Points'] = int(re.sub(r'\D', '', exp_datas[0]))
            entry['XP Growth Speed'] = exp_datas[1]

            ### BASE STAT DATA ###
            entry['Base Stats'] = {}
            pattern = r'(\d+)\s*([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)'
            matches = re.findall(pattern, td_tags[1].text)
            # assign to appropriate value
            for number, label in matches:
                entry['Base Stats'][label.strip()] = int(number)
        else:
            # need the name here or else theres no way to save the data properly
            logger.critical("Failed to find xp growth, happiness, base stat data...")
            found_data = True
        
        dextables_index = dextables_index + 2 # skip damage chart
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find any dextable elements, aborting...")
            return entry.setdefault('Name (english)', None), entry
        
        ## tr_tags MAP ##
        # tr_tags[0]: labels
        # tr_tags[1]: data
        # tr_tags[2]: data in an embedded table above

        try:
            td_tags = tr_tags[2].find_all('td') # thentry['Locations'][td_tags[0].text.strip()] = td_tags[-1].text.strip()e columns in the target row
        except Exception:
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
                pkmn_one = int(re.sub(r'\D', '', td_tags[0].find('a')['href'].split('/')[-1].split('.')[0].strip()))
                evolve_into = pkmn_one
                evolve_from = pkmn_one
            
            # add to dictionary
            entry['Evolve Level'] = evolve_level
            entry['Evolves From'] = evolve_from
            entry['Evolves Into'] = evolve_into
        else:
            logger.warning("Failed to find evole chain data...")
            found_data = True
        
        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find any dextable elements, aborting...")
            return entry.setdefault('Name (english)', None), entry
        
        ## tr_tags MAP ##
        # tr_tags[0]: label
        # tr_tags[1]: game (games continue further in successive indexes)

        ### LOCATION DATA ###
        #FIXME: all the locations just say "details". the "if len() > 2" luikely offender here
        #FIXME: in cases like venonat, the locations are the key and not the value???? wtf????
        entry['Locations'] = {}
        for locations in range(len(tr_tags) - 1, 1, -1):
            try:
                td_tags = tr_tags[locations].find_all('td') # the columns in the target row
                entry['Locations'][td_tags[0].text.strip()] = td_tags[-1].text.strip()
                if len(td_tags) > 2: # green (Jp) and Blue (Intl) share a line
                    entry['Locations'][td_tags[1].text.strip()] = td_tags[-1].text.strip()
            except Exception:
                logger.warning("Failed to find all location data...")
        
        # Level up moves
        dextables_index = dextables_index + 1
        # this boolean is used to iterate through moveset tables, because there arent always the same amount of them
        more_move_tables = False # default value
        try:
            more_move_tables = not ("Steps" in dextables[dextables_index].find('tr').text) # if this is true there are no more move tables
        except Exception:
            logger.critical("Failed to find next dextable (1st moveset), aborting...")
            # default to name none to indicate a problem
            return entry.setdefault('Name (english)', None), entry

        ### MOVESET DATA ###
        moveset = {}
        while(more_move_tables):
            tr_tags = dextables[dextables_index].find_all('tr')
            label = tr_tags[0].text.strip() # label for the move
            if "Level" in label or "TM" in label:
                name_index = 1 # Level | Name | Other stuff
            else:
                name_index = 0 # Name | Other stuff
            sub_moveset = {} # different parts of the moveset from different places
            for tr_tag in tr_tags[2::2]: # skip the move table label and the column labels, every other element is description text skip that too
                td_tags = tr_tag.find_all('td')
                if name_index: # true if name_index is 1
                    try:
                        level = int(td_tags[0].text.strip())
                    except ValueError: # if not level then set level to 0
                        level = 0
                else:
                    level = 0 # no level listed so just set it to 0
                if len(td_tags) > 1: # prevents some weirdness with tables embedded in tables getting picked up as labels
                    sub_moveset[td_tags[name_index].text.strip()] = level # add the move as the key and the level as the value
            moveset[label.replace(" (Details)", "")] = sub_moveset # add the whole table as a dictionary with its header as the key
            dextables_index = dextables_index + 1
            try: # check the next table
                more_move_tables = not ("Stats" in dextables[dextables_index].find('tr').text)
            except Exception:
                logger.critical("Failed to find next dextable (moveset), aborting...")
                # default to none for name
                return entry.setdefault('Name (english)', None), entry
        
        #add to dictionary
        entry['Moveset'] = moveset

        logger.info("Download Complete!")

        return entry.setdefault('Name (english)', None), entry
    else:
        logger.critical("Download Failed: A problem occurred with the requested page.")

        return None, None