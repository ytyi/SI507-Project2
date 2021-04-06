#################################
##### Name: Yang Tianyi
##### Uniqname: jackyty
#################################

from bs4 import BeautifulSoup
import requests
import json
from secrets import API_KEY
import sys
import secrets # file that contains your API key

BASE_URL = 'https://www.nps.gov'
CACHE_FILE_NAME = 'SI507_Project2.json'

def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

CACHE_DICT = load_cache()
def make_url_request_using_cache(url, cache,params='none'):
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        response = requests.get(url,params=params)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone=None):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone
    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    state_url_dict={}
    response = make_url_request_using_cache('https://www.nps.gov/index.htm',CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    state_listing_parent = soup.find('ul', class_='dropdown-menu SearchBar-keywordSearch')
    state_listing_uls = state_listing_parent.find_all('li',recursive=False)
    for state_listing_ul in state_listing_uls:
        state_url_dict[state_listing_ul.text.strip().lower()]=BASE_URL+state_listing_ul.find('a')['href']
    return state_url_dict

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    response = make_url_request_using_cache(site_url,CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    site_div = soup.find('div', class_='Hero-titleContainer clearfix')
    site_names = site_div.find_all('a', recursive=False)
    name=site_names[0].text.strip()
    site_category_parent=soup.find('div',class_='Hero-designationContainer')
    site_categorys=site_category_parent.find_all('span',recursive=False)
    category=site_categorys[0].text.strip()
    address = soup.find('span', itemprop='addressLocality').text.strip()+', '+soup.find('span', itemprop='addressRegion').text.strip()
    zipcode=soup.find('span', itemprop='postalCode').text.strip()
    phone = soup.find('span', itemprop='telephone').text.strip()
    site_instance = NationalSite(category, name, address, zipcode,phone)
    return site_instance




def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    list_return=[]
    response = make_url_request_using_cache(state_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    list_parks=soup.find('ul',id='list_parks')
    park_list=list_parks.find_all('li',recursive=False)
    for park in park_list:
        park_url=BASE_URL+park.find('div').find('h3').find('a')['href']+'index.htm'
        site_wanted=get_site_instance(park_url)
        list_return.append(site_wanted)
    return list_return



def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    baseurl = 'http://www.mapquestapi.com/search/v2/radius?'
    params = {
        "key": API_KEY,
        "origin": site_object.zipcode,
        "radius": 10,
        "maxMatches": 10,
        "ambiguities": "ignore",
        "outFormat": "json"
    }
    response= make_url_request_using_cache(baseurl,CACHE_DICT,params)
    return json.loads(response)


def show_nearby_places(site_object):
    '''
    print the nearby places
    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    None
    '''
    print("---------------")
    print(f"Places near {site_object.name}")
    print("---------------")
    places_near = get_nearby_places(site_object)["searchResults"]
    for place in places_near:
        place = place['fields']
        name = place['name']
        if place['group_sic_code_name_ext'] == '':
            category = "no category"
        else:
            category = place['group_sic_code_name_ext']
        if place['address'] == '':
            street_address = "no address"
        else:
            street_address = place['address']
        if place['city'] == '':
            city_name = "no city"
        else:
            city_name = place['city']
        return_str = f"- {name} ({category}): {street_address}, {city_name}"
        print(return_str)

def show_state_site(state,state_dict):
    '''
    print the list of national sites in state
    Parameters
    ----------
    site: str
        a string of a state
    state_dict: dict
        a dict contains states and corressponding url

    Returns
    -------
    None
    '''
    if state.lower() in state_dict.keys():
        site_list = get_sites_for_state(state_dict[state.lower()])
        print("-------------------")
        print(f"List of national sites in {state}")
        print("-------------------")
        for index, site in enumerate(site_list):
            print(f"[{index + 1}] {site.info()}")
        return site_list
    else:
        print("[Error] Enter proper state name")
        return -1


if __name__ == "__main__":

    state_dict = build_state_url_dict()
    while True:
        state = input('Enter a State name (e.g., Michigan, michigan) or "exit":  ')
        if state.lower=='exit':
            break
        else:
            site_list=show_state_site(state,state_dict)
            if site_list!=-1:
                while True:
                    num_input = input('Choose the number for detail search or enter "exit" or "back": ')
                    if num_input.lower() == 'exit':
                        sys.exit(0)
                    elif num_input.lower() == 'back':
                        break
                    else:
                        try:
                            num = int(num_input)
                            if 1 <= num <= len(site_list):
                                show_nearby_places(site_list[num - 1])
                            else:
                                print("[Error] Invalid input")
                        except ValueError:
                            print("[Error] Invalid input")





