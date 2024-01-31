import requests
from bs4 import BeautifulSoup
import sys
import re

print("Running: ", __file__)
print("In environment: ", sys.prefix)

pokemondict = {}

def request_page(url):
    """
    Grabs a URL and returns a Beuatiful Soup object that might be null
    """
    response = requests.get(url)
    print(f"Webpage response: {response.status_code}")
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        return None

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
        base_stats = {}
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
            "Base Stats": base_stats
            #"Moveset": moveset
        }

        #add the completed entry to the generation dictionary
        gendict = pokemondict.setdefault("Gen 1",{})
        gendict[eng_name] = entry

        #print(gendict)
    
    #TODO: remove this
    exit(0) # exists so that I dont go through every pokemon when I want to test

    """

    # set the stats
    typing = [""]
    base_stats = {}
    moveset = {}
    
    # moveset
    # how to approach this??
    # array of integers, such that it is [level], [-1] (meaning tm/hm), [level, -1] meaning from level up AND tm/hm

    # fill base stat dict
    base_stats.set("Hit Points", hp)
    base_stats.set("Attack", atk)
    base_stats.set("Defense", dfn)
    base_stats.set("Special", sp)
    base_stats.set("Speed", spe)

    # create the dictionary for the pokemon
    entry = {
        "Dex Number": dex_num,
        "Name": name,
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
        "Moveset": moveset
    }

    # add to the dictionary
    gendict.set(name, entry)
    """

def gen_two_page(url):
    """
    handles grabbing info from generation 2 pages on serebii
    """
    print(f"Now downloading: {url}")

def gen_three_page(url):
    """
    handles grabbing info from generation 3 pages on serebii
    """
    print(f"Now downloading: {url}")

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
        gen_one_page(url)
    elif gen == 2:
        gen_two_page(url)
    elif gen == 3:
        gen_three_page(url)
    elif gen == 4:
        gen_two_page(url)
    elif gen == 5:
        gen_three_page(url)
    elif gen == 6:
        gen_two_page(url)
    elif gen == 7:
        gen_three_page(url)
    elif gen == 8:
        gen_two_page(url)
    elif gen == 9:
        gen_three_page(url)
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

url = "https://www.serebii.net/pokemon/nationalpokedex.shtml" # this is currently the link to the national pokedex page on serebii
scrape_website(url)
