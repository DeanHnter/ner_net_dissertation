#imports
from urllib.parse import urlencode, urlunparse
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import requests
from googlesearch import search
import urllib
from requests_html import HTML
from requests_html import HTMLSession

'''
Bing search Scraper.
Takes one query and get the links of the websites returned by bing search page.
'''

def scrape_bing(query):

  links_b=[]
  #query = "Flavina"
  url = urlunparse(("https", "www.bing.com", "/search", "", urlencode({"q": query}), ""))
  custom_user_agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0 Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
  try:
    req = Request(url, headers={"Accept-Language": "es-ES,es;q=0.9"} )#{"User-Agent": custom_user_agent}
    page = urlopen(req)
  except Exception as e:
    pass
  soup = BeautifulSoup(page.read(), "lxml")
  links = soup.find_all("a")
  for link in links:
    try:
      if link.get('href').startswith("http") and "microsoft" not in link.get('href') and link.get('href') not in links_b and "google" not in link.get('href') and "bing" not in link.get('href'):
        links_b.append(link.get("href"))
    except:
      yahoo= scrape_yahoo(query)
      if len(yahoo)>0:
        return yahoo
  return links_b

'''
Functions to search Google, takes a query and returns results returned by Google search
In case of failing, use Bing's or Yahoo's functions.

'''


def get_source(url):
    """Return the source code for the provided URL. 

    Args: 
        url (string): URL of the page to scrape.

    Returns:
        response (object): HTTP response object from requests_html. 
    """

    try:
        session = HTMLSession()
        response = session.get(url)
        return response

    except requests.exceptions.RequestException as e:
        print(e)

def scrape_google(query):
  try:

    query = urllib.parse.quote_plus(query)
    response = get_source("https://www.google.es/search?q=" + query+"&lr=lang_es&cr=countryES")

    links = list(response.html.absolute_links)


    google_domains = ('https://www.google.', 
                      'https://google.', 
                      'https://webcache.googleusercontent.', 
                      'http://webcache.googleusercontent.', 
                      'https://policies.google.',
                      'https://support.google.',
                      'https://maps.google.')
    wrong_sites= ( "twitter", "youtube", "facebook", "instagram")

    if len(links)!=0:
      for url in links[:]:
          if url.startswith(google_domains) or "twitter" in url or "youtube" in url or "facebook" in url or "instagram" in url or ".pdf" in url:
              links.remove(url)

      return links

    else: 
      bing= scrape_bing(query)

      links=bing
      return links
  except:
    yahoo= scrape_yahoo(query)

    links=yahoo
      
    
    return links

'''
Main option for Google search.
'''

def doc_retrieval(query, num_results):
  links_gen=[]
  try:
    
    links_gen=[]
    for result in search(query, num_results= num_results, lang="es"):
      
      if result.startswith( 'https' ):
        if "twitter" in result or "facebook" in result or "instagram" in result or "youtube" in result:
          continue
        else:
          links_gen.append(result)
            
      else:
        continue
  except :
    try:
      google= scrape_google(query)
      links_gen+= google
      
      
      
    except:
      bing= scrape_bing(query)
      links_gen+=bing
      
  return links_gen 


'''
Function to search the web using Yahoo search. 
Scraped the results page and saves the links.
'''

def scrape_yahoo(query):
  links=[]
  url = "http://es.search.yahoo.com/search?p=%s"
  custom_user_agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0 Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
  r = requests.get(url + "".join(query)) 
  soup = BeautifulSoup(r.text, "lxml")
  soup.find_all("a")

  for link in soup.find_all("a"):
    if link.get("href") != None:
      if "yahoo" not in link.get("href") and "youtube" not in link.get("href"):
        if link.get('href').startswith("http") and link.get('href') not in links and "bing" not in link.get('href'):
          links.append(link.get('href'))
  return links

'''
Function to get all the links at one.
Restricted it to 17 documents

'''

def get_links(tripletss):
  
  from tqdm import tqdm
  list_of_links=[]
  #for triplet in tripletss:
  for i in tqdm(range (len(tripletss)), desc="Loading…",ascii=False, ncols=75):
    for t in tripletss[i]:
      tempa=[]
      google= doc_retrieval(t, 4)
      bing= scrape_bing(t)
      if type(google) != None and type(bing) != None:
        all= google+bing
      elif type(google) == None:
        all= bing
      elif type(bing)== None:
        all= google
      if len(all)== 0:
        yahoo= scrape_yahoo(t)
        tempa+=yahoo
      else:
        tempa+=all
    list_of_links.append(tempa)

  new_links=[]
  for lista in list_of_links:
    tem=[]
    for item in lista:
      if item[-4:] == ".pdf" and item in tem:
        continue
      else:
        if len(tem)< 17:
          tem.append(item)
        else:
          continue
    new_links.append(tem)
  return new_links