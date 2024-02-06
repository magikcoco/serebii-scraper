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
        
        #names, dex numbers, gender ratio, types
        dextables_index = 1 # skipping the first one
        tr_tags = ((BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr'))
        td_tags = tr_tags[1].find_all('td', class_='fooinfo')
        eng_name = td_tags[0].text.strip()
        jap_name = re.findall(r'[A-Za-z]+|[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+', td_tags[1].text.strip())
        numbers = td_tags[2].text.strip().split("#")[1:]
        dex_num = int(re.sub(r'\D', '', numbers[0].strip())) # strips out everything that would make parsing as int fail
        loc_num = int(re.sub(r'\D', '', numbers[1].strip())) # strips out everything that would make parsing as int fail
        gender_ratio = td_tags[3].text.strip().split(":")[1:]
        mal_percent = float(re.sub(r'[^\d.]', '', gender_ratio[0].strip()))
        fem_percent = float(re.sub(r'[^\d.]', '', gender_ratio[1].strip()))
        type1, type2 = [a_tag['href'].split('/')[-1].split('.')[0] for a_tag in td_tags[4].find_all('a')[:2]]
        typing = [type1, type2]

        # abilities, using the label in this case since its easier
        abilities = [ability.strip() for ability in tr_tags[6].find('td').text.split(":")[1].split("&")]

        # classification, height (imp), weight (imp), cap rate, base egg steps
        try:
            td_tags = tr_tags[9].find_all('td')
            classification = td_tags[0].text.strip()
            height = td_tags[1].text.strip()
            weight = td_tags[2].text.strip()
            cap_rate = int(re.sub(r'\D', '', td_tags[3].text.strip()))
            base_egg_steps = int(re.sub(r'\D', '', td_tags[4].text.strip()))
        except ValueError:
            td_tags = tr_tags[10].find_all('td')
            classification = td_tags[0].text.strip()
            height = td_tags[1].text.strip()
            weight = td_tags[2].text.strip()
            cap_rate = int(re.sub(r'\D', '', td_tags[3].text.strip()))
            base_egg_steps = int(re.sub(r'\D', '', td_tags[4].text.strip()))

        # xp growth, base happiness, ev's earned, color, safari zone flee rate
        try:
            td_tags = tr_tags[11].find_all('td')
            xp_grow_pt, xp_grow_sp = td_tags[0].text.strip().split(" Points")
            xp_grow_pt = int(xp_grow_pt.replace(",", "")) # number has commas seperating hundreds, thousands, etc
            base_happiness = int(td_tags[1].text.strip())
            ev_earned = td_tags[2].text.strip()
            color = td_tags[3].text.strip()
            safari_flee = int(td_tags[4].text.strip())
        except ValueError:
            td_tags = tr_tags[12].find_all('td')
            xp_grow_pt, xp_grow_sp = td_tags[0].text.strip().split(" Points")
            xp_grow_pt = int(xp_grow_pt.replace(",", "")) # number has commas seperating hundreds, thousands, etc
            base_happiness = int(td_tags[1].text.strip())
            ev_earned = td_tags[2].text.strip()
            color = td_tags[3].text.strip()
            safari_flee = int(td_tags[4].text.strip())

        # wild hold items and egg groups
        dextables_index = dextables_index + 2 # skip over damage taken table
        tr_tags = ((BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr'))
        td_tags = tr_tags[1].find_all('td', class_='fooinfo')
        wild_hold_items = wild_hold_item_parse(td_tags[0].text.strip())
        egg_groups = []
        for tr_tag in td_tags[1].find('table').find_all('tr'):
            egg_groups.append(tr_tag.find_all('td')[1].find('a').text.strip())

        # evolutions
        dextables_index = dextables_index + 1
        td_tags = (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr')[1].find_all('td')[1:]
        evolutions = len(td_tags) # this should be either 1, 3, or 5 in length
        evolve_level, evolve_into, evolve_from = 0, 0, 0
        if evolutions == 5:
            pkmn_one = int(re.sub(r'\D', '', td_tags[0].find('a')['href'].split('/')[-1].split('.')[0].strip()))
            pkmn_two = int(re.sub(r'\D', '', td_tags[2].find('a')['href'].split('/')[-1].split('.')[0].strip()))
            pkmn_three = int(re.sub(r'\D', '', td_tags[4].find('a')['href'].split('/')[-1].split('.')[0].strip()))
            if dex_num == pkmn_one:
                try:
                    evolve_level = int(re.sub(r'\D', '', td_tags[1].find('img')['src'].split('/')[-1].split('.')[0].strip()))
                except ValueError:
                    evolve_level = td_tags[1].find('img')['src'].split('/')[-1].split('.')[0].strip()
                evolve_into = pkmn_two
                evolve_from = pkmn_one
            elif dex_num == pkmn_two:
                try:
                    evolve_level = int(re.sub(r'\D', '', td_tags[3].find('img')['src'].split('/')[-1].split('.')[0].strip()))
                except ValueError:
                    evolve_level = td_tags[3].find('img')['src'].split('/')[-1].split('.')[0].strip()
                evolve_into = pkmn_three
                evolve_from = pkmn_one
            else:
                evolve_level = 0
                evolve_into = pkmn_three
                evolve_from = pkmn_two
        elif evolutions == 3:
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
                evolve_level = 0
                evolve_into = pkmn_two
                evolve_from = pkmn_one
        else:
            evolve_level = 0
            evolve_into = pkmn_one
            evolve_from = pkmn_one
        
        # flavor text
        dextables_index = dextables_index + 1
        tr_tags = (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr')[1:]
        flavor_text = {}
        last_flavor = "No text"
        for tr_tag in tr_tags:
            td_tags = tr_tag.find_all('td')
            if len(td_tags) > 1:
                last_flavor = td_tags[1].text.strip()
                flavor_text[td_tags[0].text.strip()] = last_flavor
            else:
                flavor_text[td_tags[0].text.strip()] = last_flavor

        # locations
        dextables_index = dextables_index + 1
        tr_tags = (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr')[2:-1]
        locations = {}
        for tr_tag in tr_tags:
            td_tags = tr_tag.find_all('td')
            locations[td_tags[0].text.strip()] = td_tags[1].text.strip().split(", ")
        
        # moveset
        moveset = {}
        dextables_index = dextables_index + 1
        more_move_tables = not ("Stats" in (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find('tr').text)
        while(more_move_tables):
            tr_tags = (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr')
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
            more_move_tables = not ("Stats" in (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find('tr').text)

        entry = {
                "National Dex Number": dex_num,
                "Hoenn Dex Number": loc_num,
                "Name (english)": eng_name,
                "Name (japanese)": jap_name,
                "Male Ratio": mal_percent,
                "Female Ratio": fem_percent,
                "Type": typing,
                "Abilites": abilities,
                "Classification": classification,
                "Height": height,
                "Weight": weight,
                "Capture Rate": cap_rate,
                "Base Egg Steps": base_egg_steps,
                "XP Growth Speed": xp_grow_sp,
                "XP Growth Points": xp_grow_pt,
                "Base Happiness": base_happiness,
                "Effort Values Earned": ev_earned,
                "Color": color,
                "Safari Zone Flee Rate": safari_flee,
                "Wild Hold Items": wild_hold_items,
                "Egg Groups": egg_groups,
                "Evolves at level": evolve_level,
                "Evolves Into": evolve_into,
                "Evolves From": evolve_from,
                "Flavor Text": flavor_text,
                "Locations": locations,
                "Moveset": moveset
            }
            #TODO: base stats
        
        print("Download Complete!")

        return eng_name, entry
    else:
        print("Download Failed: A problem occurred with the requested page.")

        return None, None