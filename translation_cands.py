#imports
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from nltk.corpus import stopwords
import wikipediaapi, wikipedia, requests
from bs4 import BeautifulSoup
from save_thread_result import ThreadWithResult

stopWords = set(stopwords.words('english'))

#Set up the model and tokenizer for the NMT Seq2Seq:

tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-es")

model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-en-es")

translator= pipeline("translation_en_to_es", model= model, tokenizer=tokenizer)

# Translation candidates

#1. NMT 

def NMT_candidate(nes):
  result=[]
  for ne in nes:
    if ne[0] not in stopWords:
      translation= translator(ne[0])
      result.append(translation[0]["translation_text"])
  return result
'''
Dictionary mapping the tag and its translation for NMT query expansion
'''
dic_tags= {"Chemical": "Químico", "Protein": "Proteína", 
          "Sequence": "Proceso/Secuencia", "GENE": "Gen",
           "Cell": "Célula", "Taxon": "Taxón"}

'''
To use a Heuristic word with the second candidate (NMT) I add the translation of the NE tag and add it to the NMT candidate.
'''
def NMT_expansion(left_nes, dic_tags, nmt):
  list_fourth= []
  for i in range(len(left_nes)):
    for k,v in dic_tags.items():
      if left_nes[i][3] == k:
        list_fourth+= [nmt[i]+" " + v]
  return list_fourth

#nmt_expanded= NMT_expansion(left_nes, dic_tags,nmt)


#2.Context of NES 

'''
Create context wiht 10 chars left and 10 right
Getting the index of each ne and comparing it to the raw data 
to find the word and the +20 characters for context web sarch enad candidates
'''
def get_context(left_nes, nes_en, data):
  lista_candidates_cont=[]
  for ne in left_nes:

    if ne[0] not in data[ne[1]]:
      lista_candidates_cont.append(ne[0])
    elif ne[0] in data[ne[1]]:
                
      if ne[0] not in stopWords:
          
        start= nes_en[ne[1]][ne[2]]["start"]
        end=nes_en[ne[1]][ne[2]]["end"]
          
        if data[ne[1]][end-1] == ".":
          start= start-10
          while data[ne[1]][start-1] != " ":
            start=start-1            
            
          lista_candidates_cont.append(data[ne[1]][start:end])
        
          
        elif  data[ne[1]][end-1] != "." or data[ne[1]][end-1] != "," and end<len(data[ne[1]]):
          left= len(data[ne[1]])-end
          if left < 10:
            end=end+left
          else:
            end= end+5
          if start-5< 0:
            start=start
          else:
            start= start-10

          left_n= len(data[ne[1]])-end
            

          if left_n == 0 :

            lista_candidates_cont.append(data[ne[1]][start:end])
            continue
          else:
            while data[ne[1]][end-1] != " ":
              end=end+1
              if data[ne[1]][end-1] == "." or data[ne[1]][end-1] == ",":
                break
              if end==(len(data[ne[1]])):
                break
            while data[ne[1]][start] != " ":
              if start == 0:
                break
              start=start-1
                  
                
      
            lista_candidates_cont.append(data[ne[1]][start:end])
  return lista_candidates_cont

#context= get_context(left_nes, nes_en)

#translation of sentences with the context from before:

def NMT_candidate_sen(sents):
  result=[]
  for se in sents:
    translation= translator(se)
    result.append(translation[0]["translation_text"])
  return result


#3. Wikipedia

'''
Wikipedia seach for intralingual links and get anchor text, extract candidate from interlingual link.
'''
wiki_wiki = wikipediaapi.Wikipedia('en')

def wiki_extract(query):
    
    page = wiki_wiki.page(query)
    suma=page.summary
    title=page.title
    if "may refer to" not in page.summary:
        r= requests.get("https://en.wikipedia.org/wiki/"+title)
        soup = BeautifulSoup(r.content, 'html.parser')
        s= soup.find('div', id="mw-navigation")
        panel= s.find("div", id="mw-panel")
        nav= panel.find("nav", id="p-lang")
        leftbar = nav.find('ul', class_='vector-menu-content-list')
        try:
            lines = leftbar.find('li', class_="interwiki-es")
            links= lines.find_all("a")
            for line in links:
                new_url= line.get('href')
            return line.get("title")[:-10]
        except:
             return title
    elif "may refer to" in page.summary:
        return page.title

'''
Use previous function to produce a candidate for each of the NES.
'''
def wiki_cands(left_nes):
  list_candidates_wiki=[]
  for ne in left_nes:
    if ne[0] not in stopWords:
      word= wiki_extract(ne[0])

      if word != " ":
        list_candidates_wiki.append(word)
      elif word == " ":
        list_candidates_wiki.append(ne[0])
  return list_candidates_wiki


#Threading to obtain all above data

'''
Use of Thread to speed up the process of obtaining the three candidates

'''
def thread_cands(left_nes, context):
  thread1 = ThreadWithResult(target=NMT_candidate, args=(left_nes,))
  thread2 = ThreadWithResult(target=NMT_candidate_sen, args=(context,))
  thread3 = ThreadWithResult(target=wiki_cands, args=(left_nes,))

  thread1.start()
  thread2.start()
  thread3.start()
  thread1.join()
  thread2.join()
  thread3.join()


  nmt = thread1.result
  context_sens = thread2.result
  wiki_first= thread3.result
  return nmt, context_sens, wiki_first

'''
Function to zip the three candidates into a list for each NE.
It will be use later for web search, and document extraction.
'''
def trio_cand(wiki, nmt_expanded, context ):
  trio_candidates=[]
  for a,b,c in zip(wiki, nmt_expanded, context):
    trio_candidates.append([a,b,c])
  return trio_candidates

#triplets= trio_cand(wiki_first, nmt_expanded, context_sens)