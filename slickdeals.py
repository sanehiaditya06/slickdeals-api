from typing import Text
import requests
from bs4 import BeautifulSoup
import logging
import dotenv
import datetime
import json
import time
import urllib3
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, HardwareType
from fp.fp import FreeProxy

logging.basicConfig(filename='vnv.log', filemode='a', format='%(asctime)s - %(name)s - %(message)s',
                    level=logging.DEBUG)

software_names = [SoftwareName.CHROME.value]
hardware_type = [HardwareType.MOBILE__PHONE]
user_agent_rotator = UserAgent(software_names=software_names, hardware_type=hardware_type)
CONFIG = dotenv.dotenv_values()



INSTOCK = []


def scrape_main_site(headers):
    """
    Scrape the site and adds each item to an array
    :return:
    """
    items = []
    url = 'https://slickdeals.net/deals/'
    s = requests.Session()
    html = s.get(url=url, headers=headers, verify=False, timeout=15)
    soup = BeautifulSoup(html.text, 'html.parser')
    products = soup.find_all('div',  {'class': 'box onPopularDeals'})
    print(products)
    for product in products:
        item = [product.find('img', {'class': 'dealImage'})['title'],
                product.find('span', {'class': 'priceShippingTruncate popularDeal'}).text,
                product.find('a', {'class': 'dealTitle'})['href'],
                product.find('img', {'class': 'dealImage'})['src']]
        items.append(item)
    return items


def discord_webhook(product_item):
    """
    Sends a Discord webhook notification to the specified webhook URL
    :param product_item: An array of the product's details
    :return: None
    """
   # product_image = product_item[2][product_item[2].rfind('/')+1:product_item[2].rfind('.html')]
    data = {}
    data["embeds"] = []
    embed = {}
    if product_item == 'initial':
        embed["title"] = "Cache Cleared"
        embed["author"]= {'name': 'slickdeals.com','url': 'https://slickdeals.net/deals/', 'icon_url': 'https://i.imgur.com/ZdGihMp.png'}
        embed["color"] = int(CONFIG['COLOUR'])
        embed["timestamp"] = str(datetime.datetime.utcnow())
        data["embeds"].append(embed)

        result = requests.post("https://discord.com/api/webhooks/872167233068077126/92V_fo9FeFaAOttd8_N5Jg562VJdUbcHYNpYdNDu50fXl87s-8QgaYIg01ESqCqJUKTt", data=json.dumps(data), headers={"Content-Type": "application/json"})
    else:
        embed["title"] = product_item[0]  # Item Name
        embed['url'] = f"https://slickdeals.net{product_item[2]}"  # Item link
        embed["thumbnail"] = {'url': product_item[3]}  # Item image
        embed["fields"]= [{'name': 'Price and Store: ', 'value': product_item[1].replace("\n"," "), 'inline' : False},
        #{'name': 'Rating: ', 'value': product_item[3], 'inline': False},
        {'name':'Quick Links: ', 'value': '[Popular](https://slickdeals.net/deals/)' + ' | ' + '[Deal Categories](https://slickdeals.net/deal-categories/)', 'inline': True}]
        embed["author"]= {'name': 'slickdeals.com','url': 'https://slickdeals.net/deals/', 'icon_url': 'https://i.imgur.com/ZdGihMp.png'}
        embed["color"] = int(CONFIG['COLOUR'])
        embed["footer"] = {'text': 'Price Deals | HeavyDrop Profits','icon_url': 'https://i.imgur.com/NeJAV1h.jpg'}
        embed["timestamp"] = str(datetime.datetime.utcnow())
        data["embeds"].append(embed)

        result = requests.post(CONFIG['WEBHOOK'], data=json.dumps(data), headers={"Content-Type": "application/json"})

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        logging.error(msg=err)
    else:
        print("Payload delivered successfully, code {}.".format(result.status_code))
        logging.info("Payload delivered successfully, code {}.".format(result.status_code))


def checker(item):
    """
    Determines whether the product status has changed
    :param item: list of item details
    :return: Boolean whether the status has changed or not
    """
    for product in INSTOCK:
        if product == item:
            return True
    return False


def remove_duplicates(mylist):
    """
    Removes duplicate values from a list
    :param mylist: list
    :return: list
    """
    return [list(t) for t in set(tuple(element) for element in mylist)]


def comparitor(item, start):
    if not checker(item):
        INSTOCK.append(item)
        if start == 0:
            discord_webhook(item)


def monitor():
    """
    Initiates monitor
    :return:
    """
    print('STARTING MONITOR')
    logging.info(msg='Successfully started monitor')
    discord_webhook('initial')
    start = 0


    headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}
    keywords = CONFIG['KEYWORDS'].split('%')
    i = 0
    print('Initial Listing Load Complete, checking for changes in future cycles.')
    while True:
        i = i + 1
        print(f'[{datetime.datetime.utcnow()}] - Cycle #{i} Complete')
        try:
            items = remove_duplicates(scrape_main_site(headers))
            for item in items:
                check = False
                if keywords == '':
                    comparitor(item, start)
                else:
                    for key in keywords:
                        if key.lower() in item[0].lower():
                            check = True
                            break
                    if check:
                        comparitor(item, start)
            time.sleep(float(CONFIG['DELAY']))
            start = 0
        except Exception as e:
            print(f"Exception found '{e}' - Rotating proxy and user-agent")
            logging.error(e)
            headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}


if __name__ == '__main__':
    urllib3.disable_warnings()
    monitor()
