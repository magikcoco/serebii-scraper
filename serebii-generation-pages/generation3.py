from helperfunctions import request_page, wild_hold_item_parse, setup_logger
from bs4 import BeautifulSoup
import re

logger = setup_logger()

def scrape_page(url):
    """
    handles grabbing info from generation 3 pages on serebii
    expects a url to a gen3 pokedex page for a specific pokemon on serebii
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
        # dextables[0]: sprites, national dex number, hoenn number, english and japanese names, abilities, gender ratio, classification, types,
        # height, weight, evolution chain
        # dextables[1]: wild hold item, dex category, color category, and footprint
        # dextables[2]: damage taken chart
        # dextables[3]: flavor text
        # dextables[4]: location
        # dextables[5]: first move table
        # dextables[-3]: egg steps to hatch, effort points from battling, catch rate
        # dextables[-2]: egg groups
        # dextables[-1]: base stats

        # default values
        tr_tags = None # these are tr elements
        td_tags = None # td elements
        found_data = True # flag on wether to proceed into something

        dextables_index = 0 # for generation 3, start at the first dextable
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find any dextable elements, aborting...")
            return entry.setdefault('Name (english)', None), entry # nothing to return in this case, but follow the standard pattern anyway
        
        ## tr_tags MAP ##
        # tr_tags[0]: the label for pokemon game picture, national no. etc
        # tr_tags[1]: the data under the above
        # tr_tags[2]: a gif portrait
        # tr_tags[3]: the row containing a fooinfo with the ability text
        # tr_tags[4]: another picture
        # tr_tags[5]: the explanation for the ability
        # tr_tags[6]: a picture and the gender ratio label
        # tr_tags[7]: another picture
        # tr_tags[8]: the gender ratio information
        # tr_tags[9]: labels for classification, types, etc
        # tr_tags[10]: info for the above
        # tr_tags[11]: evolution chain label
        # tr_tags[12]: evolution chain info

        try:
            td_tags = tr_tags[1].find_all('td', class_='fooinfo') # the columns in the target row
        except Exception:
            logger.warning("Failed to find name, dex number data...")
            found_data = False

        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: ruby/sapphire portraits
            # td_tags[1]: national dex number
            # td_tags[2]: local dex number
            # td_tags[3]: english name
            # td_tags[4]: japanese name

            ### DEX NUMBER DATA ###
            entry['National Dex Number'] = int(re.sub(r'\D', '', td_tags[1].text.strip())) # strips out everything that would make parsing as int fail
            entry['Hoenn Dex Number'] = int(re.sub(r'\D', '', td_tags[2].text.strip())) # strips out everything that would make parsing as int fail

            ### NAME DATA ###
            entry['Name (english)'] = td_tags[3].text.strip()
            entry['Name (japanese)'] = re.findall(r'[A-Za-z]+|[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+', td_tags[4].text.strip())
        else:
            # need the name here or else theres no way to save the data properly
            logger.critical("Without a name no key is available to save data, aborting...")
            return entry.setdefault('Name (english)', None), entry # this will return null for the name but just for the sake of the pattern

        try:
            td_tags = tr_tags[3].find_all('td', class_='fooinfo') # the columns in the target row
        except Exception:
            logger.warning("Failed to find name, dex number data...")
            found_data = False
        
        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: firered/leafgreen portraits
            # td_tags[1]: ability label

            ### ABILITY DATA ###
            entry['Abilities'] = td_tags[1].text.strip().split(": ")[1].split(" & ")
        else:
            logger.warning("Failed to find ability data...")
            found_data = True

        # sometimes elements may be missing which change where exactly in the table this info might be
        try:
            td_tags = tr_tags[8].find_all('td', class_='fooinfo')
        except IndexError:
            try:
                td_tags = tr_tags[7].find_all('td', class_='fooinfo')
            except Exception:
                found_data = False
        except Exception:
            found_data = False
        
        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: male ratio float
            # td_tags[1]: female ratio float

            ### GENDER RATIO DATA ###
            entry['Male Ratio'] = float(re.sub(r'[^\d.]', '', td_tags[0].text.strip()))
            entry['Female Ratio'] = float(re.sub(r'[^\d.]', '', td_tags[1].text.strip()))
        else:
            logger.warning("Failed to find gender ratio data...")
            found_data = True


        # sometimes elements may be missing which change where exactly in the table this info might be
        try:
            td_tags = tr_tags[10].find_all('td', class_='fooinfo')
        except IndexError:
            try:
                td_tags = tr_tags[9].find_all('td', class_='fooinfo')
            except Exception:
                found_data = False
        except Exception:
            found_data = False
        
        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: classification
            # td_tags[1]: type1
            # td_tags[2]: type2
            # td_tags[3]: height
            # td_tags[4]: weight

            ### CLASSIFICATION DATA ###
            entry['Classification'] = td_tags[0].text.strip()

            ### ABILITY DATA ###
            entry['Types'] = [a_tag['href'].split('/')[-1].split('.')[0] for a_tag in [a for td in td_tags[1:3] for a in td.find_all('a')][:2]]

            ### HEIGHT DATA ###
            entry['Height'] = td_tags[3].text.strip()

            ### WEIGHT DATA ###
            entry['Weight'] = td_tags[4].text.strip()
        else:
            logger.warning("Failed to find classification, types, height, and weight data...")
            found_data = True
        
        # sometimes elements may be missing which change where exactly in the table this info might be
        try:
            td_tags = tr_tags[12].find_all('td', class_='fooinfo')
        except IndexError:
            try:
                td_tags = tr_tags[11].find_all('td', class_='fooinfo')
            except Exception:
                found_data = False
        except Exception:
            found_data = False

        if found_data:
            ## td_tags MAP ##
            # td_tags[0]: evolution chain

            ### EVOLUTION DATA ###
            a_tags = td_tags[0].find_all('a')
            evolutions = len(a_tags) # this should be either 1, 2, or 3 in length
            # this wont pick up images
            levels = [int(re.sub(r'\D', '', level)) for level in td_tags[0].text.strip().split(">") if re.sub(r'\D', '', level).isdigit()]
            # so create a list of images
            image_names = []
            for img in td_tags[0].find_all('img', recursive=False):
                image_names.append(img['src'].split('.')[0])
            image_index = 0

            abort_levels = False # this will indicate a problem so the loop can be broken from inside the nested except block

            levels = []
            for level in td_tags[0].text.strip().split(">"):
                try:
                    levels.append(int(re.sub(r'\D', '', level)))
                except Exception:
                    try:
                        levels.append(image_names[image_index])
                    except Exception:
                        abort_levels = True
                if abort_levels:
                    break
                image_index = image_index + 1 # advance the index either way to stay in the right spot
            
            evolve_level, evolve_into, evolve_from = 0, 0, 0 #default all 3 to zero
            if not abort_levels:
                if evolutions == 3: # if there are 3 pokemon in the chain
                    #national dex numbers
                    pkmn_one = int(re.sub(r'\D', '', a_tags[0]['href'].split('/')[-1].split('.')[0].strip()))
                    pkmn_two = int(re.sub(r'\D', '', a_tags[1]['href'].split('/')[-1].split('.')[0].strip()))
                    pkmn_three = int(re.sub(r'\D', '', a_tags[2]['href'].split('/')[-1].split('.')[0].strip()))

                    if entry['National Dex Number'] == pkmn_one: # if the current pokemon is the first
                        evolve_from = pkmn_one
                        evolve_to = pkmn_two
                        evolve_level = levels[0]
                    elif entry['National Dex Number'] == pkmn_two: # if the current pokemon is the second
                        evolve_from = pkmn_one
                        evolve_to = pkmn_three
                        evolve_level = levels[1]
                    else: # in this case the current pokemon is the third
                        evolve_from = pkmn_two
                        evolve_to = pkmn_three
                elif evolutions == 2: # if there are two pokemon, same as 3 but a little simpler
                    pkmn_one = int(re.sub(r'\D', '', a_tags[0]['href'].split('/')[-1].split('.')[0].strip()))
                    pkmn_two = int(re.sub(r'\D', '', a_tags[1]['href'].split('/')[-1].split('.')[0].strip()))

                    evolve_into = pkmn_two # in all cases the pokemon evolves from the first and into the second
                    evolve_from = pkmn_one # because a pokemon points to itself if it doesnt evolve from or to something

                    if entry['National Dex Number'] == pkmn_one: # but only in the case where the current pokemon is the first will a level be added
                        evolve_level = levels[0]
                else: # if there is only one pokemon, then level can stay at 0 by default and itll point to itself
                    pkmn_one = int(re.sub(r'\D', '', a_tags[0]['href'].split('/')[-1].split('.')[0].strip()))
                    evolve_into = pkmn_one
                    evolve_from = pkmn_one 
            
            # add to dictionary
            entry['Evolve Level'] = evolve_level
            entry['Evolves From'] = evolve_from
            entry['Evolves Into'] = evolve_into
        else:
            logger.warning("Failed to find evolve chain data...")
            found_data = True

        
        # Wild hold item, dex category, color category
        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable (wild hold item+), aborting...")
            return entry.setdefault('Name (english)', None), entry
        
        try:
            td_tags = tr_tags[1].find_all('td')
        except Exception:
            found_data = False

        if found_data:
            ### WILD HOLD ITEM DATA ###
            entry['Wild Hold Items'] = wild_hold_item_parse(td_tags[0].text.strip())

            ### DEX CATEGORY DATA ###
            entry['Dex Category'] = td_tags[1].find('a')['href'].split('/')[-1].split('.')[0]

            ### COLOR CATEGORY ###
            entry['Color Category'] = td_tags[2].text.strip()
        else:
            logger.warning("Failed to find wild hold item, dex category, and color data...")
            found_data = True

        # Flavor text
        dextables_index = dextables_index + 2
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable (flavor text), aborting...")
            return entry.setdefault('Name (english)', None), entry

        try:
            entry['Flavor Text'] = {}
            for tr_tag in tr_tags[1:]: # first element in the list is the label "flavortext"
                tds = tr_tag.find_all('td')
                entry['Flavor Text'][tds[0].text.strip()] = tds[1].text.strip() # Game: Text
        except Exception:
            logger.warning("Failed to find flavor text data...")

        # Locations
        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find next dextable (locations), aborting...")
            return entry.setdefault('Name (english)', None), entry
        
        try:
            entry['Locations'] = {}
            for tr_tag in tr_tags[2:]: # the first two elements are labels "Location" and etc
                tds = tr_tag.find_all('td')
                entry['Locations'][tds[0].text.strip()] = tds[1].text.strip().split(", ") # Game: Location, Location...
        except Exception:
            logger.warning("Failed to find flavor text data...")
        
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
            moveset[label] = sub_moveset # add the whole table as a dictionary with its header as the key
            dextables_index = dextables_index + 1
            try: # check the next table
                more_move_tables = not ("Steps" in dextables[dextables_index].find('tr').text)
            except Exception:
                logger.critical("Failed to find next dextable (moveset), aborting...")
                # default to none for name
                return entry.setdefault('Name (english)', None), entry
        
        #add to dictionary
        entry['Moveset'] = moveset
        
        # Egg Steps, Effort Points gained, Catch rate
        # dextables will be incremented already by the loop prior
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find any dextable elements, aborting...")
            return entry.setdefault('Name (english)', None), entry
        
        try:
            td_tags = tr_tags[1].find_all('td')
        except Exception:
            found_data = False

        if found_data:
            entry['Egg Steps'] = int(re.sub(r'\D', '', td_tags[0].text.strip()))
            entry['Effort Values Earned'] = []
            for pt in td_tags[1].text.strip().split(", "):
                entry['Effort Values Earned'].append(pt)
            entry['Catch Rate'] = int(re.sub(r'\D', '', td_tags[2].text.strip()))
        else:
            logger.warning("Failed to find egg steps, effort values, catch rate data...")
            found_data = True

        # Egg groups
        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr')[2:] # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find any dextable elements, aborting...")
            return entry.setdefault('Name (english)', None), entry
        
        try:
            entry['Egg Groups'] = []
            for tr_tag in tr_tags:
                entry['Egg Groups'].append(tr_tag.find_all('td')[1].text.strip())
        except Exception:
            logger.warning("Failed to find egg groups data...")
        
        # Base stats
        dextables_index = dextables_index + 1
        try:
            tr_tags = dextables[dextables_index].find_all('tr') # the rows of the target dextable
        except Exception:
            logger.critical("Failed to find any dextable elements, aborting...")
            return entry.setdefault('Name (english)', None), entry
        
        try:
            td_tags = tr_tags[2].find_all('td', class_='cen')
        except Exception:
            found_data = False
        
        if found_data:
            labels = [td.text.strip() for td in tr_tags[1].find_all('td')[1:]]
            entry['Base Stats'] = {}
            for index, td_tag in enumerate(td_tags):
                entry['Base Stats'][labels[index]] = int(td_tag.text.strip())
        else:
            logger.warning("Failed to find base stats data...")
        
        logger.info("Download Complete!")

        return entry.setdefault('Name (english)', None), entry
    else:
        logger.critical("Download Failed: A problem occurred with the requested page.")

        return None, None