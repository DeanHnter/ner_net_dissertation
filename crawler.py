#Imports

from bs4 import BeautifulSoup
from langdetect import detect
from bs4 import SoupStrainer
#from doc_retrieval import *

'''
Function to crawl and parse links obtained from previous function doc_retrieval()
Avoid 400 codes,
Accepts only UTF8
Performs language detection to ensure docs in spanish are found.
'''


def test_parse(general, requests_session):
  
  only_h1 = SoupStrainer(["title","h1","p"])
  
  list_of_docs=[]

  for url in general:
    if len(list_of_docs)<=10:
      try:
        data = requests_session.get(url, timeout=8)
      except:
        continue
      soup = BeautifulSoup(data.content, 'lxml', parse_only=only_h1)


      if soup.original_encoding != "utf-8":
        continue
      else:
        title_page= soup.find_all("title")
        titles = soup.find_all("h1")
        paragraphs= soup.find_all("p")
      temp_list=[]
      for n, t in enumerate(title_page):
        text= t.text
        temp_list.append(text)
      for n,t in enumerate(titles):
          text=t.text
          if text != " " and "406" not in text and "403" not in text and "Error" not in text and "Denied" not in text and "JavaScript" not in text:
              temp_list.append(text)
      for n,p in enumerate(paragraphs):
          text=p.text
          try:
            lang= detect(text)
          except:
            lang= "en"
            pass 
          if text != " " and lang == "es" and "cookies" not in text:
              if n < 4:
                temp_list.append(text)
      temp_list=" ".join(temp_list)
        
      if len(temp_list)>0: 
          list_of_docs.append(temp_list)
    else:
      break
  return list_of_docs


'''
Function that calls the above parsing function for each triplet, creates and returns a list with the parsed titles, and paragraphs
In case no website is allowed crawling or language detection from before does not find any document in Spanish,
if the len is 0 then it forces to restart by adding the words " español -dictionary -diccionario". It should look the NE by telling the search engine to look it up in spanish and avoid dictionaries.
'''

def get_parse_new(triplet, requests_session, new_links, ne):
  final=[]
    
  corpus= test_parse(new_links, requests_session)
  if len(corpus)>0:
    final = final + corpus
  elif len(corpus)==0:
    new_text= ne+" español -dictionary -diccionario"
    general = doc_retrieval(new_text, 10)
    corpus= test_parse(general, requests_session)
    if len(corpus)>0:
      final= final + corpus

  return final