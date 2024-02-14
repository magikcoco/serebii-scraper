import re
import requests
from bs4 import BeautifulSoup
import logging

start_timestamp = None

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

def setup_logger():
    global initial_timestamp

    if initial_timestamp is None:
        initial_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    logger = logging.getLogger('my_shared_logger')
    logger.setLevel(logging.DEBUG)

    log_filename = f'shared_log_{initial_timestamp}.log'

    # Create handlers
    file_handler = logging.FileHandler(log_filename, mode='a')
    console_handler = logging.StreamHandler()

    # Create formatters and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
