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
        dextables_index = 0
        tr_tags = ((BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr'))
        ## These come in weird. Here are the indexes:
        ## 0: the label for pokemon game picture, national no. etc
        ## 1: the data under the above
        ## 2: a gif portrait
        ## 3: the row containing a fooinfo with the ability text
        ## 4: another picture
        ## 5: the explanation for the ability
        ## 6: a picture and the gender ratio label
        ## 7: another picture
        ## 8: the gender ratio information
        ## 9: labels for classification, types, etc
        ## 10: info for the above
        ## 11: evolution chain label
        ## 12: evolution chain info
        # national dex, local dex, english name, japanese name
        td_tags = tr_tags[1].find_all('td', class_='fooinfo')
        dex_num = int(re.sub(r'\D', '', td_tags[1].text.strip())) # strips out everything that would make parsing as int fail
        loc_num = int(re.sub(r'\D', '', td_tags[2].text.strip())) # strips out everything that would make parsing as int fail
        eng_name = td_tags[3].text.strip()
        jap_name = re.findall(r'[A-Za-z]+|[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+', td_tags[4].text.strip())
        # abilities
        td_tags = tr_tags[3].find_all('td', class_='fooinfo')
        abilities = td_tags[1].text.strip().split(": ")[1].split(" & ")
        # gender ratios
        try:
            td_tags = tr_tags[8].find_all('td', class_='fooinfo')
            mal_percent = float(re.sub(r'[^\d.]', '', td_tags[0].text.strip()))
            fem_percent = float(re.sub(r'[^\d.]', '', td_tags[1].text.strip()))
        except IndexError:
            td_tags = tr_tags[7].find_all('td', class_='fooinfo')
            mal_percent = float(re.sub(r'[^\d.]', '', td_tags[0].text.strip()))
            fem_percent = float(re.sub(r'[^\d.]', '', td_tags[1].text.strip()))
        # classification, type 1, type 2, height (imperial), weight (imperial)
        type1, type2 = [], []
        try:
            td_tags = tr_tags[10].find_all('td', class_='fooinfo')
            classif = td_tags[0].text.strip()
            type1 = BeautifulSoup(str(td_tags[1]), 'html.parser').find('a')['href'].split('/')[-1].split('.')[0]
            type2 = BeautifulSoup(str(td_tags[2]), 'html.parser').find('a')['href'].split('/')[-1].split('.')[0]
        except IndexError:
            td_tags = tr_tags[9].find_all('td', class_='fooinfo')
            classif = td_tags[0].text.strip()
            type1 = BeautifulSoup(str(td_tags[1]), 'html.parser').find('a')['href'].split('/')[-1].split('.')[0]
            type2 = BeautifulSoup(str(td_tags[2]), 'html.parser').find('a')['href'].split('/')[-1].split('.')[0]
        typing = [type1, type2]
        imp_height = td_tags[3].text.strip()
        imp_weight = td_tags[4].text.strip()
        # evolution data
        try:
            td_tags = tr_tags[12].find_all('td', class_='fooinfo')
        except IndexError:
            td_tags = tr_tags[11].find_all('td', class_='fooinfo')
        evolve_level = int(re.sub(r'\D', '', td_tags[0].text.strip().split(">")[0]))
        evole_into = int(re.sub(r'\D', '', BeautifulSoup(str(td_tags[0]), 'html.parser').find_all('a')[1]['href'].split('/')[-1].split('.')[0]))
        # Wild hold item, dex category, color category
        dextables_index = dextables_index + 1
        td_tags = (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr')[1].find_all('td')
        wild_hold_items = wild_hold_item_parse(td_tags[0].text.strip())
        dex_category = td_tags[1].find('a')['href'].split('/')[-1].split('.')[0]
        color_category = td_tags[2].text.strip()
        # Flavor text
        dextables_index = dextables_index + 2
        tr_tags = ((BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr'))
        flavors = {}
        for tr_tag in tr_tags[1:]:
            tds = tr_tag.find_all('td')
            flavors[tds[0].text.strip()] = tds[1].text.strip()
        # Locations
        dextables_index = dextables_index + 1
        tr_tags = ((BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr'))
        locations = {}
        for tr_tag in tr_tags[2:]:
            tds = tr_tag.find_all('td')
            locations[tds[0].text.strip()] = tds[1].text.strip().split(", ")
        # Level up moves for Ruby/Sapphire/Emerald/Colosseum/XD
        dextables_index = dextables_index + 1
        move_start_index = dextables_index
        more_move_tables = not ("Steps" in (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find('tr').text)
        labels = ["Ruby/Sapphire/Emerald/Colosseum/XD Level Up",
        "Fire Red/Leaf Green Level Up",
        "TM & HM",
        "Fire Red/Leaf Green/Emerald Move Tutor",
        "Emerald Move Tutor",
        "Egg Moves",
        "Special Attacks"]
        moveset = {}
        while(more_move_tables):
            tr_tags = ((BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr'))
            moves = {}
            for tr_tag in tr_tags[2::2]:
                tds = tr_tag.find_all('td')
                if not any(keyword in (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find('tr').text for keyword in ("Level", "TM")):
                    moves[tds[0].text.strip()] = 0
                else:
                    try:
                        moves[tds[1].text.strip()] = int(tds[0].text.strip())
                    except ValueError:
                        moves[tds[1].text.strip()] = 0
            moveset[labels[dextables_index-move_start_index]] = moves
            dextables_index = dextables_index + 1
            more_move_tables = not ("Steps" in (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find('tr').text)
        # Egg Steps, Effort Points gained, Catch rate
        # dextables will be incremented already by the loop prior
        td_tags = (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr')[1].find_all('td')
        egg_steps = int(re.sub(r'\D', '', td_tags[0].text.strip()))
        pts = td_tags[1].text.strip().split(", ")
        effort_points = {}
        for pt in pts:
            splitup = pt.split(": ")
            effort_points[splitup[0]] = int(re.sub(r'\D', '', splitup[1]))
        catch_rate = int(re.sub(r'\D', '', td_tags[2].text.strip()))
        # Egg groups
        dextables_index = dextables_index + 1
        tr_tags = (BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr')[2:]
        egg_groups = []
        for tr_tag in tr_tags:
            egg_groups.append(tr_tag.find_all('td')[1].text.strip())
        # Base stats
        dextables_index = dextables_index + 1
        tr_tags = ((BeautifulSoup(str(dextables[dextables_index]), 'html.parser')).find_all('tr'))
        labels = [td.text.strip() for td in tr_tags[1].find_all('td')[1:]]
        base_stats = {}
        for index, td_tag in enumerate(tr_tags[2].find_all('td', class_='cen')):
            base_stats[labels[index]] = int(td_tag.text.strip())


        entry = {
            "National Dex Number": dex_num,
            "Hoenn Dex Number": loc_num,
            "Name (english)": eng_name,
            "Name (japanese)": jap_name,
            "Abilities": abilities,
            "Male Ratio": mal_percent,
            "Female Ratio": fem_percent,
            "Class": classif,
            "Type": typing,
            "Height (Imperial)": imp_height,
            "Weight (Imperial)": imp_weight,
            "Evolve Level": evolve_level,
            "Evolves Into": evole_into,
            "Wild Hold Items": wild_hold_items,
            "Dex Category": dex_category,
            "Color Category": color_category,
            "Egg Groups": egg_groups,
            "Base Stats": base_stats,
            "Flavor Text": flavors,
            "Locations": locations,
            "Moveset": moveset
        }
        
        print("Download Complete!")

        return eng_name, entry
    else:
        print("Download Failed: A problem occurred with the requested page.")

        return None, None