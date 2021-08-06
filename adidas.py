import requests
from bs4 import BeautifulSoup
import logging
import dotenv
import datetime
import json
import time
from requests.models import Response
import urllib3
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, HardwareType
from fp.fp import FreeProxy
import urllib.request

logging.basicConfig(filename='test.log', filemode='a', format='%(asctime)s - %(name)s - %(message)s',
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
    request = urllib.request.Request("https://shop.adidas.co.in/gateway/catalog/api/product/ADIDAS_IN?q=%22YEEZY%22~15&fields=activeStartDate_dt&fields=priority_l&skip=0&limit=60&filterQuery=(outOfStock_b:false%20OR%20(outOfStock_b:true%20AND%20displayType_i:1))&sortFields=sub(priority_l,0):desc;floor(div(sub(1626615549497,activeStartDate_dt),2592000000)):asc;sub(maxPrice_d,facetPrice_d):asc;activeStartDate_dt:desc&sortFields=sub(priority_l,0):desc;floor(div(sub(1626615549497,activeStartDate_dt),2592000000)):asc;sub(maxPrice_d,facetPrice_d):asc;activeStartDate_dt:desc&sourceCode=0&y3=0&_=1626615547202", headers=headers)
    r = urllib.request.urlopen(request).read()
    json_data = json.loads(r)
    if json_data["numFound"] != 0:
        particular = json_data["data"]  
        for product in particular:
            item = [product["productId"],
                    product["urlKey"],
                    product["facetPrice"],
                    product["content"]["defaultAsset"]["publishedURL"],
                    product["content"]["text"]["name"]]
            inventory = []
            for size in product["productListingInStockDtos"]:
                inventory.append(f'{size["attributeValue"]}')
            inventoryStr = '\n'.join([str(elem) for elem in inventory])
            item.append(inventoryStr)                
            items.append(item)
    return items


def discord_webhook(product_item):
    """
    Sends a Discord webhook notification to the specified webhook URL
    :param product_item: An array of the product's details
    :return: None
    """

    data = {}
    data["embeds"] = []
    embed = {}
    if product_item == 'initial':
        embed["title"] = "Cache Cleared."
        embed["color"] = 9314558
        embed["author"] = {'name': 'shop.adidas.co.in', 'icon_url':'https://i.imgur.com/vSESfae.jpg', 'url':'https://shop.adidas.co.in'}
        embed["timestamp"] = str(datetime.datetime.utcnow())
        data["embeds"].append(embed)
        result = requests.post("https://discord.com/api/webhooks/872167233068077126/92V_fo9FeFaAOttd8_N5Jg562VJdUbcHYNpYdNDu50fXl87s-8QgaYIg01ESqCqJUKTt", data=json.dumps(data), headers={"Content-Type": "application/json"})
    else:
        embed["title"] = product_item[4]  # Item 
        embed['url'] = f'https://shop.adidas.co.in/#!product/{product_item[1]}'  # Item link
        embed['thumbnail'] = {'url': f'https://content.adidas.co.in{product_item[3]}'} #Item Image
        embed["color"] = int(CONFIG['COLOUR'])
        embed['fields'] = [{'name': 'SKU:', 'value': product_item[0], 'inline': True},
        {'name': 'Price: ', 'value': f"₹{product_item[2]}", 'inline': True},
        {'name': 'Sizes: ', 'value': product_item[5]},
        {'name': 'Quick Links: ', 'value': '[Query](https://shop.adidas.co.in/#search/Pag-60/No-0/0/All/YEEZY)' + ' | ' + '[DEV](https://www.instagram.com/adityasanehi/)', 'inline' : False}]
        embed["footer"] = {'text': 'Adidas v1 | HeavyDrop Profits', 'icon_url' : 'https://i.imgur.com/vSESfae.jpg'}
        embed["author"] = {'name': 'shop.adidas.co.in', 'icon_url':'https://i.imgur.com/vSESfae.jpg', 'url':'https://shop.adidas.co.in'}
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
    start = 1

    headers = {'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Mobile Safari/537.36',
              'accept-encoding': 'gzip, deflate, br',
              'accept':	'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
              'authority': 'shop.adidas.co.in',
              'upgrade-insecure-requests': 1,
              'accept-language': 'en-US,en;q=0.9',
              'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
              'sec-ch-ua-mobile': '?1',
              'sec-fetch-dest': 'document',
              'sec-fetch-mode': 'navigate',
              'sec-fetch-site': 'none',
              'sec-fetch-user': '?1',
              'scheme': 'https',
              'cache-control': 'max-age=1',
              'path' : '/gateway/catalog/api/product/ADIDAS_IN?q=%22YEEZY%22~15&fields=activeStartDate_dt&fields=priority_l&skip=0&limit=60&filterQuery=(outOfStock_b:false%20OR%20(outOfStock_b:true%20AND%20displayType_i:1))&sortFields=sub(priority_l%2C0)%3Adesc%3Bfloor(div(sub(1626615549497,activeStartDate_dt),2592000000))%3Aasc%3Bsub(maxPrice_d%2CfacetPrice_d)%3Aasc%3BactiveStartDate_dt%3Adesc&sortFields=sub(priority_l%2C0)%3Adesc%3Bfloor(div(sub(1626615549497,activeStartDate_dt),2592000000))%3Aasc%3Bsub(maxPrice_d%2CfacetPrice_d)%3Aasc%3BactiveStartDate_dt%3Adesc&sourceCode=0&y3=0&_=1626615547202'
              #'Cookie' : 'AWSALBAPP-0=_remove_; AWSALBAPP-1=_remove_; AWSALBAPP-2=_remove_; AWSALBAPP-3=_remove_; BNI_persistence=VzhPPZLZLmUSnOgHz5qfH5DpBHL8rt1u-TQItzif5hDQP70tmMHi7GMo8UmGxNcS4aHIo3RrDvlv5OwpO1RvCA==; JSESSIONID=3267A085715795FCD6C4E77F4A3C2E2B; trkId=nAjqkTcgvfoxQmgmajbc; BNES_JSESSIONID=ulpBdz24oZCj8mDr5UXDiDQpeHYJSkLBvcx7Ads2ge9qtnUsRA3dSi+EAZPBiy9u8NPfOhdyms7vslC3drs90ri2SNfAAMEL; BNES_trkId=WtbAsfVSu+xTugbuSZZO18mTfSdLmBKMGZDfJt/jQJftIJoHjVjI/vP1dPfhdKvoERrlOcDp6mQ=; BNES_AWSALBAPP-0=GvqZAtj00Y2FE6V9U7r+ALmAtGFc93bBikVqhF/fUsdYtwrs25JObLABHYPAdfsk; BNES_AWSALBAPP-1=uT8Bhn8UsPNCsWLtDh9Oztj7E5ZSfguz8BBWz9eqd+cvSh/NvSwAXluWMcgFPdmv; BNES_AWSALBAPP-2=k8D2HQkmuGLG5g+tdpFb+35i8Fu+ICA2dUQXSlr7IwnlFpJEXwnAzAnbCWTu5ZgA; BNES_AWSALBAPP-3=fawDk+EzZUtpX9uZv6Gt1iSEgXSHkbS7jQ1KniOexltKoaPPaM7QM/D3lWNI78qr'
              }
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
            headers = {
              'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Mobile Safari/537.36',
              'accept-encoding': 'gzip, deflate, br',
              'accept':	'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
              'authority': 'shop.adidas.co.in',
              'upgrade-insecure-requests': 1,
              'accept-language': 'en-US,en;q=0.9',
              'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
              'sec-ch-ua-mobile': '?1',
              'sec-fetch-dest': 'document',
              'sec-fetch-mode': 'navigate',
              'sec-fetch-site': 'none',
              'sec-fetch-user': '?1',
              'scheme': 'https',
              'cache-control': 'max-age=1',
              'path' : '/gateway/catalog/api/product/ADIDAS_IN?q=%22YEEZY%22~15&fields=activeStartDate_dt&fields=priority_l&skip=0&limit=60&filterQuery=(outOfStock_b:false%20OR%20(outOfStock_b:true%20AND%20displayType_i:1))&sortFields=sub(priority_l%2C0)%3Adesc%3Bfloor(div(sub(1626615549497,activeStartDate_dt),2592000000))%3Aasc%3Bsub(maxPrice_d%2CfacetPrice_d)%3Aasc%3BactiveStartDate_dt%3Adesc&sortFields=sub(priority_l%2C0)%3Adesc%3Bfloor(div(sub(1626615549497,activeStartDate_dt),2592000000))%3Aasc%3Bsub(maxPrice_d%2CfacetPrice_d)%3Aasc%3BactiveStartDate_dt%3Adesc&sourceCode=0&y3=0&_=1626615547202'
            }


if __name__ == '__main__':
    urllib3.disable_warnings()
    monitor()
