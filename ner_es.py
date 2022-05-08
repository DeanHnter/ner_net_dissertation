#Imports
from nltk.tokenize import MWETokenizer
import nltk
#from get_NER import ner

'''
Run NER in Spanish
'''
def ner_es(clean_docs):
  list_nes=[]
  
  for doc in clean_docs:
    try:
      nes= ner(doc)
      list_nes.append(nes)
    except:
      continue
  
  nes_es=[]
  for i in list_nes:
    for w in i:
      nes_es.append(w)
  return nes_es

'''
Obtains a list of nes without the rest of the info.
'''
def list_nes_es(nes_es):

  list_es=[]
  for ne in nes_es:
    if len(ne) != 0 and ne["word"] not in list_es:
      list_es.append(ne["word"])
  return list_es


'''
Preprocessing of docs in Spanish 

'''
def tok_es(clean_docs):
  #tokenized original article/sentece
  tokenized_sentence =[]
  for d in clean_docs:
    words= nltk.tokenize.word_tokenize(d)
    tokenized_sentence.append(words)
  return tokenized_sentence

def token_nes(list_es):
  tokenized_nes=[]
  #obtain the tokenized nes for latter adding to the mwe tokenizer
  for n in list_es:
    words= nltk.tokenize.word_tokenize(n)
    if len(words) <= 1:
      continue
    else:
      tokenized_nes.append(words)
  return tokenized_nes

def retoken_doc(tokenized_nes, tokenized_sentence):
  #create the instance of the MWETOKENIZER and add the ones that should be together
  tokenizer_mwe_es_x = MWETokenizer(tokenized_nes, separator=' ')
  #retokenizing
  retokenized_article=[]
  for d in tokenized_sentence:
    words = tokenizer_mwe_es_x.tokenize(d)
    retokenized_article.append(words)
  return retokenized_article

