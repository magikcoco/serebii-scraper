from helperfunctions import request_page, wild_hold_item_parse
from bs4 import BeautifulSoup
import re

def scrape_page(url):
    """
    handles grabbing info from generation 1 pages on serebii
    expects a url to a gen1 pokedex page for a specific pokemon on serebii
    returns a string of the english name for the pokemon, and a dictionary containing the info for that pokemon which was scraped from the page
    if request_page from helperfunctions returns None, then this will return None, None
    """
    print(f"Now downloading: {url}")
    soup = request_page(url) # get the page to scrape
    if soup is not None: # check for null
        fooevos = soup.find_all('td', class_=['fooevo', 'foo']) # the labels for the values
        fooinfos = soup.find_all('td', class_=['fooinfo', 'cen']) # the values themselves

        # get names, number, class, height, weight, cap rate, xp growth, stats
        eng_name = "" # names in different languages
        jap_name = []
        fre_name = ""
        ger_name = ""
        kor_name = ""
        dex_num = 0 #national pokedex number
        classif = "" #the classification of the pokemon
        imp_height = "" # height and weight statistics in different units
        imp_weight = ""
        met_height = ""
        met_weight = ""
        cap_rate = 0 # the capture rate
        xp_grow_sp = "" # this is the speed of growth, like "Very Slow" or "Very Fast"
        xp_grow_pt = 0 # The growth points. I dont actually know wtf this one even means but its a number
        typing = [] # the type the pokemon is, may be multiple types
        base_stats = {} # the base stats for the pokemon
        moveset = {} # the moveset for this pokemon
        locations = {} # the locations for each game where this pokemon is found

        # go over the information in tandem so the type of information is identifiable with fooevo
        for fooevo, fooinfo in zip(fooevos, fooinfos):
            if "Picture" in fooevo.text: # get the picture from bulbapedia instead, there is a game sprite section
                continue #skip this
            elif "Type" in fooevo.text: # these ones dont come up as text
                more_soup = BeautifulSoup(str(fooinfo), 'html.parser') # parse the html content again
                a_tags = more_soup.find_all('a') # get the a tags for their href values
                for tag in a_tags:
                    href = tag.get('href')
                    if href:
                        # need the word in the url
                        typ = href.split('/')[-1].split('.')[0] # the last word in /example/type.shtml is the target
                        typing.append(typ)
            elif "Names" in fooevo.text: # these are the other names category but we need to match it before the english name due to the similar labels
                o_rows = fooinfo.text.strip().split("\n") #the names are newlines as Language: Name, except for japanese which has two diff writings
                for o_row in o_rows:
                    if "Japan" in o_row:
                        pattern = r'[A-Za-z]+|[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+'
                        jap_name = re.findall(pattern, o_row.split(": ")[1]) # splits by latin and japanese characters
                    elif "French" in o_row:
                        fre_name = o_row.split(":")[1].strip() # in latin char
                    elif "German" in o_row:
                        ger_name = o_row.split(":")[1].strip() # in latin char
                    else: # korean is the last one listed
                        kor_name = o_row.split(":")[1].strip() # in latin char
            elif "Name" in fooevo.text: # this is the english name
                eng_name = fooinfo.text.strip()
            elif "No." in fooevo.text: # this is the pokedex number
                numeric = re.sub(r'\D', '', fooinfo.text.strip()) # strips out everything that would make parsing as int fail
                dex_num = int(numeric)
            elif "Classif" in fooevo.text: # the classification, Ex. "Seed pokemon", "Turtle pokemon", "Dumbass 3D Sprite using pokemon"
                classif = fooinfo.text.strip()
            elif "Height" in fooevo.text: # the height stats
                imp_height, met_height = re.split(r'[\s\r\n\t]+', fooinfo.text.strip())
                imp_height, met_height = imp_height.strip(), met_height.strip()
            elif "Weight" in fooevo.text: # weight stats
                imp_weight, met_weight = re.split(r'[\s\r\n\t]+', fooinfo.text.strip())
                imp_weight, met_weight = imp_weight.strip(), met_weight.strip()
            elif "Capture" in fooevo.text: # capture rate
                cap_rate = int(fooinfo.text.strip())
            elif "Exp" in fooevo.text: # growth stats
                xp_grow_pt, xp_grow_sp = fooinfo.text.strip().split(" Points")
                xp_grow_pt = int(xp_grow_pt.replace(",", "")) # number has commas seperating hundreds, thousands, etc
            elif "Effort" in fooevo.text:
                # pattern to match out the ambiguously seperated values
                pattern = r'(\d+)\s*([A-Z][a-zA-Z]*)'
                matches = re.findall(pattern, fooinfo.text)
                # assign to appropriate value
                for number, label in matches:
                    if label == 'Hit':
                        base_stats["Hit Points"] = int(number) # otherwise it is added as key 'Hit' instead
                    else:
                        base_stats[label] = int(number)
            else:
                print(f"Unrecognized information:\n{fooevo.text.strip()}:\n {fooinfo.text.strip()}\n\n")
            if "Effort" in fooevo.text:
                break # nothing past this is useful
        
        dextables = soup.find_all('table', class_='dextable')
        # Next get location information
        loc_dextable = dextables[5]
        loc_soup = BeautifulSoup(str(loc_dextable), 'html.parser')
        loc_tr_tags = loc_soup.find_all('tr')
        for tr_tag in loc_tr_tags:
            td_tags = tr_tag.find_all('td')
            for td_tag in td_tags:
                if 'class' in td_tag.attrs and any(cls in ['firered', 'leafgreen', 'sapphire', 'yellow'] for cls in td_tag['class']):
                    next_td = td_tag.find_next(class_='fooinfo')
                    if next_td is not None:
                        locations[td_tag.text.strip()] = next_td.text.strip()
                    else:
                        locations[td_tag.text.strip()] = "Unknown"
                else:
                    continue
        
        # Next get the move list
        lvl_up_dextable = dextables[6] # the moves gained from level up
        tm_hm_dextable = dextables[7] # the moves gained by tm or hm
        # move information is beyond the scope, to be stored in a separate movelist section.
        # only need level data. tm or hm implicitly part of move data.
        # Moves by level up table
        # starting from the 3rd <tr>, get every other <tr> and take the first two <td> elements
        lvl_soup = BeautifulSoup(str(lvl_up_dextable), 'html.parser')
        lvl_tr_tags = lvl_soup.find_all('tr')
        for tr_tag in lvl_tr_tags[2::2]:
            td_tags = tr_tag.find_all('td', class_='fooinfo')
            level = td_tags[0].text.strip() # has the level information
            name = td_tags[1].text.strip() # has the name
            try:
                level = int(level)
            except ValueError:
                level = 0
            moveset.setdefault(name, []).append(level)
        #moves from tm/hm, level set as -1. in some cases a move might be on both lists, the leveled number comes first
        tm_hm_soup = BeautifulSoup(str(tm_hm_dextable), 'html.parser')
        tm_hm_tr_tags = tm_hm_soup.find_all('tr')
        for tr_tag in tm_hm_tr_tags[2::2]:
            td_tags = tr_tag.find_all('td', class_='fooinfo') 
            name = td_tags[1].text.strip() # has the name
            moveset.setdefault(name, []).append(-1) # treat all levels like -1

        entry = {
            "Dex Number": dex_num,
            "Name (english)": eng_name,
            "Name (japanese)": jap_name,
            "Name (french)": fre_name,
            "Name (german)": ger_name,
            "Name (korean)": kor_name,
            "Type": typing,
            "Class": classif,
            "Height (Imperial)": imp_height,
            "Height (Metric)": met_height,
            "Weight (Imperial)": imp_weight,
            "Weight (Metric)": met_weight,
            "Capture Rate": cap_rate,
            "XP Growth Speed": xp_grow_sp,
            "XP Growth Points": xp_grow_pt,
            "Base Stats": base_stats,
            "Locations": locations,
            "Moveset": moveset
        }

        print("Download Complete!")

        return eng_name, entry
    else:
        print("Download Failed: A problem occurred with the requested page.")

        return None, None