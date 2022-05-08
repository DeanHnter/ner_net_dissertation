#Imports
from simalign import SentenceAligner
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer,CountVectorizer
from scipy.sparse import hstack
from save_thread_result import ThreadWithResult
import os
from information_retri import *

'''
Candidate number 0.
Unigram aligment using Simalign
Function to get aligments from the documents, get the words aligned and score the options. Candidates get from this can only be one word entities.
Feed the retokenized_article
'''


myaligner = SentenceAligner(model="bert", token_type="bpe", matching_methods="mai")

def align_cand(ne, tokenized_docs):

  new_retok= []
  for t in tokenized_docs:
    new_retok+=t
  
  alignments = myaligner.get_word_aligns(ne, new_retok)


  saved_align=[]
  saved_align+=alignments["mwmf"]

  align_candi= []
  for i,s in enumerate(saved_align):
    cands= new_retok[s[1]]
    align_candi.append(cands)

  #Score the align candidates and get the best one.

  if len(align_candi)> 5:
    best_options=semantic_search(ne, align_candi)
    return list(set(best_options))
  else:
    return list(set(align_candi))


'''
Candidate number 1. 
Strict string matching
Extact query should match the original document. Ask for best docs without tokenization and the query from the query list.
If an extact match is made this becomes a candidate.

'''
def strict_match(clean_docs, nmt):

  final_candidate=[]
  count=0
  for b in clean_docs:
    if nmt.lower() in b.lower():
      count+=1
  if count >= 1:
    final_candidate.append(nmt)
  return final_candidate

'''
Candidate number 2.
This function checks if each found NE in spanish equals the query. 
If it does it seaches the original NE in english and check if they have the same entity group. If 
Both are correct it becomes a candidate.
'''

def nes_x_queries(nes_es, nmtq, triplets, left_nes):
  final_translation=[]
  indx= 0
  for i in range(len(nes_es)):
  #for ne in nes_es:
    for m in left_nes:
      if nes_es[i]["word"]== nmtq:
        indx= nmt.index(nmtq)
        if nes_es[i]["entity_group"] == left_nes[indx][3]:
          if nes_es[i]["word"] not in final_translation:
            final_translation.append(nes_es[i]["word"])
          break

      elif nes_es[i]["word"] != nmtq:
        for t in triplets:
          if nes_es[i]["word"] == t:
            if t not in final_translation:
              final_translation.append(t)
          elif nes_es[i]["word"]!=  t:
            final_translation.append(nmtq)
  return final_translation

'''
Candidate number 3.
Check similarity between query and nes in Spanish.
it should also add the candidate to the list.
'''
def simil_query_test(query, list_es):
  list_scores=[]
  if len(list_es)>0:
    doc_score_pairs = semantic_score(query, list_es)
    for score, doc in doc_score_pairs:
      list_scores.append([score, doc])
    list_sorted= sorted(list_scores)
    if len(list_sorted)>0:
      return list_sorted[-1][1]
    else:
      return []
  else:
    return []

'''
Candidate number 4.
Similarity score based on all the nes found on the same tag for the query (bilingual mode)

'''
def tags_vs_eng_word_test(nes_es, left_nes, ne):

  candidate= []
  lista= list(set([word["word"] for word in nes_es if word["entity_group"]== left_nes[3]]))
  if len(lista)>0:
    candidate.append(semantic_score(ne, lista))
  
  if len(candidate) >0: 

    candidate= sorted(candidate)
    return candidate[-1][0][1]
  else:
    return []

'''
Using a trained Desicion Tree model to identify if a word is the translation of the other.

'''
filename ='RF_model/DesicionTree_new.sav' 
vocab_en= "RF_model/vocab_en.pkl"
vocab_es= "RF_model/vocab_es.pkl" 

loaded_model = pickle.load(open(filename, 'rb'))
tf_en_vectorizer= TfidfVectorizer(analyzer="char_wb",ngram_range=(2,5), vocabulary=pickle.load(open(vocab_en, "rb")))
tf_es_vectorizer= TfidfVectorizer(analyzer="char_wb",ngram_range=(2,5), vocabulary=pickle.load(open(vocab_es, "rb")))

'''
Candidate number 5.
RandomForest using the NES
Matches all the nes and provides 1 if the word is a translation or -1 if it isnt.
Trained using Character n grams(2,3,4,5)
'''
def randomf_nes_test(lista_nes, ne):
  cands=[]
  if len(lista_nes)>0:

    ne_data= [ne]*len(lista_nes)
    test_en= tf_en_vectorizer.fit_transform(ne_data)
    test_es= tf_es_vectorizer.fit_transform(lista_nes)
    test_enes = hstack([test_en,test_es])
    prediction= loaded_model.predict(test_enes)

    #prediction
    for i in range(len(prediction)):
      if prediction[i] != -1:
        if lista_nes[i].lower() not in cands:
          cands.append(lista_nes[i])
    if len(cands)>0:
      score= semantic_score(ne, cands)
      score=sorted(score, reverse=True)
      return score[0][1]
  else:
    return []

'''
Thread to get the six candidates faster.
It also returns a list with the number of candidate and the candidate each one has returned.
'''

def trans_candidates_thread(clean_docs, nes_es, query, triplets, queries_cosine, retokenized_article, left_nes, nmt, ne, list_es):
  final_canc=[]

  if len(ne[0].split(" "))==1:   
    
    thread1 = ThreadWithResult(target=align_cand, args=(ne, retokenized_article))
    thread2 = ThreadWithResult(target=strict_match, args=(clean_docs, nmt))
    thread3 = ThreadWithResult(target=nes_x_queries, args=(nes_es, nmt, triplets, left_nes))
    thread4 = ThreadWithResult(target=simil_query_test, args=(query, list_es))
    thread5 = ThreadWithResult(target=tags_vs_eng_word_test, args=(nes_es, left_nes, ne))
    thread6= ThreadWithResult(target= randomf_nes_test, args= (list_es, ne))

    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    thread5.start()
    thread6.start()
    thread1.join()
    thread2.join()
    thread3.join()
    thread4.join()
    thread5.join()
    thread6.join()

    #aligned = thread1.result
    #strict = thread2.result
    #strict_tag= thread3.result
    #query_ne= thread4.result
    #tagged= thread5.result
    #rf_ne= thread6.result

    try:
      thread1.result
      if len(thread1.result)>0:
        final_canc.append([thread1.result[0], "0"])
    except:
      pass
    try:  
      thread2.result
      if len(thread2.result)> 0:
        final_canc.append([thread2.result[0], "1"])
    except:
      pass
    try:
      thread3.result
      if len(thread3.result)> 0:
        final_canc.append([thread3.result[0], "2"])
    except:
      pass 
    try:  
      thread4.result
      if len(thread4.result)> 0:
        final_canc.append([thread4.result, "3"])
    except:
      pass 

    try:
      thread5.result
      if len(thread5.result)> 0:
        final_canc.append([thread5.result, "4"])
    except:
      pass 
    try:
      thread6.result
      if thread6.result != None:
        if len(thread6.result)>0:
          final_canc.append([thread6.result, "5"])
    except:
      pass 

  else:

    thread1 = ThreadWithResult(target=strict_match, args=(clean_docs, nmt))
    thread2 = ThreadWithResult(target=nes_x_queries, args=(nes_es, nmt, triplets, left_nes))
    thread3 = ThreadWithResult(target=simil_query_test, args=(query, list_es))
    thread4 = ThreadWithResult(target=tags_vs_eng_word_test, args=(nes_es, left_nes, ne))
    thread5= ThreadWithResult(target= randomf_nes_test, args= (list_es, ne))

    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    thread5.start()
    thread1.join()
    thread2.join()
    thread3.join()
    thread4.join()
    thread5.join()

    #strict = thread1.result
    #strict_tag= thread2.result
    #query_ne= thread3.result
    #tagged= thread4.result
    #rf_ne= thread5.result

    try:
      thread1.result  
      if len(thread1.result)> 0:
        final_canc.append([thread1.result[0], "1"])
    except:
      pass 
    try:
      thread2.result  
      if len(thread2.result)> 0:
        final_canc.append([thread2.result[0], "2"])
    except:
      pass 
    try:
      thread3.result  
      if len(thread3.result)> 0:
        final_canc.append([thread3.result, "3"])
    except:
      pass 
    try:
      thread4.result  
      if len(thread4.result)> 0:
        final_canc.append([thread4.result, "4"])
    except:
      pass 
    try:
      thread5.result  
      if thread5.result != None:
        if len(thread5.result)>0:
          final_canc.append([thread5.result, "5"])
    except:
      pass 
  return final_canc

'''
Measuring candites using semantic similarity and sentence transformers.
This outputs a list with the "Best translation candidates given the query"

'''

def last_simil_test(final_cands, query):
  list_temp=[]
  if len(final_cands)>0:
    lista=[word[0].lower() for word in final_cands]
    word2num= {word[0].lower():word[1] for word in final_cands}  
    score= semantic_score(query.lower(), lista)
    for simil in score:
      list_temp.append([[simil], word2num[simil[1].lower()]])
    final_result= sorted(list_temp)
    if len(final_result) !=0:
      return final_result
    else:
      return []
  else:
    return []

'''
Initial test provided an insight of how the system performed.
The last step was not always correct so I added a little more weight to the scores obtained before to help the function that were showing 
that they obtained almost alawys the best candidate.
If the scores are below 70% then none of the candidates are selected and I used the initial NMT output
'''

def weight(final_result, nmt):
  if len(final_result) != 0:
    for f in final_result:
      if f[1] == "0":
        f[0][0][0]+=0.3
      if f[1] == "1":
        f[0][0][0]+=0.8
      elif f[1] == "2":
        f[0][0][0]+= 0.2
      elif f[1]== "3":
        f[0][0][0]+= 0.2
      elif f[1]=="4":
        f[0][0][0]+= 0.4
      elif f[1] == "5":
        f[0][0][0]+= 0.5


    new_list= sorted(final_result)
    if new_list[-1][0][0][0]< 0.90:
      return nmt
    else:
      return new_list[-1][0][0][1]
  else:
    return nmt