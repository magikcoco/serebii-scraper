import requests
from bs4 import BeautifulSoup
import sys
import re
import time

print("Running: ", __file__)
print("In environment: ", sys.prefix)

pokemondict = {}

def request_page(url):
    """
    Grabs a URL and returns a Beuatiful Soup object that might be null
    """
    #time.sleep(5) # for avoiding a rate limit
    response = requests.get(url)
    print(f"Webpage response: {response.status_code}")
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html5lib') #magic parsing library do not touch
    else:
        #TODO: handle other errors
        return None

def wild_hold_item_parse(text):
    return_dict = {}
    pattern = r'([A-Z][a-z\s]+)*\s*-\s*([A-Z]+|\d+%|(([A-Z][a-z\s]+)*))(?=[A-Z][a-z]|$)' # monstrosity
    match = re.search(pattern, text)
    matches = []
    while(match is not None): # get all the matches
        match = match.group(0)
        text = text.replace(match, "")
        if match.startswith("Wild") and len(match) > 4 and match[4].isupper():
            match = match[4:]
        if match.startswith("Gen I Trade") and len(match) > len("Gen I Trade"):
            match = match[len("Gen I Trade"):]
        matches.append(match)
        match = re.search(pattern, text)
    for string in matches:
        key, value = string.split(" - ")
        return_dict[key] = value
    return return_dict

def gen_one_page(url):
    """
    handles grabbing info from generation 1 pages on serebii
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

        #add the completed entry to the generation dictionary
        gendict = pokemondict.setdefault("Gen 1",{})
        gendict[eng_name] = entry
        #print(gendict)
        print("Download Complete!")

def gen_two_page(url):
    """
    handles grabbing info from generation 2 pages on serebii
    """
    print(f"Now downloading: {url}")
    soup = request_page(url) # get the page to scrape
    if soup is not None: # check for null
        fooevos = soup.find_all('td', class_=['fooevo', 'foo', 'footwo']) # the labels for the values
        fooinfos = soup.find_all('td', class_=['fooinfo', 'cen']) # the values themselves

        # get names, number, class, height, weight, cap rate, xp growth, stats
        eng_name = "" # names in different languages
        jap_name = []
        fre_name = ""
        ger_name = ""
        kor_name = ""
        dex_num = 0 #national pokedex number
        joh_num = 0 #johto pokedex number
        mal_percent = 0.0 # the ratio of males
        fem_percent = 0.0 # the ratio of females
        classif = "" #the classification of the pokemon
        imp_height = "" # height and weight statistics in different units
        imp_weight = ""
        met_height = ""
        met_weight = ""
        cap_rate = 0 # the capture rate
        egg_steps = 0 # the base egg steps
        xp_grow_sp = "" # this is the speed of growth, like "Very Slow" or "Very Fast"
        xp_grow_pt = 0 # The growth points. I dont actually know wtf this one even means but its a number
        base_hap = 0 # the base happiness
        typing = [] # the type the pokemon is, may be multiple types
        base_stats = {} # the base stats for the pokemon
        moveset = {} # the moveset for this pokemon
        locations = {} # the locations for each game where this pokemon is found
        wild_hold_items = {} # the items this pokemon might hold naturally
        egg_groups = [] # the egg groups of this pokemon

        temp_list = [] # need to filter out the fooevo "Damage", because there is no corresponding fooinfo.
        for fooevo in fooevos: # doing it this way preserves the order of the list
            if "Damage" in fooevo.text:
                continue
            else:
                temp_list.append(fooevo)
        fooevos = temp_list

        # go over the information in tandem so the type of information is identifiable with fooevo
        for fooevo, fooinfo in zip(fooevos, fooinfos):
            if "Picture" in fooevo.text: # get the picture from bulbapedia instead, there is a game sprite section
                continue #skip this, and the fooinfo
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
                dex_nums = fooinfo.text.strip().split("#")
                valid_nums = []
                for num in dex_nums:
                    numeric = re.sub(r'\D', '', num) # strips out everything that would make parsing as int fail
                    try:
                        numeric = int(numeric) 
                        valid_nums.append(numeric)
                    except ValueError:
                        pass
                dex_num = valid_nums[0] # expect two numbers here
                joh_num = valid_nums[1]
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
                pattern = r'(\d+)\s*([A-Z][a-zA-Z]*(?:\s[A-Z][a-zA-Z]*)?)'
                matches = re.findall(pattern, fooinfo.text)
                # assign to appropriate value
                for number, label in matches:
                    base_stats[label] = int(number) #regex should catch multi-word-labels
            elif "Happiness" in fooevo.text:
                base_hap = int(fooinfo.text.strip()) #its just a number
            elif "Steps" in fooevo.text:
                egg_steps = int(fooinfo.text.strip().replace(",", "")) #its a number with commas
            elif "Groups" in fooevo.text:
                blocks = re.split(r'\s+', fooinfo.text.strip())
                pattern = r'[A-Z][a-z]*'
                egg_groups = [re.match(pattern, block).group() for block in blocks]
                if not egg_groups:
                    egg_groups.append("None")
            elif "Wild" in fooevo.text:
                pattern = r'([A-Z][a-z\s]+)*\s*-\s*([A-Z]+|\d+%|(([A-Z][a-z\s]+)*))(?=[A-Z][a-z]|$)' # monstrosity
                text = fooinfo.text.strip()
                match = re.search(pattern, text)
                matches = []
                while(match is not None): # get all the matches
                    match = match.group(0)
                    text = text.replace(match, "")
                    if match.startswith("Wild") and len(match) > 4 and match[4].isupper():
                        match = match[4:]
                    if match.startswith("Gen I Trade") and len(match) > len("Gen I Trade"):
                        match = match[len("Gen I Trade"):]
                    matches.append(match)
                    match = re.search(pattern, text)
                for string in matches:
                    key, value = string.split(" - ")
                    wild_hold_items[key] = value
            elif "Gender" in fooevo.text:
                pattern = r'([^%]+?)[%]' # we just want the percentage
                text = fooinfo.text.strip()
                match = re.search(pattern, text)
                matches = []
                while(match is not None):
                    match = match.group(0)
                    text = text.replace(match, "")
                    matches.append(match)
                    match = re.search(pattern, text)
                for string in matches:
                    key, value = string.split(":")
                    if "Male" in key:
                        mal_percent = float(value.replace("%", "").strip())
                    else:
                        fem_percent = float(value.replace("%", "").strip())
            else:
                print(f"Unrecognized information:\n{fooevo.text.strip()}:\n {fooinfo.text.strip()}\n\n")
            if "Groups" in fooevo.text:
                break # nothing past this is useful
        
        dextables = soup.find_all('table', class_='dextable')
        # Next get location information
        loc_dextable = dextables[6]
        loc_soup = BeautifulSoup(str(loc_dextable), 'html.parser')
        loc_tr_tags = loc_soup.find_all('tr')
        for tr_tag in loc_tr_tags:
            td_tags = tr_tag.find_all('td')
            for td_tag in td_tags:
                if 'class' in td_tag.attrs and any(cls in ['heartgold', 'soulsilver', 'crystal'] for cls in td_tag['class']):
                    next_td = td_tag.find_next(class_='fooinfo')
                    if next_td is not None:
                        locations[td_tag.text.strip()] = next_td.text.strip()
                    else:
                        locations[td_tag.text.strip()] = "Unknown"
                else:
                    continue
        
        # Next get the move list
        move_dextables = dextables[7:-1]
        for move_dextable in move_dextables:
            move_soup = BeautifulSoup(str(move_dextable), 'html.parser')
            table_name = move_soup.find('td', class_='fooevo')
            if table_name is not None:
                table_name = table_name.text
            else:
                continue
            if "Stats" in table_name:
                continue
            elif "Level" in table_name:
                tr_tags = move_soup.find_all('tr')
                for tr_tag in tr_tags[2::2]:
                    td_tags = tr_tag.find_all('td', class_='fooinfo')
                    level = td_tags[0].text.strip() # has the level information
                    name = td_tags[1].text.strip() # has the name
                    try:
                        level = int(level)
                    except ValueError:
                        level = 0
                    moveset.setdefault(name, []).append(level)
            else:
                value = -999 #TODO: record these in the readme
                if "TM" in table_name:
                    value = -1
                elif "Egg" in table_name:
                    value = -2
                elif "Crystal" in table_name:
                    value = -3
                elif "Gen I" in table_name:
                    value = -4
                else:
                    continue
                tr_tags = move_soup.find_all('tr')
                for tr_tag in tr_tags[2::2]:
                    td_tags = tr_tag.find_all('td', class_='fooinfo')
                    name = ""
                    if "Level" in table_name or "TM" in table_name:
                        name = td_tags[1].text.strip() # has the name
                    else:
                        name = td_tags[0].text.strip() # has the name
                    moveset.setdefault(name, []).append(value) # treat all levels like -1
        
        entry = {
            "National Dex Number": dex_num,
            "Johto Dex Number": joh_num,
            "Name (english)": eng_name,
            "Name (japanese)": jap_name,
            "Name (french)": fre_name,
            "Name (german)": ger_name,
            "Name (korean)": kor_name,
            "Male Ratio": mal_percent,
            "Female Ratio": fem_percent,
            "Type": typing,
            "Class": classif,
            "Height (Imperial)": imp_height,
            "Height (Metric)": met_height,
            "Weight (Imperial)": imp_weight,
            "Weight (Metric)": met_weight,
            "Capture Rate": cap_rate,
            "Base Egg Steps": egg_steps,
            "XP Growth Speed": xp_grow_sp,
            "XP Growth Points": xp_grow_pt,
            "Base Happiness": base_hap,
            "Base Stats": base_stats,
            "Wild Hold Items": wild_hold_items,
            "Egg Groups": egg_groups,
            "Locations": locations,
            "Moveset": moveset
        }
        #print(entry)
        
        #add the completed entry to the generation dictionary
        gendict = pokemondict.setdefault("Gen 2",{})
        gendict[eng_name] = entry
        #print(gendict)
        
        print("Download Complete!")

def gen_three_page(url):
    """
    handles grabbing info from generation 3 pages on serebii
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
        #print(entry)
        
        #add the completed entry to the generation dictionary
        gendict = pokemondict.setdefault("Gen 2",{})
        gendict[eng_name] = entry
        #print(gendict)
        
        print("Download Complete!")
        #exit()

def gen_four_page(url):
    """
    handles grabbing info from generation 4 pages on serebii
    """
    print(f"Now downloading: {url}")

def gen_five_page(url):
    """
    handles grabbing info from generation 5 pages on serebii
    """
    print(f"Now downloading: {url}")

def gen_six_page(url):
    """
    handles grabbing info from generation 6 pages on serebii
    """
    print(f"Now downloading: {url}")

def gen_seven_page(url):
    """
    handles grabbing info from generation 7 pages on serebii
    """
    print(f"Now downloading: {url}")

def gen_eight_page(url):
    """
    handles grabbing info from generation 8 pages on serebii
    """
    print(f"Now downloading: {url}")

def gen_nine_page(url):
    """
    handles grabbing info from generation 9 pages on serebii
    """
    print(f"Now downloading: {url}")

def gen_page(gen, url):
    """
    handles redirecting to the appropriate generation-specific function
    """
    # generation pages vary slightly in format so each generation is split into seperate functions
    # additionally if only one page is changed, not all of them break
    if gen == 1:
        #gen_one_page(url)
        print("Skipping gen 1...")
    elif gen == 2:
        #gen_two_page(url)
        print("Skipping gen 2...")
    elif gen == 3:
        gen_three_page(url)
        #print("Skipping gen 3...")
    elif gen == 4:
        #gen_four_page(url)
        print("Skipping gen 4...")
    elif gen == 5:
        #gen_five_page(url)
        print("Skipping gen 5...")
    elif gen == 6:
        #gen_six_page(url)
        print("Skipping gen 6...")
    elif gen == 7:
        #gen_seven_page(url)
        print("Skipping gen 7...")
    elif gen == 8:
        #gen_eight_page(url)
        print("Skipping gen 8...")
    elif gen == 9:
        #gen_nine_page(url)
        print("Skipping gen 9...")
    else:
        print(f"Unsupported generation: {gen}") # the last good one was 5, they should have never left using sprites

def pokemon_page(url):
    """
    grabs a table of links for each generation in which the target pokemon appears and calls pen_page on each one
    """
    print("Accessing: "+url)
    soup = request_page(url) # get the page and make sure its not None
    if soup is not None:
        #target_table_index = 2 # the table we want is the 2nd one of class dextab
        tables = soup.find_all('table', class_='dextab')
        for table in tables:
            if table.find('td', class_='pkmn'): # the target table contains td elements of class pkmn, which no other dextab table has
                links = table.find_all('a')
                total_links = len(links)
                for index, link in enumerate(links):
                    gen = total_links - index # they are listed in descending generation, so the first number should be the highest
                    gen_page(gen, "https://www.serebii.net"+link['href']) #call gen_page with the full url

def scrape_website(url):
    """
    scrape the serebii website for info
    """
    print(f"Accessing: {url}")
    soup = request_page(url)
    if soup is not None:
        table = soup.find('table') # find the table
        links = []
        for row in table.find_all('tr'): # iterate through table rows
            cells = row.find_all('td') # get all cells in row
            if len(cells) > 3: # check if there are at least 3 columns
                third_column = cells[3] # this is the cell with the target link
                link = third_column.find('a')
                if link and link.has_attr('href'):
                    links.append(link['href'])
                    pokemon_page("https://www.serebii.net"+link['href'])

start = time.time()
url = "https://www.serebii.net/pokemon/nationalpokedex.shtml" # this is currently the link to the national pokedex page on serebii
scrape_website(url)
end = time.time()
exec_time = end - start
print(f"\n\n\nExecution time: {exec_time} seconds")
